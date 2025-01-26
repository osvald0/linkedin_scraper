import json
import time
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service

from linkedin_scraper.config import ScraperConfig
from linkedin_scraper.utils import retry_on_failure, setup_logging
from sqlalchemy.orm import sessionmaker

from linkedin_scraper.models import Job, init_db


class LinkedInJobScraper:
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.engine = init_db()
        self.logger = setup_logging()
        self.Session = sessionmaker(bind=self.engine)

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.linkedin.com",
            "DNT": "1",
        }

    def scrape_jobs(self) -> None:
        """
        Main scraping function for LinkedIn jobs.

        First gets all job IDs for each location, then fetches job details for each ID.
        Handles failures by tracking failed jobs and their error messages.
        Finally saves both successful and failed jobs to output file.
        """
        self.logger.info("Starting scraping process")
        options = webdriver.ChromeOptions()

        if self.config.headless:
            self.logger.info("Running in headless mode")
            options.add_argument("--headless")

        driver = webdriver.Chrome(options=options)
        self.logger.info("Browser initialized")

        job_ids = []
        all_jobs = []
        failed_jobs = []

        try:

            self.logger.info("Attempting login")
            self._login(driver)

            for geo_id in self.config.geo_ids:
                ids = self._get_job_ids(driver, self.config.keywords, geo_id)
                job_ids.extend(ids)

            for job_id in job_ids:
                try:
                    details = self._get_job_details(driver, job_id)
                    if details and self._should_include_job(details):
                        all_jobs.append(details)

                except Exception as e:
                    failed_jobs.append({"job_id": job_id, "error": str(e)})
                    contin
        finally:
            driver.quit()

        if all_jobs or failed_jobs:
            self._save_results(all_jobs, failed_jobs)

    def _get_job_ids(
        self, driver: webdriver.Chrome, keyword: str, geo_id: str
    ) -> List[str]:
        """
        Gets job IDs from LinkedIn search page.

        Args:
            driver: Selenium webdriver instance
            keyword: Search term for jobs
            geo_id: LinkedIn location ID

        Returns:
            List of job IDs found on the search page
        """

        self.logger.info(f"Getting jobs for keyword: {keyword}, geo_id: {geo_id}")
        url = f"https://www.linkedin.com/jobs/search?keywords={keyword}&f_TPR={self.config.date_filter}&geoId={geo_id}"
        self.logger.info(f"Navigating to: {url}")
        driver.get(url)
        # breakpoint()
        time.sleep(5)

        # I have issues with this selector, rate limit again?
        # job_list = driver.find_element(By.CLASS_NAME, "jobs-search__results-list")

        job_cards = driver.find_elements(
            By.CSS_SELECTOR, '[data-job-id]:not([data-job-id="search"])'
        )

        self.logger.info(f"Found {len(job_cards)} job cards")
        self.logger.info(job_cards)

        job_ids = []

        for card in job_cards:
            try:
                job_id = card.get_attribute("data-job-id")
                self.logger.info(f"Extracted job ID: {job_id}")
                if job_id:
                    job_ids.append(job_id)

            except Exception as e:
                self.logger.error(f"Error extracting job ID: {str(e)}")

        self.logger.info(f"Total job IDs extracted: {len(job_ids)}")
        return job_ids

    def _get_job_details(self, driver: webdriver.Chrome, job_id: str) -> Optional[Dict]:
        """
        Gets detailed information for a specific job.

        Args:
            driver: Selenium webdriver instance
            job_id: LinkedIn job ID

        Returns:
            Dictionary containing job details or None if extraction fails
        """
        url = f"https://www.linkedin.com/jobs/search/?currentJobId={job_id}"
        driver.get(url)
        # TODO: Create a function to generate random sleeps times between 5 and 10 secs.
        time.sleep(10)

        try:
            details = {
                "job_id": job_id,
                "title": driver.find_element(
                    By.CLASS_NAME, "job-details-jobs-unified-top-card__job-title"
                ).text,
                "company": driver.find_element(
                    By.CLASS_NAME, "job-details-jobs-unified-top-card__company-name"
                ).text,
                "description": driver.find_element(
                    By.CLASS_NAME, "jobs-description__content"
                ).text,
                "url": url,
            }
            self.logger.info(f"Extracted job details for {job_id}")
            return details

        except Exception as e:
            self.logger.error(f"Error extracting job {job_id}: {str(e)}")
            return None

    def _should_include_job(self, job_details: Dict) -> bool:
        """
        Checks if job matches required filters.

        Args:
            job_details: Dictionary of job information

        Returns:
            True if job should be included based on contains/non_contains filters
        """
        content = " ".join(str(value).lower() for value in job_details.values())

        if not all(keyword.lower() in content for keyword in self.config.contains):
            return False

        if any(keyword.lower() in content for keyword in self.config.non_contains):
            return False

        return True

    def _login(self, driver):
        """
        Logs into LinkedIn using configured credentials.

        Args:
            driver: Selenium webdriver instance

        Navigates to login page and authenticates using email/password from config.
        """
        driver.get("https://www.linkedin.com/login")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        ).send_keys(self.config.linkedin_email)

        driver.find_element(By.ID, "password").send_keys(self.config.linkedin_password)
        driver.find_element(By.CSS_SELECTOR, "[type=submit]").click()
        time.sleep(15)

    def _save_results_json(self, jobs: List[Dict], failed_jobs: List[Dict]) -> None:
        """
        Saves scraped jobs to JSON file.

        Args:
            jobs: List of successfully scraped job details
            failed_jobs: List of failed jobs with error messages

        Saves statistics and both successful/failed jobs to configured output file.
        """
        output = {
            "successful_jobs": jobs,
            "failed_jobs": failed_jobs,
            "stats": {
                "total_jobs": len(jobs) + len(failed_jobs),
                "successful": len(jobs),
                "failed": len(failed_jobs),
            },
        }

        output_path = os.path.abspath(self.config.output_file)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        self.logger.info(
            f"Saved {len(jobs)} successful and {len(failed_jobs)} failed jobs to: {output_path}"
        )

    def _save_results(self, jobs: List[Dict], failed_jobs: List[Dict]) -> None:
        """Save results to SQLite database and JSON file."""
        session = self.Session()

        try:
            for job_data in jobs:
                job = Job(
                    job_id=job_data["job_id"],
                    title=job_data["title"],
                    company=job_data["company"],
                    description=job_data["description"],
                    url=job_data["url"],
                    success=True,
                )
                session.merge(job)

            for failed in failed_jobs:
                job = Job(job_id=failed["job_id"], success=False, error=failed["error"])
                session.merge(job)

            session.commit()
            self.logger.info(
                f"Saved {len(jobs)} successful and {len(failed_jobs)} failed jobs to database"
            )

        except Exception as e:
            session.rollback()
            self.logger.error(f"Database error: {str(e)}")

        finally:
            session.close()


def main():
    config = ScraperConfig.from_env()
    scraper = LinkedInJobScraper(config)
    scraper.scrape_jobs()


if __name__ == "__main__":
    main()
