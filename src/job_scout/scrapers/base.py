import datetime
import logging
from abc import ABC, abstractmethod

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class JobData:
    """Standard job data container used across all scrapers."""

    def __init__(
        self,
        title: str,
        source: str,
        company: str | None = None,
        location: str | None = None,
        description: str | None = None,
        salary_min: float | None = None,
        salary_max: float | None = None,
        salary_currency: str | None = None,
        job_type: str | None = None,
        experience_level: str | None = None,
        remote: bool = False,
        url: str | None = None,
        apply_url: str | None = None,
        tags: str | None = None,
        requirements: str | None = None,
        posted_date: datetime.datetime | None = None,
        application_deadline: datetime.datetime | None = None,
        external_id: str | None = None,
    ):
        self.title = title
        self.source = source
        self.company = company
        self.location = location
        self.description = description
        self.salary_min = salary_min
        self.salary_max = salary_max
        self.salary_currency = salary_currency
        self.job_type = job_type
        self.experience_level = experience_level
        self.remote = remote
        self.url = url
        self.apply_url = apply_url
        self.tags = tags
        self.requirements = requirements
        self.posted_date = posted_date
        self.application_deadline = application_deadline
        self.external_id = external_id

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "source": self.source,
            "company": self.company,
            "location": self.location,
            "description": self.description,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_currency": self.salary_currency,
            "job_type": self.job_type,
            "experience_level": self.experience_level,
            "remote": self.remote,
            "url": self.url,
            "apply_url": self.apply_url,
            "tags": self.tags,
            "requirements": self.requirements,
            "posted_date": self.posted_date,
            "application_deadline": self.application_deadline,
            "external_id": self.external_id,
        }


class BaseScraper(ABC):
    "Base scraper for a scraper classes"

    SOURCE_NAME: str = "unknown"

    _USER_AGENTS = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    )

    def __init__(self) -> None:
        import random

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": random.choice(self._USER_AGENTS),
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

    def rorate_user_agents(self):
        "Rotate the user Agents."
        import random

        self.session.headers["user-Agent"] = random.choice(self._USER_AGENTS)

    def fetch_page(
        self, url: str, parameters: dict | None = None
    ) -> BeautifulSoup | None:
        "Fetch a page and return a parsed HTML."
        self.rorate_user_agents()
        try:
            response = self.session.get(url=url, params=parameters)
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except requests.RequestException as e:
            logger.error(f"{self.SOURCE_NAME} failed to fetch {url}: {e}")
            return None

    def fetch_json(self, url: str, parameters: dict | None = None) -> dict | None:
        "Fetch json data for a url page endpoint."
        self.rorate_user_agents()
        try:
            response = self.session.get(url=url, params=parameters)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"{self.SOURCE_NAME} failed to json {url}: {e}")
            return None

    @abstractmethod
    def scrape(
        self, seacrh_query: str, location: str, number_of_pages: int
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
