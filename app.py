import streamlit as st
import os
import time
import pandas as pd
import plotly.express as px
import shutil
import logging
import json
import zipfile
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# --- Web Scraping & Automation ---
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tenacity import retry, stop_after_attempt, wait_fixed
import pdfkit

# --- Google Drive API ---
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- Application Setup ---
st.set_page_config(
    page_title="SBTET Results Downloader",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants & Configuration ---
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "url": "https://sbtet.ap.gov.in/APSBTET/gradeWiseResults.do",
    "input_id": "hno",
    "dropdown_id": "grade1",
    "submit_xpath": "//input[@value='Get Result']",
    "result_div_id": "printDiv"
}
DOWNLOADS_DIR = os.path.join(os.getcwd(), "downloads")

# --- Classes for Core Logic ---

class SBTETScraper:
    """Handles all web scraping operations using Selenium."""
    def __init__(self, selectors, save_path):
        """
        Initializes the scraper with target selectors.
        Args:
            selectors (dict): A dictionary containing URL, input_id, dropdown_id, etc.
            save_path (str): The local directory to save files.
        """
        self.selectors = selectors
        self.save_path = save_path

    def _setup_driver(self):
        """Initializes and returns a headless Chrome WebDriver."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        try:
            return webdriver.Chrome(options=chrome_options)
        except Exception as e:
            logger.critical(f"Failed to initialize WebDriver: {e}")
            st.error(f"WebDriver Error: {e}. Please ensure Chrome/ChromeDriver is installed and in your PATH.")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def fetch_single_result(self, pin, year, generate_pdf):
        """Fetches, parses, and saves the result for a single PIN."""
        driver = self._setup_driver()
        if not driver:
            return {"PIN NUMBER": pin, "RESULT": "Driver Error", "Subject Results": []}

        try:
            driver.get(self.selectors['url'])
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, self.selectors['input_id']))).send_keys(pin)
            Select(WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, self.selectors['dropdown_id'])) )).select_by_visible_text(year)
            driver.find_element(By.XPATH, self.selectors['submit_xpath']).click()

            result_div = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, self.selectors['result_div_id'])))
            result_data = self._extract_data(driver, pin)

            if generate_pdf and check_wkhtmltopdf():
                html_inner = result_div.get_attribute("innerHTML")
                self._save_as_pdf(html_inner, pin)

            logger.info(f"Successfully scraped data for PIN: {pin}")
            return result_data
        except Exception:
            logger.warning(f"Result not found or timed out for PIN: {pin}")
            return {"PIN NUMBER": pin, "RESULT": "Not Found", "Subject Results": []}
        finally:
            if driver:
                driver.quit()

    def _extract_data(self, driver, pin):
        """Extracts structured data from the result page."""
        def get_text(xpath):
            try: return driver.find_element(By.XPATH, xpath).text.strip()
            except: return ""

        data = {
            "PIN NUMBER": pin,
            "STUDENT NAME": get_text("//th[contains(text(),'Name')]/following-sibling::td"),
            "BRANCH": get_text("//th[contains(text(),'Branch')]/following-sibling::td"),
            "GPA": pd.to_numeric(get_text("//th[contains(text(),'GPA')]/following-sibling::td"), errors='coerce'),
            "RESULT": get_text("//th[contains(text(),'Result')]/following-sibling::td"),
            "Subject Results": []
        }

        try:
            rows = driver.find_elements(By.XPATH, f"//div[@id='{self.selectors['result_div_id']}']//table[2]//tr[position()>1]")
            for row in rows:
                cols = [c.text.strip() for c in row.find_elements(By.TAG_NAME, 'td')]
                if len(cols) >= 8:
                    data["Subject Results"].append({
                        "Subject Name": cols[0], "External": cols[1], "Internal": cols[2],
                        "Total": cols[3], "Grade Points": cols[4], "Credits Earned": cols[5],
                        "Grade": cols[6], "SUB.Result": cols[7]
                    })
        except Exception as e:
            logger.warning(f"Could not parse subject details for {pin}: {e}")
        return data

    def _save_as_pdf(self, html_content, pin):
        """Saves the provided HTML content as a styled PDF."""
        styled_html = f"""<html><head><meta charset="UTF-8"><style>body {{ font-family: 'Helvetica', 'Arial', sans-serif; }} table, th, td {{ border: 1px solid #ddd; border-collapse: collapse; padding: 8px; text-align: left; }} th {{ background-color: #f2f2f2; }}</style></head><body>{html_content}</body></html>"""
        pdf_path = os.path.join(self.save_path, f"{pin}_result.pdf")
        try:
            pdfkit.from_string(styled_html, pdf_path)
            logger.info(f"Saved PDF for {pin} at {pdf_path}")
        except Exception as e:
            logger.error(f"Failed to generate PDF for {pin}: {e}")

class ResultProcessor:
    """Handles processing and analysis of scraped results."""
    def __init__(self, all_results_data):
        self.raw_data = all_results_data
        self.df = self._create_dataframe()

    def _create_dataframe(self):
        """Creates a flattened DataFrame from the raw results data."""
        flat_results = []
        valid_results = [r for r in self.raw_data if r is not None]
        for r in valid_results:
            base = {k: v for k, v in r.items() if k != "Subject Results"}
            if r.get("Subject Results"):
                for sub in r["Subject Results"]:
                    flat_results.append({**base, **sub})
            elif r:
                flat_results.append(base)
        return pd.DataFrame(flat_results)

    def get_summary_stats(self):
        """Calculates and returns summary statistics."""
        if self.df.empty:
            return {"total": 0, "passed": 0, "failed": 0}

        unique_students = self.df.drop_duplicates(subset=['PIN NUMBER']).copy()
        total = unique_students['PIN NUMBER'].nunique()
        passed = unique_students[unique_students["RESULT"].str.contains("Pass|Distinction|First", case=False, na=False)].shape[0]
        return {"total": total, "passed": passed, "failed": total - passed}

    def get_branch_performance(self):
        """Analyzes and returns performance data grouped by branch."""
        if self.df.empty or 'BRANCH' not in self.df.columns or self.df['BRANCH'].nunique() < 1:
            return None

        unique_students = self.df.drop_duplicates(subset=['PIN NUMBER']).copy()
        unique_students['Status'] = unique_students['RESULT'].apply(lambda x: 'Pass' if isinstance(x, str) and any(p in x for p in ["Pass", "Distinction", "First"]) else 'Fail')
        summary = unique_students.groupby('BRANCH')['Status'].value_counts().unstack(fill_value=0)
        if 'Pass' not in summary: summary['Pass'] = 0
        if 'Fail' not in summary: summary['Fail'] = 0
        summary['Total'] = summary['Pass'] + summary['Fail']
        summary['Pass Rate (%)'] = (summary['Pass'] / summary['Total'] * 100).round(2)
        return summary.sort_values(by='Pass Rate (%)', ascending=False)

    def get_top_performers(self, n=10):
        """Returns the top N students by GPA."""
        if self.df.empty or 'GPA' not in self.df.columns:
            return pd.DataFrame()

        return self.df[['PIN NUMBER', 'STUDENT NAME', 'BRANCH', 'GPA']].dropna(subset=['GPA']).drop_duplicates(subset=['PIN NUMBER']).nlargest(n, 'GPA')

    def get_subject_analysis(self):
        """Analyzes pass/fail rates for each subject."""
        if self.df.empty or 'Subject Name' not in self.df.columns:
            return None

        subjects = self.df.dropna(subset=['Subject Name', 'SUB.Result']).copy()
        subjects['Status'] = subjects['SUB.Result'].apply(lambda x: 'Pass' if x == 'P' else 'Fail')
        analysis = subjects.groupby('Subject Name')['Status'].value_counts().unstack(fill_value=0)
        if 'Pass' not in analysis: analysis['Pass'] = 0
        if 'Fail' not in analysis: analysis['Fail'] = 0
        analysis['Total'] = analysis['Pass'] + analysis['Fail']
        analysis['Pass Rate (%)'] = (analysis['Pass'] / analysis['Total'] * 100).round(2)
        return analysis.sort_values(by='Pass Rate (%)', ascending=True)

class DriveUploader:
    """Handles authentication and file uploads to Google Drive."""
    def __init__(self):
        self.service = self._get_service()

    def _get_service(self):
        """Authenticates using st.secrets and returns the Drive service."""
        try:
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/drive.file"])
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            st.error(f"Google Drive auth failed: {e}")
            st.info("Ensure `gcp_service_account` is correctly configured in `secrets.toml`.")
            return None

    def upload_file(self, file_path, folder_id):
        """Uploads a single file to the specified Drive folder."""
        if not self.service or not os.path.exists(file_path):
            return False

        file_name = os.path.basename(file_path)
        metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaFileUpload(file_path)
        try:
            self.service.files().create(body=metadata, media_body=media, fields='id').execute()
            logger.info(f"Successfully uploaded {file_name} to Drive.")
            return True
        except Exception as e:
            logger.error(f"Drive upload failed for {file_name}: {e}")
            return False

# --- Helper & Utility Functions ---
@st.cache_data
def load_uploaded_file(uploaded_file):
    """Caches the reading of an uploaded file."""
    if uploaded_file.name.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    else:
        return pd.read_excel(uploaded_file)

def check_wkhtmltopdf():
    """Checks if wkhtmltopdf dependency is met."""
    return shutil.which("wkhtmltopdf") is not None

def load_config():
    """Loads configuration from JSON file or returns defaults."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return DEFAULT_CONFIG
    return DEFAULT_CONFIG

# --- Main Application UI & Logic ---
def main():
    """Renders the Streamlit UI and orchestrates the application flow."""
    if 'config' not in st.session_state:
        st.session_state.config = load_config()

    # --- Sidebar for Inputs ---
    with st.sidebar:
        st.header("Configuration")
        mode = st.selectbox("Select Mode", ["Range", "Single", "CSV"])
        pin_list = []

        if mode == "Range":
            base = st.text_input("Enter Base PIN (e.g., 23315-CM-)", "23315-CM-")
            start = st.number_input("Start Suffix", min_value=1, value=1)
            count = st.number_input("No. of Students", min_value=1, max_value=1000, value=5)
            pin_list = [f"{base}{str(i).zfill(3)}" for i in range(start, start + count)] if base else []
        elif mode == "Single":
            pin = st.text_input("Enter a single PIN:")
            if pin: pin_list.append(pin)
        elif mode == "CSV":
            uploaded_file = st.file_uploader("Upload File", type=["csv", "xlsx"])
            if uploaded_file:
                df_upload = load_uploaded_file(uploaded_file)
                col = st.selectbox("Select PIN column:", options=df_upload.columns)
                pin_list = df_upload[col].dropna().astype(str).tolist()

        year = st.selectbox("Select Year/Semester", ["1YEAR", "2SEM","3SEM","4SEM","5SEM", "6SEM", "7SEM"], index=0)

        # --- MODIFICATION: Removed manual save path input ---

        st.subheader("Download Options")
        generate_excel = st.checkbox("Prepare Excel Report", value=True)
        generate_pdf = st.checkbox("Prepare Individual PDFs", value=True, disabled=not check_wkhtmltopdf())

        with st.expander("Advanced Settings"):
            st.info("Manually edit the web page element identifiers (for advanced users).", icon="⚙️")

            url = st.text_input("Target URL", value=st.session_state.config.get('url', DEFAULT_CONFIG['url']))
            input_id = st.text_input("PIN/Hall Ticket Input ID", value=st.session_state.config.get('input_id', DEFAULT_CONFIG['input_id']))
            dropdown_id = st.text_input("Year/Semester Dropdown ID", value=st.session_state.config.get('dropdown_id', DEFAULT_CONFIG['dropdown_id']))
            submit_xpath = st.text_input("Submit Button XPath", value=st.session_state.config.get('submit_xpath', DEFAULT_CONFIG['submit_xpath']))
            result_div_id = st.text_input("Result Container DIV ID", value=st.session_state.config.get('result_div_id', DEFAULT_CONFIG['result_div_id']))

            st.session_state.config = {
                "url": url, "input_id": input_id, "dropdown_id": dropdown_id,
                "submit_xpath": submit_xpath, "result_div_id": result_div_id
            }
            st.session_state.max_workers = st.slider("Max Parallel Downloads", 1, 10, 5)

            if st.button("Save Config to File"):
                with open(CONFIG_FILE, "w") as f:
                    json.dump(st.session_state.config, f, indent=4)
                st.success("Configuration saved to config.json!")

    # --- Main Page ---
    st.markdown("## SBTET Download Tool")
    st.markdown(f"_v6.1 (Darion Edition) - {datetime.now().strftime('%B %Y')}_")

    if not check_wkhtmltopdf():
        st.warning("**PDF generation disabled:** `wkhtmltopdf` not found. Please install it and ensure it's in your system's PATH.", icon="⚠️")

    col1, col2 = st.columns([1, 6])
    if col1.button("Start Process", type="primary", use_container_width=True):
        if pin_list:
            st.session_state.process_running = True
            st.session_state.process_complete = False

            # --- MODIFICATION: Automatically create a unique directory for this run ---
            run_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            save_path = os.path.join(DOWNLOADS_DIR, f"results_{run_timestamp}")
            os.makedirs(save_path, exist_ok=True)
            logger.info(f"Created save directory: {save_path}")
            # --- End Modification ---

            scraper = SBTETScraper(st.session_state.config, save_path)
            progress_bar = st.progress(0, text="Starting...")
            all_results = []
            total_pins = len(pin_list)

            with ThreadPoolExecutor(max_workers=st.session_state.max_workers) as executor:
                future_to_pin = {executor.submit(scraper.fetch_single_result, pin, year, generate_pdf): pin for pin in pin_list}
                for i, future in enumerate(future_to_pin):
                    pin_val = future_to_pin[future]
                    all_results.append(future.result())
                    progress_bar.progress((i + 1) / total_pins, text=f"Processing PIN: {pin_val} ({i+1}/{total_pins})")

            st.session_state.raw_results = all_results
            processor = ResultProcessor(all_results)
            st.session_state.df_results = processor.df

            excel_path = None
            if generate_excel:
                excel_path = os.path.join(save_path, "sbtet_results.xlsx")
                processor.df.to_excel(excel_path, index=False)

            st.session_state.result_files = {
                "excel": excel_path,
                "pdfs": [os.path.join(save_path, f"{r['PIN NUMBER']}_result.pdf") for r in all_results if os.path.exists(os.path.join(save_path, f"{r['PIN NUMBER']}_result.pdf"))]
            }
            st.session_state.process_complete = True
            st.session_state.process_running = False
            st.rerun()
        else:
            st.warning("No PINs provided to process.")

    if col2.button("↷ Reset", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    # --- Results Display ---
    if st.session_state.get('process_complete'):
        st.success("Processing Complete!")
        processor = ResultProcessor(st.session_state.get('raw_results', []))

        with st.expander("↓ Download & Upload Options", expanded=True):
            files_generated = st.session_state.get('result_files', {})
            excel_file = files_generated.get('excel')
            pdf_files = files_generated.get('pdfs', [])

            if not excel_file and not pdf_files:
                st.info("No files were generated based on your sidebar selections.")
            else:
                # --- MODIFICATION: Always offer a ZIP of all generated files ---
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                    if excel_file and os.path.exists(excel_file):
                        zf.write(excel_file, os.path.basename(excel_file))
                    for pdf in pdf_files:
                        if os.path.exists(pdf): zf.write(pdf, os.path.basename(pdf))

                if zip_buffer.getbuffer().nbytes > 0:
                     st.download_button(
                        "📦 Download All as ZIP",
                        zip_buffer.getvalue(),
                        f"sbtet_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                # --- End Modification ---

            with st.form("drive_upload_form"):
                folder_id = st.text_input("Google Drive Folder ID")
                if st.form_submit_button("Upload to Google Drive"):
                    if not folder_id:
                        st.error("A Google Drive Folder ID is required.")
                    else:
                        files_to_upload = []
                        if excel_file and os.path.exists(excel_file): files_to_upload.append(excel_file)
                        if pdf_files: files_to_upload.extend([f for f in pdf_files if os.path.exists(f)])

                        if not files_to_upload:
                            st.warning("No files were generated to upload.")
                        else:
                            uploader = DriveUploader()
                            if uploader.service:
                                upload_progress = st.progress(0, text="Starting upload...")
                                for i, f_path in enumerate(files_to_upload):
                                    uploader.upload_file(f_path, folder_id)
                                    upload_progress.progress((i+1)/len(files_to_upload), text=f"Uploading {os.path.basename(f_path)}...")
                                st.success("Upload to Google Drive complete.")

        tab_summary, tab_analytics, tab_data = st.tabs(["Summary", "Analytics", "Raw Data"])

        with tab_summary:
            stats = processor.get_summary_stats()
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Processed", stats['total'])
            c2.metric("Passed", stats['passed'])
            c3.metric("Failed", stats['failed'])
            if stats['total'] > 0:
                fig = px.pie(names=["Passed", "Failed"], values=[stats['passed'], stats['failed']], title="Overall Pass/Fail Distribution", color_discrete_sequence=["#00C853", "#D32F2F"])
                st.plotly_chart(fig, use_container_width=True)

            st.subheader("Performance by Branch")
            branch_perf = processor.get_branch_performance()
            if branch_perf is not None:
                st.dataframe(branch_perf, use_container_width=True)
            else:
                st.info("No branch data available to display.")


        with tab_analytics:
            st.subheader("GPA Distribution")
            gpa_data = processor.df['GPA'].dropna()
            if not gpa_data.empty:
                fig_gpa = px.histogram(gpa_data, nbins=20, title="Distribution of Grade Point Average (GPA)")
                st.plotly_chart(fig_gpa, use_container_width=True)
            else:
                st.info("No GPA data available for analysis.")

            st.subheader("Top 10 Performers")
            top_10 = processor.get_top_performers(10)
            st.dataframe(top_10, use_container_width=True)

            st.subheader("Subject Performance Analysis")
            subject_analysis = processor.get_subject_analysis()
            if subject_analysis is not None:
                st.dataframe(subject_analysis, use_container_width=True)
            else:
                st.info("No subject data available for analysis.")


        with tab_data:
            st.dataframe(processor.df, use_container_width=True)

if __name__ == "__main__":
    main()