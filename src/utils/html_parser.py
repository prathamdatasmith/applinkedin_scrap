import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def create_soup_from_url(url: str, headers: dict) -> BeautifulSoup:
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return None

def extract_tech_stack(description: str, tech_keywords: list) -> str:
    """Extract technology stack from job description with improved matching."""
    if not description or not tech_keywords:
        return "Not specified"
    
    found_tech = set()  # Use set to avoid duplicates
    description_lower = description.lower()
    
    # Process each keyword
    for tech in tech_keywords:
        # Handle variations of the same technology
        tech_variations = {
            tech.lower(),
            tech.lower().replace(' ', ''),
            tech.lower().replace('-', ''),
            tech.lower().replace('.', '')
        }
        
        # Check for each variation
        if any(variant in description_lower for variant in tech_variations):
            found_tech.add(tech)
    
    return ', '.join(sorted(found_tech)) if found_tech else 'Not specified'

def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""
    # Remove extra whitespace and normalize
    cleaned = ' '.join(text.split())
    # Remove special characters but keep basic punctuation
    cleaned = ''.join(char for char in cleaned if char.isprintable())
    return cleaned.strip()

def extract_salary_range(description: str) -> str:
    """Extract salary information if available."""
    salary_keywords = ['salary', 'compensation', 'pay', 'ctc', 'package']
    lines = description.lower().split('\n')
    
    for line in lines:
        if any(keyword in line for keyword in salary_keywords):
            # Find amounts with common Indian formats (lakhs/crores)
            if any(term in line for term in ['lakh', 'lac', 'crore']):
                return clean_text(line)
    return 'Not specified'
