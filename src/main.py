import logging
import sys
import json
import os

#local imports
from page_interaction import scrape_product_page
from utils import DATA_OUTPUT_DIR, clean_filename, PROJECT_ROOT

# initialize logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# IDs listing
PRODUCT_IDS =  ["CEM7073T",

                ]


if __name__ == "__main__":
    logger.info("PIPELINE: Starting the scraping pipeline")
    logger.info(f"project root: {PROJECT_ROOT}")

    for p_id in PRODUCT_IDS:
        try:
            # scraps each product
            scraped_data = scrape_product_page(p_id)

            if scraped_data:
                # save the structured data to a PRODUCT_ID.json file
                json_filename = f"{clean_filename(p_id)}.json"
                json_filepath = os.path.join(DATA_OUTPUT_DIR, json_filename)
                logger.info(f"Saving structured data as {json_filepath}")
                try:
                    with open(json_filepath, 'w', encoding='utf-8') as f:
                        json.dump(scraped_data, f, indent=2, ensure_ascii=False) # Use indent=2 para formato legível
                    logger.info("Data saved successfully")
                except IOError as e:
                    logger.error(f"Error saving {json_filepath}: {e}")
            else:
                logger.warning(f"Scraping for {p_id} returned None, scraping failed.")

        except Exception as e:
             logger.error(f"Error scraping {p_id}: {e}", exc_info=True)

    logger.info("PIPELINE: Scraping concluded for all files.")