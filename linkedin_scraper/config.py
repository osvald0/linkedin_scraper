import os
from dataclasses import dataclass
from typing import Dict, List

from dotenv import load_dotenv


@dataclass
class ScraperConfig:
    """
    Configuration class for LinkedIn job scraper.

    Attributes:
        keywords: Search term for jobs
        geo_ids: List of LinkedIn location IDs
        date_filter: Time filter for job postings
        contains: Required keywords in job details
        non_contains: Excluded keywords from job details
        linkedin_email: LinkedIn login email
        linkedin_password: LinkedIn login password
        output_file: Path to save results JSON
    """

    keywords: str
    geo_ids: List[str]
    date_filter: str
    contains: List[str]
    non_contains: List[str]
    linkedin_email: str
    linkedin_password: str
    headless: bool = False
    output_file: str = "jobs.json"

    DATE_FILTER_MAP = {
        "past_24h": "r86400",
        "past_week": "r604800",
        "past_month": "r2592000",
        "any_time": "",
    }

    LOCATION_MAP = {
        "uk": "101165590",
        "netherlands": "102890719",
        "germany": "101282230",
        "uruguay": "100867946",
    }

    @classmethod
    def from_env(cls):
        load_dotenv()
        locations = os.getenv("LOCATIONS", "").lower().split(",")
        geo_ids = [cls.LOCATION_MAP.get(location.strip()) for location in locations]
        return cls(
            keywords=os.getenv("KEYWORDS", ""),
            geo_ids=geo_ids,
            date_filter=cls.DATE_FILTER_MAP.get(os.getenv("DATE_FILTER", "past_24h")),
            contains=os.getenv("CONTAINS", "").split(","),
            non_contains=os.getenv("NON_CONTAINS", "").split(","),
            linkedin_email=os.getenv("LINKEDIN_EMAIL"),
            linkedin_password=os.getenv("LINKEDIN_PASSWORD"),
            headless=os.getenv("HEADLESS", "false").lower() == "true",
            output_file=os.getenv("OUTPUT_FILE", "jobs.json"),
        )
