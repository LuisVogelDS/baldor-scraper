import os
import time
import logging
import requests
import re
from urllib.parse import urlparse, urljoin
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from typing import Dict, List, Any, Tuple, Optional

# Importa funções utilitárias dos módulos locais
from selenium_utils import click_tab, safe_find_element
from utils import ASSETS_BASE_DIR, clean_filename, get_file_extension_from_url

logger = logging.getLogger(__name__)


def download_asset_with_requests(asset_url: str | None, product_id: str, asset_type: str) -> str | None:
    # downloads assets using requests and saves them in the product's assets directory. Used for manuals and images
    
    if not asset_url:
        logger.debug(f"  empty download URL for '{asset_type}' skiping download.")
        return None

    cleaned_product_id = clean_filename(product_id)
    product_asset_subdir = os.path.join(ASSETS_BASE_DIR, cleaned_product_id)
    os.makedirs(product_asset_subdir, exist_ok=True)

    ext_map = {"manual": ".pdf", "image": ".jpg"}
    ext = ext_map.get(asset_type)

    # Usa o asset_type como nome do arquivo (manual.pdf, image.jpg)
    local_filename = f"{clean_filename(asset_type)}{ext}"
    local_filepath_absolute = os.path.join(product_asset_subdir, local_filename)
    local_path_relative = os.path.join(os.path.basename(ASSETS_BASE_DIR), cleaned_product_id, local_filename).replace('\\', '/')

    if os.path.exists(local_filepath_absolute):
         logger.debug(f"  file already exists {local_filepath_absolute}, removing it")
         try: os.remove(local_filepath_absolute)
         except OSError as e: logger.warning(f"   error remobing existing file {local_filepath_absolute}: {e}")

    logger.info(f"  Downloading asset '{asset_type}' de {asset_url} para {local_filepath_absolute} usando requests...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        with requests.get(asset_url, stream=True, headers=headers, timeout=30) as r:
            r.raise_for_status()

            with open(local_filepath_absolute, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        logger.info(f"  Asset downloaded '{asset_type}' ")
        return local_path_relative

    except requests.exceptions.RequestException as e:
        logger.warning(f"  Error downloading '{asset_type}' from {asset_url} using requests: {e}")
        if os.path.exists(local_filepath_absolute):
             try: os.remove(local_filepath_absolute)
             except OSError as rm_err: logger.warning(f"  Error removing file {local_filepath_absolute}: {rm_err}")
        return None
    except IOError as e:
        logger.warning(f"  Error saving file {local_filepath_absolute}: {e}")
        return None
    except Exception as e:
        logger.error(f"  Error downloading '{asset_type}' from {asset_url} using requests: {e}")
        if os.path.exists(local_filepath_absolute):
             try: os.remove(local_filepath_absolute)
             except OSError as rm_err: logger.warning(f"  Error removing file {local_filepath_absolute}: {rm_err}")
        return None


def download_cad_interactively(driver: WebDriver, product_id: str, selenium_download_dir: str) -> str | None:
    
    # Goes to the Drawings tab, interacts with the dropdown, clicks the download button and returns the downloaded file path
   
    logger.info("Starting CAD download")
    cad_downloaded_path_relative: str | None = None

    cleaned_product_id = clean_filename(product_id)
    logger.debug(f"path set to {selenium_download_dir}")

    if not click_tab(driver, 'drawings'):
        logger.warning("Error accessing drawings tab")
        return None

    logger.debug("Drawings tab accessed")

    cad_section_locator = (By.CSS_SELECTOR, '.pane[data-tab="drawings"] .section.cadfiles')
    if not safe_find_element(driver, *cad_section_locator, wait_time=10):
        logger.warning("CAD files section found")
        return None

    dropdown_input_locator = (By.CSS_SELECTOR, '.pane[data-tab="drawings"] .k-dropdown-wrap .k-input')
    try:
        dropdown_input = WebDriverWait(driver, 15).until(EC.element_to_be_clickable(dropdown_input_locator))
        logger.debug("Dropdown found")
        dropdown_input.click()
        logger.debug("Dropdown clicked")
        time.sleep(1)

    except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
        logger.warning(f"Error clicking dropdown: {e}")
        return None

    dropdown_list_locator = (By.XPATH, "//div[contains(@class, 'k-animation-container') and not(@aria-hidden='true')]//ul[@role='listbox']")
    first_dwg_option = None
    option_text_found = None

    try:
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located(dropdown_list_locator))
        logger.debug("Kendo UI dropdown list visible")

        list_items_locator = (By.XPATH, "//div[contains(@class, 'k-animation-container') and not(@aria-hidden='true')]//li[@role='option']")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located(list_items_locator))

        list_items = driver.find_elements(*list_items_locator)
        logger.debug(f"{len(list_items)} options found in the dropdown list")

        for item in list_items:
            try:
                item_text = item.text
                if "DWG" in item_text.upper():
                    first_dwg_option = item
                    option_text_found = item_text
                    logger.info(f"First option containing DWG: '{option_text_found}'")
                    break
            except StaleElementReferenceException:
                 logger.debug("StaleElementReferenceException while verifying this item. Skipping")
                 continue

        if first_dwg_option:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(first_dwg_option))
            first_dwg_option.click()
            logger.info(f"Option '{option_text_found}' clicked.")
            time.sleep(2)
        else:
            logger.warning("No DWG option in the dropdown. CAD was NOT downloaded")
            return None

    except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
        logger.warning(f"Error finding or clicking DWG. CAD was NOT downloaded : {e}")
        return None

    logger.debug("Waiting for the download button")
    download_button_locator = (By.ID, 'cadDownload')
    download_button = None
    try:
        download_button = WebDriverWait(driver, 15).until(EC.element_to_be_clickable(download_button_locator))
        WebDriverWait(driver, 5).until(lambda driver: driver.find_element(*download_button_locator).get_attribute("aria-disabled") == "false")
        logger.info("Button found and clickable")

    except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
        logger.warning(f"Button not found or cliclable: {e}")
        return None

    files_before = os.listdir(selenium_download_dir)
    logger.debug(f"Files in directory before the click {files_before}")

    try:
        download_button.click()
        logger.info("Button clicked")
        time.sleep(2)

    except (ElementClickInterceptedException, Exception) as e:
        logger.warning(f"Error clicking: {e}")
        return None

    logger.info(f"Waiting for the file at '{selenium_download_dir}'...")
    timeout_seconds = 30
    check_interval_seconds = 1
    end_time = time.time() + timeout_seconds
    downloaded_file_name = None

    while time.time() < end_time:
        files_after = os.listdir(selenium_download_dir)
        new_files = [f for f in files_after if f not in files_before and not f.endswith('.crdownload')]

        if new_files:
            downloaded_file_name = new_files[0]
            full_downloaded_path = os.path.join(selenium_download_dir, downloaded_file_name)

            time.sleep(1)
            if os.path.exists(full_downloaded_path) and not full_downloaded_path.endswith('.crdownload'):
                logger.info(f"CAD detected: {downloaded_file_name}")
                time.sleep(1)

                logger.info(f"CAD downloaded: {downloaded_file_name}")
                relative_path = os.path.join(os.path.basename(ASSETS_BASE_DIR), cleaned_product_id, downloaded_file_name).replace('\\', '/')
                return relative_path


        time.sleep(check_interval_seconds)

    logger.warning(f"Timeout {timeout_seconds}s ")
    return None