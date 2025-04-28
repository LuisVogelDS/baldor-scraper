import time
import logging
from typing import List, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)

def safe_find_element(driver: WebDriver, by: By, value: str, wait_time: int = 10):
    try:
        element = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
        return None

def safe_find_elements(driver: WebDriver, by: By, value: str, wait_time: int = 10):
    try:
        WebDriverWait(driver, wait_time).until(
             EC.presence_of_element_located((by, value))
        )
        elements = driver.find_elements(by, value)
        return elements
    except (TimeoutException, NoSuchElementException):
        return []

def click_tab(driver: WebDriver, tab_name: str):
    # clicks on a tab if its not already active
    logger.debug(f"Trying to access tab {tab_name}")
    tab_locator = (By.CSS_SELECTOR, f'nav ul li[data-tab="{tab_name}"]')
    try:
        tab_element = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(tab_locator)
        )
        if 'active' not in tab_element.get_attribute('class'):
             logger.debug(f"Tab '{tab_name}' not active. Clicking")
             tab_element.click()
             logger.info(f"Tab '{tab_name}' clicked")
             time.sleep(1)
             return True
        else:
             logger.debug(f"Tab '{tab_name}' is already active. No need to click.")
             return True
    except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
        logger.warning(f"Error: couldnt click on tab '{tab_name}' Error: {e}")
        return False

def handle_cookie_overlay(driver: WebDriver):
    # handles the cookie overlay
    overlay_locator = (By.CSS_SELECTOR, '.adroll_consent_notice')
    dismiss_button_locators = [
        (By.ID, 'adroll_consent_accept'),
        (By.XPATH, "//div[contains(@class, 'adroll_consent_notice')]//button[contains(text(), 'Allow All')]"),
    ]

    logger.debug("Trying possible cookies")
    try:
        overlay_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(overlay_locator)
        )
        logger.info("Overlay '.adroll_consent_notice' detected")

        clicked_dismissal = False
        logger.debug("Looking for a dismiss button")
        wait_for_dismiss_button = WebDriverWait(driver, 10)

        for locator in dismiss_button_locators:
            try:
                logger.debug(f"Trying locator {locator}")
                dismissal_button = wait_for_dismiss_button.until(
                     EC.element_to_be_clickable(locator)
                )
                dismissal_button.click()
                logger.info("Button clicked")
                clicked_dismissal = True
                break
            except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
                logger.debug(f"Button not found or clickable. Error: {e}")
                continue

        if clicked_dismissal:
            logger.debug("Waiting for overlay to disappera")
            WebDriverWait(driver, 10).until(
                 EC.invisibility_of_element_located(overlay_locator)
            )
            logger.info("Overlay disappeared.")
        else:
             logger.warning("No clickable button found to close the overlay. Download may be intercepted")

    except (TimeoutException, NoSuchElementException):
        logger.debug("Overlay '.adroll_consent_notice' not detected")
    except Exception as e:
         logger.error(f"Error handling cookie overlay: {e}")