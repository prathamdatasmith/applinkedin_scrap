import logging
from bs4 import BeautifulSoup
import requests
import time

logger = logging.getLogger(__name__)

class JobDescriptionScraper:
    def __init__(self, headers):
        self.headers = headers
        self.logger = logging.getLogger(__name__)

    def get_description(self, url: str) -> str:
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try multiple possible description containers
            description_selectors = [
                'div.description__text',
                'div.show-more-less-html__markup',
                'div.job-description',
                'section.description'
            ]
            
            for selector in description_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    return desc_elem.get_text(strip=True, separator=' ')
            
            return "Description not available"
            
        except Exception as e:
            self.logger.error(f"Error fetching job description: {e}")
            return "Failed to fetch description"
