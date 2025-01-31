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
from selenium.common.exceptions import NoSuchElementException

from linkedin_scraper.config import ScraperConfig
from linkedin_scraper.utils import retry_on_failure, setup_logging
from sqlalchemy.orm import sessionmaker

from linkedin_scraper.models import Job, init_db
from linkedin_scraper.constants import LinkedInConstants


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
            "Referer": LinkedInConstants.BASE_URL,
            "DNT": "1",
        }

    def scrape_jobs(self) -> None:
        """
        Main scraping function for LinkedIn jobs.

        First gets all job IDs for each location, then fetches job details for each ID.
        Handles failures by tracking failed jobs and their error messages.
        Finally saves both successful and failed jobs to output file.
        """
        self.logger.info("Starting scraping process...")
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
            self._login(driver)

            for geo_id in self.config.geo_ids:
                ids = self._get_all_job_ids(driver, self.config.keywords, geo_id)
                job_ids.extend(ids)

            for job_id in job_ids:
                try:
                    details = self._get_job_details(driver, job_id)
                    if details and self._should_include_job(details):
                        self.logger.info("Job included")
                        all_jobs.append(details)
                    else:
                        self.logger.info("Job excluded")
                except Exception as e:
                    self.logger.error(f"Error: {e}")
                    continue
        finally:
            driver.quit()

        self.logger.info(
            f"Found {len(all_jobs)} successful jobs and {len(failed_jobs)} failed jobs"
        )

        if len(all_jobs) > 0 or len(failed_jobs) > 0:
            self._save_results(all_jobs, failed_jobs)

    def _get_job_ids(self, driver: webdriver.Chrome) -> List[str]:
        """
        Gets job IDs from LinkedIn current search page.
        Args:
            driver: Selenium webdriver instance

        Returns:
            List of job IDs found on the current search page
        """
        job_cards = driver.find_elements(
            By.CSS_SELECTOR, LinkedInConstants.JOB_LIST_CSS
        )
        self.logger.info(f"Found {len(job_cards)} job cards in this page")

        job_ids = set()

        for card in job_cards:
            try:
                if job_id := card.get_attribute("data-job-id"):
                    job_ids.add(job_id)
            except StaleElementReferenceException:
                continue
            except Exception as e:
                self.logger.error(f"Error extracting job ID: {str(e)}")
                continue

        self.logger.info(f"Total job IDs extracted in this page: {len(job_ids)}")
        return list(job_ids)

    def _get_all_job_ids(
        self, driver: webdriver.Chrome, keyword: str, geo_id: str
    ) -> List[str]:
        """Gets all jobs IDs from LinkedIn search pages."""
        self.logger.info(f"Getting jobs for keyword: {keyword}, geo_id: {geo_id}")

        url = f"{LinkedInConstants.JOBS_SEARCH_URL}?keywords={keyword}&f_TPR={self.config.date_filter}&geoId={geo_id}"
        driver.get(url)
        time.sleep(LinkedInConstants.WAIT_MEDIUM)

        all_job_ids = set()

        try:
            all_job_ids.update(self._get_job_ids(driver))

            while True:
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, "li.active + li")
                    next_button.click()

                    # This isn't the best approack, I should wait for an element,
                    # but for the rate limit it's better to wait some more time 🤷
                    self.logger.info(
                        f"Waiting {LinkedInConstants.WAIT_SHORT}s before continue..."
                    )
                    time.sleep(LinkedInConstants.WAIT_SHORT)

                    all_job_ids.update(self._get_job_ids(driver))

                except NoSuchElementException:
                    self.logger.info("No more pages to process")
                    break
                except Exception as e:
                    self.logger.error(f"Error during pagination: {str(e)}")
                    break

        except Exception as e:
            self.logger.error(f"Error during job extraction: {str(e)}")

        job_ids_list = list(all_job_ids)
        self.logger.info(f"Total unique job IDs extracted: {len(job_ids_list)}")
        return job_ids_list

    def _get_job_details(self, driver: webdriver.Chrome, job_id: str) -> Optional[Dict]:
        """
        Gets detailed information for a specific job.

        Args:
            driver: Selenium webdriver instance
            job_id: LinkedIn job ID

        Returns:
            Dictionary containing job details or None if extraction fails
        """

        self.logger.info(f"Getting details for job {job_id}")

        url = f"{LinkedInConstants.BASE_URL}/jobs/search/?currentJobId={job_id}"
        driver.get(url)
        time.sleep(LinkedInConstants.WAIT_MEDIUM)

        try:

            details = {
                "job_id": job_id,
                "title": driver.find_element(
                    By.CLASS_NAME, LinkedInConstants.JOB_TITLE_CLASS
                ).text,
                "company": driver.find_element(
                    By.CLASS_NAME, LinkedInConstants.COMPANY_NAME_CLASS
                ).text,
                "description": driver.find_element(
                    By.CLASS_NAME, LinkedInConstants.DESCRIPTION_CLASS
                ).text,
                "url": url,
                "location": driver.find_element(
                    By.CLASS_NAME,
                    LinkedInConstants.LOCATION_CLASS,
                )
                .find_element(By.TAG_NAME, "span")
                .text,
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

        print("Keyword matches:")

        for keyword in self.config.contains:
            print(f"{keyword}: {keyword.lower() in content}")

        if self.config.contains:
            if not any(keyword.lower() in content for keyword in self.config.contains):
                return False

        if self.config.non_contains:
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
        self.logger.info("Attempting login")

        driver.get(LinkedInConstants.LOGIN_URL)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        ).send_keys(self.config.linkedin_email)

        driver.find_element(By.ID, "password").send_keys(self.config.linkedin_password)
        driver.find_element(By.CSS_SELECTOR, "[type=submit]").click()

        # I need time to pass the manual validation!
        time.sleep(LinkedInConstants.WAIT_LONG)

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

        self.logger.info(
            f"Attempting to save {len(jobs)} successful and {len(failed_jobs)} failed jobs"
        )

        try:
            for job_data in jobs:
                self.logger.info(f"Processing job {job_data['job_id']}")
                job = Job(
                    success=True,
                    url=job_data["url"],
                    title=job_data["title"],
                    job_id=job_data["job_id"],
                    company=job_data["company"],
                    location=job_data.get("location"),
                    description=job_data["description"],
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
            self.logger.error(f"Database error: {str(e)}")
            session.rollback()

        finally:
            session.close()


def main():
    config = ScraperConfig.from_env()
    scraper = LinkedInJobScraper(config)
    scraper.scrape_jobs()


if __name__ == "__main__":
    main()
