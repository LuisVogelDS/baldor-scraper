# Baldor Product Data Scraper - Luis Vogel

## Project Description

This project implements a solution for a machine learning engineering challenge on web scraping. The goal is to build a python pipeline to extract structured data and assets, like images, PDFs and CAD files, from product pages on the Baldor website (https://www.baldor.com/).

The scraper uses `selenium` with `undetected-chromedriver` to navigate and interact with the website (including dynamic elements like tabs and dropdowns), and the `requests` library for downloading assets with direct URLs.

## Pipeline

1.  Navigate to the specified product pages;
2.  Extract structured data from different tabs of the page;
3.  Extarct specific fields (HP, Voltage, RPM, Frame) from the specifications and include them at the top level of the JSON object;
4.  Construct a description field summarizing key data points;
5.  Locate URLs for assets (Product Image, PDF Manual, CAD DWG file);
6.  Download the assets into a directory structure organized by product ID;
7.  Generate a JSON file for each product containing the structured data and the relative paths to the downloaded assets.

## Output Structure

Executing the scraper will create an `output/` directory at the project root, with the following structure:

baldor_scraper/
└── output/
├── product_1.json
├── product_2.json
└── assets/
├── product_1/
│ ├── image.jpg (or .png, etc.)
│ ├── manual.pdf
│ └── cad_file_name.dwg
└── product_2/
│ ├── image.jpg
│ ├── manual.pdf
│ └── cad_file_name.dwg


## Prerequisites
- Python version: It is recommended to use Python 3.13.3 to replicate the development environment. Please, ensure setuptools is installed for compatibility with libraries that still rely on distutils;

- uv: The specified dependency management tool;

## Setup

Follow these steps to set up the development environment using uv:

1.  Clone the repository (or organize your files into the described structure if starting locally):
    git clone https://github.com/LuisVogelDS/baldor-scraper
    cd baldor-scraper

2.  Create a venv in the project root using uv and Python 3.13.3 and activate it:
    uv venv --python python3.13.3.exe
    .venv\Scripts\activate

3.  Install the dependencies listed in requirements.txt using uv inside the project root
    uv pip install -r requirements.txt

4.  Verify the Python version within the activated environment:
    python --version

## How to Run

1.  Ensure your virtual environment is activated

2.  Execute the main script from the project root directory:
    python src/main.py

3.  The script will process the list of `PRODUCT_IDS` defined in `src/main.py`. For each product, it will:
    *   Open a Chrome browser instance
    *   Navigate to the product page
    *   Extract data and asset URLs
    *   Dynamically click through menus to get the CAD download
    *   Download assets using requests or wait for Selenium's download
    *   Close the browser
    *   Save the data and asset paths into a JSON file in the output/ folder.

4.  The scraping process is logged to the console, providing feedback on each step.

## Logging

The script uses Python's standard `logging` library to provide detailed output during execution. Log messages are displayed in the console (`sys.stdout`) and include timestamps and severity levels (`INFO`, `WARNING`, `ERROR`, `DEBUG` if enabled).

## Author

Luis Vogel