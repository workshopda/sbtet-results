# SBTET Results Downloader

## Overview
SBTET Results Downloader is a Streamlit-based web application designed to automate the process of downloading and analyzing student results from the SBTET (State Board of Technical Education and Training) website. It uses Selenium for web scraping, processes the results, generates reports in Excel and PDF formats, and optionally uploads the results to Google Drive.

## Features
- Supports multiple input modes: Range of PINs, Single PIN, or CSV file upload.
- Scrapes detailed student results including subject-wise marks and GPA.
- Generates Excel reports summarizing all results.
- Generates individual PDF reports for each student (requires `wkhtmltopdf`).
- Provides analytics and visualizations such as pass/fail distribution, branch performance, GPA distribution, and top performers.
- Uploads generated files to a specified Google Drive folder.
- Configurable web scraping parameters for advanced users.
- Multi-threaded scraping for faster processing.

## Installation

### Prerequisites
- Python 3.8 or higher
- Google Chrome and ChromeDriver installed and accessible in your system PATH
- `wkhtmltopdf` installed for PDF generation (optional but recommended)

### Install dependencies
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit app:
```bash
streamlit run app.py
```

2. Use the sidebar to select the input mode:
   - **Range**: Specify a base PIN, start suffix, and number of students.
   - **Single**: Enter a single PIN.
   - **CSV**: Upload a CSV or Excel file containing a column with PINs.

3. Select the year/semester from the dropdown.

4. Choose download options:
   - Generate Excel report
   - Generate individual PDFs (requires `wkhtmltopdf`)

5. (Optional) Adjust advanced settings such as target URL and HTML element identifiers.

6. Click **Start Process** to begin scraping and processing.

7. After completion, download the results as Excel, PDFs, or a ZIP archive.

8. (Optional) Upload the results to a Google Drive folder by providing the folder ID.

## Configuration

- The app saves scraping configuration in `config.json`.
- Advanced users can modify the URL, input field IDs, dropdown IDs, and other selectors via the sidebar.
- Maximum parallel downloads can be adjusted for performance tuning.

## Output

- Results are saved in a timestamped folder inside the `downloads` directory.
- Excel report contains detailed student results.
- PDFs contain formatted individual student result pages.
- Analytics tabs provide visual insights into the data.

## Google Drive Upload

- Requires a Google Cloud service account configured in Streamlit secrets (`secrets.toml`).
- Upload files directly to a specified Google Drive folder by entering the folder ID.

## Troubleshooting

- Ensure ChromeDriver version matches your installed Chrome browser.
- Install `wkhtmltopdf` and ensure it is in your system PATH for PDF generation.
- Check network connectivity to the SBTET website.
- Review logs for errors during scraping or uploading.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contact

For support or inquiries, please contact the maintainer.
