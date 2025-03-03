import yaml
import logging.config
import os
from src.scrapers.linkedin_scraper import LinkedInScraper

def load_config():
    config_path = os.path.join('config', 'config.yaml')
    logging_config_path = os.path.join('config', 'logging_config.yaml')
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    with open(logging_config_path, 'r') as f:
        logging_config = yaml.safe_load(f)
        logging.config.dictConfig(logging_config)

    return config

def main():
    config = load_config()
    logger = logging.getLogger('linkedin_scraper')
    
    try:
        scraper = LinkedInScraper(config)
        # Change "Data Engineer" to your desired search term
        scraper.scrape_jobs("Data Engineer")
    except Exception as e:
        logger.error(f"Error during scraping: {e}")

if __name__ == "__main__":
    main()
