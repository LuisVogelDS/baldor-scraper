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