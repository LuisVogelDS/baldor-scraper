import logging
import re
from typing import Dict, List, Any
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from urllib.parse import urljoin 

# local imports
from selenium_utils import safe_find_element, safe_find_elements, click_tab

logger = logging.getLogger(__name__)

def extract_product_description_div(driver: WebDriver) -> str | None:
    # extracts the products description
    description_locator = (By.CSS_SELECTOR, '.product-description')
    description_element = safe_find_element(driver, *description_locator, wait_time=5)
    if description_element:
        return description_element.text.strip()
    return None


def extract_specs(driver: WebDriver) -> Dict[str, str]:
    # extracts the products specs
    specs_data: Dict[str, str] = {}
    if not click_tab(driver, 'specs'):
        logger.warning("Error accessing specs tab")
        return specs_data

    logger.info("Extracting specs")
    specs_section_locator = (By.CSS_SELECTOR, '.pane[data-tab="specs"] .detail-table.product-overview')
    specs_section = safe_find_element(driver, *specs_section_locator, wait_time=10)

    if not specs_section:
        logger.warning("Specs table not found")
        return specs_data

    spec_pairs_locator = (By.CSS_SELECTOR, '.pane[data-tab="specs"] .detail-table.product-overview .col.span_1_of_2 > div')
    spec_elements = safe_find_elements(driver, *spec_pairs_locator, wait_time=10)

    if not spec_elements:
        logger.warning("Specs elements not found")
        return specs_data

    for spec_div in spec_elements:
        try:
            label_span = spec_div.find_element(By.CSS_SELECTOR, 'span.label')
            value_span = spec_div.find_element(By.CSS_SELECTOR, 'span.value')

            label = label_span.text.strip()
            value = value_span.text.strip()

            if label:
                specs_data[label] = value
        except NoSuchElementException:
            logger.debug("Warning: unexpected structure in specs element. Skipping this item.")
            continue
        except StaleElementReferenceException:
             logger.warning("Warning: StaleElementReferenceException while processing this element. Skipping.")
             continue

    logger.info(f"Extracted {len(specs_data)} spec itens.")
    return specs_data

def extract_bom(driver: WebDriver) -> List[Dict[str, Any]]:
    # extracts the BOM from the parts tab
    bom_data: List[Dict[str, Any]] = []
    if not click_tab(driver, 'parts'):
        logger.warning("Error accessing parts tab")
        return bom_data

    logger.info("Extracting BOM")
    bom_table_locator = (By.CSS_SELECTOR, '.pane[data-tab="parts"] .data-table')
    bom_table = safe_find_element(driver, *bom_table_locator, wait_time=10)

    if not bom_table:
        logger.info("BOM table not found")
        return bom_data

    bom_rows_locator = (By.CSS_SELECTOR, '.pane[data-tab="parts"] .data-table tbody tr')
    bom_rows = safe_find_elements(driver, *bom_rows_locator, wait_time=10)

    if not bom_rows:
        logger.info("BOM elements not found")
        return bom_data

    headers = []
    try:
        header_elements = bom_table.find_elements(By.CSS_SELECTOR, 'thead th')
        headers = [h.text.strip() for h in header_elements if h.text.strip()]
        logger.debug(f"BOM headers found: {headers}")
    except NoSuchElementException:
        logger.debug("Warning: BOM table headers not found. Using default headers")
        headers = ["Part Number", "Description", "Quantity"]

    part_number_idx, description_idx, quantity_idx = -1, -1, -1
    try:
        try: part_number_idx = headers.index("Part Number")
        except ValueError: pass
        if part_number_idx == -1: part_number_idx = 0

        try: description_idx = headers.index("Description")
        except ValueError: pass
        if description_idx == -1 and len(headers) > 1: description_idx = 1

        for i, h in enumerate(headers):
             if "Quantity" in h:
                 quantity_idx = i
                 break
        if quantity_idx == -1 and len(headers) > 2:
            quantity_idx = 2


        valid_indices = [idx for idx in [part_number_idx, description_idx, quantity_idx] if idx != -1]
        if not valid_indices:
            logger.warning("Error: No valid indices found for BOM data extraction.")
            return bom_data

        for row in bom_rows:
            try:
                cells = row.find_elements(By.CSS_SELECTOR, 'td')
                if len(cells) > max(valid_indices):
                    part_number = cells[part_number_idx].text.strip() if part_number_idx != -1 else ""
                    description = cells[description_idx].text.strip() if description_idx != -1 else ""
                    quantity_text = cells[quantity_idx].text.strip() if quantity_idx != -1 else ""

                    quantity: Any = quantity_text
                    if quantity_text:
                        try:
                            num_match = re.match(r'^\s*(\d+\.?\d*)\s*', quantity_text)
                            if num_match:
                                quantity = float(num_match.group(1))
                        except ValueError:
                            logger.debug(f"Error converting '{quantity_text}' to float")

                    if part_number:
                         bom_data.append({
                             "part_number": part_number,
                             "description": description,
                             "quantity": quantity
                         })
                    else:
                         logger.debug(f"Warning: register without part number '{row.text}'. Skipping")

            except (NoSuchElementException, StaleElementReferenceException) as e:
                logger.warning(f"Error proccessing BOM register: {e}. Skipping")
                continue

    except Exception as e:
        logger.error(f"Error proccessing BOM register: {e}")
    return bom_data

def extract_static_asset_urls(driver: WebDriver) -> Dict[str, str | None]:
    # Extracts static asset urls from the html. Used for manuals and images
    asset_urls: Dict[str, str | None] = {
        'image': None,
        'manual': None,
    }

    logger.info("Extracting static URLs")

    # --- Imagem ---
    image_element_locator = (By.CSS_SELECTOR, '.product-image')
    image_element = safe_find_element(driver, *image_element_locator, wait_time=5)
    if image_element:
        img_src = image_element.get_attribute('src')
        if img_src:
            asset_urls['image'] = urljoin(driver.current_url, img_src)
            logger.info(f"  Image URL found: {asset_urls['image']}")
        else:
            logger.debug("  Image not found")
    else:
        logger.debug("  Image's element not found")

    # --- PDF Manual ---
    pdf_link_locator = (By.ID, 'infoPacket')
    pdf_link_element = safe_find_element(driver, *pdf_link_locator, wait_time=5)
    if pdf_link_element:
        pdf_href = pdf_link_element.get_attribute('href')
        if pdf_href:
            asset_urls['manual'] = urljoin(driver.current_url, pdf_href)
            logger.info(f"  PDF Manual URL found: {asset_urls['manual']}")
        else:
            logger.debug("  PDF not found.")
    else:
         logger.debug("  PDFs element not found.")

    logger.info("Static URLs extracted")
    return asset_urls