# SBTET Results Downloader (Darion Edition)

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Output](#output)
- [Google Drive Integration](#google-drive-integration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Overview
SBTET Results Downloader is a robust and scalable Streamlit application engineered to automate the extraction, processing, and analysis of student results from the State Board of Technical Education and Training (SBTET) portal. Utilizing Selenium for reliable web scraping, the application delivers comprehensive reporting capabilities, including Excel and PDF generation, alongside seamless Google Drive integration for cloud storage.

## Features
- Flexible input modes: Range of PINs, Single PIN, or CSV file upload.
- Detailed extraction of student academic results, including subject-wise marks and GPA.
- Generation of consolidated Excel reports for comprehensive data analysis.
- Creation of individual PDF reports per student (requires `wkhtmltopdf`).
- Interactive analytics with visualizations covering pass/fail rates, branch performance, GPA distribution, and top performers.
- Google Drive API integration for direct upload of generated reports.
- Advanced configuration options for customizing scraping parameters.
- Multi-threaded execution to optimize performance and throughput.

## Prerequisites
- Python 3.8 or later
- Google Chrome browser and corresponding ChromeDriver installed and accessible via system PATH
- `wkhtmltopdf` utility for PDF report generation (optional but highly recommended)

## Installation

### Installing wkhtmltopdf

#### Windows
1. Download the latest stable installer from the official website: [https://wkhtmltopdf.org/downloads.html](https://wkhtmltopdf.org/downloads.html)
2. Execute the installer and follow the installation wizard.
3. Add the installation directory (e.g., `C:\Program Files\wkhtmltopdf\bin`) to your system PATH environment variable.
4. Restart your terminal or IDE to apply the PATH changes.

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install -y wkhtmltopdf
```

#### Other Linux Distributions
Consult your distribution’s package manager or download the appropriate package from the official website.

### Python Dependencies
Install required Python packages using pip:
```bash
pip install -r requirements.txt
```

## Usage

1. Launch the application:
```bash
streamlit run app.py
```

2. Configure the input mode via the sidebar:
   - **Range**: Define a base PIN, starting suffix, and number of students.
   - **Single**: Input a single PIN.
   - **CSV**: Upload a CSV or Excel file containing PINs.

3. Select the academic year or semester.

4. Choose output options:
   - Generate an Excel report.
   - Generate individual PDF reports (requires `wkhtmltopdf`).

5. (Optional) Modify advanced settings such as target URL and HTML element selectors.

6. Click **Start Process** to initiate data scraping and processing.

7. Upon completion, download results as Excel, PDFs, or a consolidated ZIP archive.

8. (Optional) Upload results to a Google Drive folder by specifying the folder ID.

## Configuration

- Scraping parameters are persisted in `config.json`.
- Advanced users may customize URL, input field IDs, dropdown selectors, and other parameters via the sidebar interface.
- Adjust maximum parallel downloads to optimize performance based on system capabilities.

## Output

- Results are saved in a timestamped directory within the `downloads` folder.
- Excel reports provide detailed student data for further analysis.
- PDFs offer professionally formatted individual student result pages.
- Analytics tabs present insightful visualizations and summaries to aid decision-making.

## Google Drive Integration

- Requires a Google Cloud service account configured in Streamlit secrets (`secrets.toml`).
- Enables direct upload of generated reports to a specified Google Drive folder for centralized storage.

## Troubleshooting

- Verify ChromeDriver version compatibility with your installed Chrome browser.
- Ensure `wkhtmltopdf` is installed and included in your system PATH for PDF generation.
- Confirm network connectivity to the SBTET website.
- Review application logs for any scraping or upload errors.

## Contributing

Contributions, issues, and feature requests are welcome. Please fork the repository and submit a pull request or open an issue for discussion.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contact

For support or inquiries, please contact the project maintainer.
