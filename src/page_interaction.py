import time
import os
import logging
import undetected_chromedriver as uc
import re 
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException
from typing import Dict, List, Any, Tuple
from urllib.parse import urljoin

# local imports
from selenium_utils import handle_cookie_overlay
from data_extraction import extract_specs, extract_bom, extract_static_asset_urls
from asset_downloader import download_asset_with_requests, download_cad_interactively
from utils import BASE_URL, DATA_OUTPUT_DIR, ASSETS_BASE_DIR, clean_filename

logger = logging.getLogger(__name__)

def scrape_product_page(product_id: str):
    full_url = urljoin(BASE_URL, product_id) 

    # inicialize an expected structure
    product_data: Dict[str, Any] = {
        "product_id": product_id,
        "name": product_id,
        "description": None,
        "specs": {},
        "hp": None,
        "voltage": None,
        "rpm": None,
        "frame": None,
        "bom": [],
        "assets": {
            "manual": None,
            "cad": None,
            "image": None,
        }
    }
    driver = None

    logger.info(f"Scraping {product_id} from {full_url}")

    selenium_download_dir_for_this_product = os.path.join(ASSETS_BASE_DIR, product_id)
    os.makedirs(selenium_download_dir_for_this_product, exist_ok=True)

    try:
        options = uc.ChromeOptions()
        options.headless = False
        options.add_argument("--start-maximized")

        options.add_experimental_option(
            "prefs", {
                "download.default_directory": selenium_download_dir_for_this_product,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True
            }
        )

        logger.debug("booting undetected_chromedriver")
        driver = uc.Chrome(options=options)
        logger.info("webdriver booted")

        logger.debug(f"loading {full_url}")
        driver.get(full_url)
        logger.info("Page loaded")

        handle_cookie_overlay(driver)

        all_specs = extract_specs(driver)
        product_data['specs'] = all_specs

        spec_key_mapping_for_toplevel = {
            "Output @ Frequency": "hp",
            "Voltage @ Frequency": "voltage",
            "Speed": "rpm",
            "Frame": "frame"
        }
        for html_key, json_key in spec_key_mapping_for_toplevel.items():
            if html_key in product_data['specs']:
                value = product_data['specs'][html_key]

                if json_key == 'hp':
                     match = re.search(r'^\s*(\d*\.?\d+)', value)
                     if match:
                          try:
                              hp_float = float(match.group(1))
                              product_data['hp'] = str(hp_float)
                          except ValueError:
                              logger.warning(f"Error converting HP '{match.group(1)}' from '{value}' to float")
                              product_data['hp'] = value
                     else:
                          logger.warning(f"Error extracting int HP from '{value}'.")
                          product_data['hp'] = value

                elif json_key == 'rpm':
                     match = re.search(r'^\s*(\d+)', value)
                     if match:
                          product_data['rpm'] = match.group(1)
                     else:
                          logger.warning(f"Error extracting int RPM from '{value}'.")
                          product_data['rpm'] = value
                else:
                    product_data[json_key] = value

        description_parts = []
        if 'Enclosure' in all_specs: description_parts.append(all_specs['Enclosure'])
        if product_data.get('hp') is not None and product_data['hp'] != '':
             description_parts.append(f"{product_data['hp']} HP")
        if product_data.get('rpm') is not None and product_data['rpm'] != '':
             description_parts.append(f"{product_data['rpm']} RPM")
        if 'Frame' in all_specs: description_parts.append(all_specs['Frame'])

        product_data['description'] = ", ".join(description_parts) if description_parts else None
        if product_data['description']:
             logger.info(f"Description: {product_data['description']}")
        else:
             logger.warning("Error building description from specs")

        product_data['bom'] = extract_bom(driver)

        static_asset_urls = extract_static_asset_urls(driver)

        logger.info("Downloading static assets via requests")
        downloaded_asset_paths = {}

        downloaded_asset_paths['image'] = download_asset_with_requests(static_asset_urls.get('image'), product_id, 'image')
        downloaded_asset_paths['manual'] = download_asset_with_requests(static_asset_urls.get('manual'), product_id, 'manual')

        downloaded_asset_paths['cad'] = download_cad_interactively(driver, product_id, selenium_download_dir_for_this_product)

        product_data['assets'] = {
            "manual": downloaded_asset_paths.get('manual'),
            "cad": downloaded_asset_paths.get('cad'),
            "image": downloaded_asset_paths.get('image'),
        }

        return product_data

    except WebDriverException as e:
        logger.error(f"WebDriver error during scraping {product_id}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Error during scraping {product_id}: {e}", exc_info=True)
        return None

    finally:
        if driver:
            logger.debug("Closing browser")
            try:
                driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                 logger.warning(f"Error closing browser: {e}", exc_info=True)