import datetime
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from typing import ClassVar

logger = logging.getLogger(__name__)


@dataclass
class JobData:
    """Standard job data container used across all scrapers."""

    title: str
    source: str
    company: str | None = None
    location: str | None = None
    industry: str | None = None
    description: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = "Ksh. "
    job_type: str | None = None
    experience_level: str | None = None
    minimum_experience: str | None = None
    remote: bool = False
    url: str | None = None
    apply_url: str | None = None
    tags: str | None = None
    skills: str | None = None
    qualifications: str | None = None
    posted_date: datetime.datetime | None = None
    application_deadline: datetime.datetime | None = None
    external_id: str | None = None


class BaseScraper(ABC):
    "Base scraper for a scraper classes"

    SOURCE_NAME: ClassVar[str] = "unknown"

    _USER_AGENTS: ClassVar[tuple[str, ...]]= (
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64), "
            "AppleWebKit/537.36 (KHTML, like Gecko), "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    )

    def __init__(self) -> None:
        import random

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": random.choice(self._USER_AGENTS),
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                ),
                # "Accept-Encoding": "gzip, deflate, br",
                # "Connection": "keep-alive",
                # "Upgrade-Insecure-Requests": "1",
            }
        )

    def rotate_user_agent(self):
        "Rotate the user Agents."
        import random

        self.session.headers["User-Agent"] = random.choice(self._USER_AGENTS)

    def fetch_page(
        self, url: str, parameters: dict | None = None
    ) -> BeautifulSoup | None:
        "Fetch a page and return a parsed HTML."
        self.rotate_user_agent()
        try:
            response = self.session.get(url=url, params=parameters, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
            # return response
        except requests.RequestException as e:
            logger.error(f"{self.SOURCE_NAME} failed to fetch {url}: {e}")
            return None

    def fetch_json(self, url: str, parameters: dict | None = None) -> dict | None:
        "Fetch json data for a url page endpoint."
        self.rotate_user_agent()
        try:
            response = self.session.get(url=url, params=parameters)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"{self.SOURCE_NAME} failed to json {url}: {e}")
            return None

    @abstractmethod
    def scrape(
        self,
        # seacrh_query: str | None = None,
        location: str | None = None,
        number_of_pages: int = 3,
    ) -> list[JobData]:
        """Scrape jobs. Must be implemented by each scraper."""
        raise NotImplementedError(
            "This method is not meant to be called directly"
            "Please instantiate a scraper class and implement it then call this class."
            """For example
            
            class Scraper(BaseScraper):
                SOURCE_NAME: str = "name". 
                
                def scrape(
                    self,
                    search_query: str,
                    location: str,
                    number_of_pages:int) -> list[JobData]:
                    ...
            """
        )
