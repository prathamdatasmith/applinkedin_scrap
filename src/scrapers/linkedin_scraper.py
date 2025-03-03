import logging
import time
import csv
import os
from urllib.parse import urlencode
from ..utils.html_parser import create_soup_from_url, extract_tech_stack
from .job_description_scraper import JobDescriptionScraper
from ..constants.tech_keywords import TECH_KEYWORDS

logger = logging.getLogger(__name__)

class LinkedInScraper:
    def __init__(self, config):
        self.config = config
        self.job_desc_scraper = JobDescriptionScraper(config['scraper']['headers'])
        self.logger = logging.getLogger(__name__)
        self.tech_keywords = TECH_KEYWORDS  # Store tech keywords directly
        self.desc_folder = 'job_descriptions'
        os.makedirs(self.desc_folder, exist_ok=True)

    def scrape_jobs(self, keywords: str):
        print(f"\n🚀 Starting LinkedIn job scraping for: {keywords}")
        jobs_per_page = self.config['scraper']['jobs_per_page']
        processed_jobs = 0
        page = 0

        print(f"🔍 Search parameters:")
        print(f"    - Keywords: {keywords}")
        print(f"    - Location: India")
        with open(self.config['output']['file'], mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(self.config['output']['columns'])

            while True:
                print(f"\n📄 Processing page {page + 1}...")
                params = self._build_search_params(keywords, page, jobs_per_page)
                url = f"{self.config['scraper']['base_url']}?{urlencode(params)}"
                
                jobs = self._process_page(url, writer)
                if not jobs:
                    print("🛑 No more jobs found on this page. Stopping.")
                    break

                processed_jobs += jobs
                print(f"⏳ Progress: Processed {processed_jobs} jobs so far...")
                page += 1
                print(f"💤 Waiting {self.config['scraper']['delay']['between_pages']} seconds before next page...")
                time.sleep(self.config['scraper']['delay']['between_pages'])

        print(f"\n✅ Finished scraping. Total jobs processed: {processed_jobs}")
        print(f"💾 Results saved to: {self.config['output']['file']}")
        print("🎉 Scraping completed successfully!\n")

    def _build_search_params(self, keywords, page, jobs_per_page):
        return {
            'keywords': keywords,
            'location': 'India',
            'geoId': self.config['locations']['india']['geoId'],
            'start': page * jobs_per_page,
            'position': 1,
            'pageNum': page,
            'f_WT': '2',
            'locationId': 'OTHERS.india'
        }

    def _process_page(self, url, writer):
        soup = create_soup_from_url(url, self.config['scraper']['headers'])
        if not soup:
            print("❌ Failed to fetch page content")
            return 0

        job_cards = soup.find_all('div', {'class': 'base-card'})
        if not job_cards:
            return 0

        print(f"📊 Found {len(job_cards)} jobs on this page")
        jobs_processed = 0
        
        for i, job in enumerate(job_cards, 1):
            try:
                title_elem = job.find('h3', {'class': 'base-search-card__title'})
                company_elem = job.find('h4', {'class': 'base-search-card__subtitle'})
                location_elem = job.find('span', {'class': 'job-search-card__location'})
                link_elem = job.find('a', {'class': 'base-card__full-link'})

                if not all([title_elem, company_elem, location_elem, link_elem]):
                    continue

                job_data = {
                    'job_title': self._extract_text(title_elem),  # Changed from 'title'
                    'company': self._extract_text(company_elem),   # Keep as 'company'
                    'location': self._extract_text(location_elem), # Keep as 'location'
                    'job_link': self._extract_link(link_elem),
                    'tech_stack': self._extract_tech_stack(description), # Changed to 'tech_stack'
                    'date_posted': self._extract_text(job.find('time'))
                }

                # Save description to file
                desc_filename = f"job_desc_{int(time.time())}_{i}.txt"
                desc_filepath = os.path.join(self.desc_folder, desc_filename)
                description = self.job_desc_scraper.get_description(job_data['job_link'])
                
                with open(desc_filepath, 'w', encoding='utf-8') as f:
                    f.write(description)

                # Create markdown style links
                job_link_md = f"[Job Link]({job_data['job_link']})"
                desc_link_md = f"[Job Description]({desc_filename})"
                
                tech_stack = extract_tech_stack(description, self.tech_keywords)

                writer.writerow([
                    job_data['job_title'],    # Changed from 'title'
                    job_data['company'],
                    job_data['location'],
                    job_link_md,  # Modified to markdown link
                    desc_link_md,  # Modified to markdown link
                    job_data['tech_stack']     # Changed from 'technologies'
                ])

                jobs_processed += 1
                print(f"  ✓ [{i}/{len(job_cards)}] Processed: {job_data['job_title']} at {job_data['company']}")
                time.sleep(self.config['scraper']['delay']['between_jobs'])

            except Exception as e:
                print(f"  ⚠️ Error processing job card: {e}")
                continue

        return jobs_processed