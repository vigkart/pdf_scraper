# pdf_scraper

## Overview
The PDF Scraper is a tool designed for extracting and processing tables from PDF files in the 'MSCI' and 'FTSE' formats using Camelot and Pandas.
## Process
1. **scraper.py:** This script drives the extraction process. It loops over all the provided PDF files and invokes the `scrape()` function for each.

2. **scrape():** This function takes user input for pages to be scraped in each PDF file. It then calls the `scrape_page()` function for every selected page.

3. **scrape_page():** This function processes each individual page with the help of the following sub-functions:
   Custom functions to handle general format errors:
   - **header():** Processes and separates each header into its own column.
   - **footer():** Removes end rows that are not part of the table.
   - **drop_empty_rows():** Drops rows that were included in the pdf for visual indication of a new category but is otherwise empty
   - **merge_columns_with_blank_headers():** Ensures no empty columns are left in the dataframe and merges the columns appropriately.
   - **handle_overflow():** Manages situations where a table only contains a few lines, which can be misread by Camelot.

   Other custom functions called to handle specific format errors:
   - **get_name():** Gets the name of the table from the pdf's initially parsed page
   - **split_headers():** This function is called in **header()** in order to ensure headers are properly separated by checking for '\n' characters
   - **fix_country():** Adjusts the 'country' column to correct any formatting issues.
   - **fix_region():** Adjusts the 'region' column to correct any formatting issues.
   - **china_ticker_fix():** Handles specific formatting issues related to Chinese securities' tickers.

   NOTES:
   - The `type` parameter in many functions helps identify whether the PDF is an 'MSCI' or 'FTSE' formatted document.
   - **scrape_page()** checks if a table is an extension of another previously parsed tables, then it merges them

## Known Issues and Potential Resolutions

**Tickers:** Certain tickers, particularly in MSCI previews (page 4 tables), may contain duplicate or random strings. Potential resolutions include:
- Using a database of tickers to match names.
- Web scraping with Selenium WebDriver to find and match tickers.
- May have to use AI to match company names in database to company names in tables

**Functionality Limitation:** The script only works with security level flow tables. For diagrams and charts, a different approach will be required.

## Usage
- I recommend running this in a Conda environment as that is where Camelot works best
- Must have required dependencies installed
- Must have a **pdfs** folder with the pdfs you would like to scrape
- The pdfs in **pdfs** must have 'ftse' or 'msci' somewhere in the name for the scraper.py to identify its **type**
- Must have a empty **proc_tables** folder as a destination to store the outputted csvs
- then run **scraper.py**

## Dependencies:
This scraper uses the following dependencies:
- Camelot
- Pandas
- Numpy

For [camelot](https://pypi.org/project/camelot-py/) you must have ghostscript and Tkinter installed.
- On windows, you must install [ghostscript](https://www.ghostscript.com/releases/index.html) manually
- On windows, Tkinter is already installed with the python distribution


After you have ghostscript installed, to install camelot run:
```Bash
conda install -c conda-forge camelot-py
```

To install pandas and numpy use pip or conda:
```Bash
pip install pandas
pip install numpy
```
