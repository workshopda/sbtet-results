# SBTET Results Downloader (Darion Edition)

## Overview
SBTET Results Downloader is a sophisticated Streamlit-based application designed to automate the retrieval and analysis of student results from the State Board of Technical Education and Training (SBTET) website. Leveraging Selenium for robust web scraping, the application processes data efficiently, generates comprehensive reports in Excel and PDF formats, and supports seamless integration with Google Drive for file uploads.

## Key Features
- Multiple input modes: Range of PINs, Single PIN, or CSV file upload.
- Detailed extraction of student results, including subject-wise marks and GPA.
- Generation of consolidated Excel reports summarizing all results.
- Creation of individual PDF reports per student (requires `wkhtmltopdf`).
- Interactive analytics and visualizations: pass/fail distribution, branch performance, GPA distribution, and top performers.
- Google Drive integration for direct upload of generated files.
- Advanced configuration options for web scraping parameters.
- Multi-threaded processing for enhanced performance and scalability.

## Installation

### Prerequisites
- Python 3.8 or higher
- Google Chrome browser and matching ChromeDriver installed and accessible via system PATH
- `wkhtmltopdf` for PDF generation (optional but strongly recommended)

### Installing wkhtmltopdf

#### Windows
1. Download the installer from the official website: [https://wkhtmltopdf.org/downloads.html](https://wkhtmltopdf.org/downloads.html)
2. Execute the installer and follow the on-screen instructions.
3. Add the installation directory (e.g., `C:\Program Files\wkhtmltopdf\bin`) to your system PATH environment variable.
4. Restart your terminal or development environment to apply the changes.

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install -y wkhtmltopdf
```

#### Other Linux Distributions
Refer to your distribution’s package manager or download the appropriate package from the official website above.

### Dependency Installation
Install the required Python packages using pip:
```bash
pip install -r requirements.txt
```

## Usage

1. Launch the application:
```bash
streamlit run app.py
```

2. Configure input mode via the sidebar:
   - **Range**: Define a base PIN, starting suffix, and number of students.
   - **Single**: Input a single PIN.
   - **CSV**: Upload a CSV or Excel file containing PINs.

3. Select the relevant year or semester.

4. Choose output options:
   - Generate an Excel report.
   - Generate individual PDF reports (requires `wkhtmltopdf`).

5. (Optional) Modify advanced settings such as target URL and HTML element selectors.

6. Click **Start Process** to initiate scraping and data processing.

7. Upon completion, download results as Excel, PDFs, or a consolidated ZIP archive.

8. (Optional) Upload results to a Google Drive folder by specifying the folder ID.

## Configuration

- Scraping parameters are saved in `config.json`.
- Advanced users can customize URL, input field IDs, dropdown selectors, and other parameters via the sidebar.
- Adjust maximum parallel downloads to optimize performance.

## Output

- Results are stored in a timestamped directory within the `downloads` folder.
- Excel reports provide detailed student data.
- PDFs offer formatted individual student result pages.
- Analytics tabs present insightful visualizations and summaries.

## Google Drive Integration

- Requires a Google Cloud service account configured in Streamlit secrets (`secrets.toml`).
- Enables direct upload of generated files to a specified Google Drive folder.

## Troubleshooting

- Verify ChromeDriver version compatibility with your installed Chrome browser.
- Ensure `wkhtmltopdf` is installed and included in your system PATH for PDF generation.
- Confirm network connectivity to the SBTET website.
- Review application logs for any scraping or upload errors.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contact

For support or inquiries, please contact the project maintainer.
