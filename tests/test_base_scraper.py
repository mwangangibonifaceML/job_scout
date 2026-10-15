from __future__ import annotations

import datetime
import logging
from unittest.mock import MagicMock

import pytest
import requests
from bs4 import BeautifulSoup

from job_scout.scrapers.base import BaseScraper, JobData


class ConcreteScraper(BaseScraper):
    SOURCE_NAME = "test_scraper"

    def scrape(
        self, search_query: str, location: str, number_of_pages: int
    ) -> list[JobData]:
        return []


@pytest.fixture
def scraper() -> ConcreteScraper:
    "Return a scraper with a mocked HTTP session."
    instance = ConcreteScraper()
    instance.session = MagicMock()
    instance.session.headers = {"User-Agent": instance._USER_AGENTS[0]}
    return instance


def test_basescraper_cannot_instantiated_directly():
    with pytest.raises(TypeError):
        BaseScraper()


def test_congrate_scraper_can_be_instatiated():
    congrate_scraper = ConcreteScraper()
    assert isinstance(congrate_scraper, BaseScraper)
    assert congrate_scraper.SOURCE_NAME == "test_scraper"


def test_session_is_initialized_with_default_headers() -> None:
    instance = ConcreteScraper()

    try:
        headers = instance.session.headers
        assert headers["User-Agent"] in instance._USER_AGENTS
        assert headers["Accept-Language"] == "en-US,en;q=0.9"
        # assert headers["Accept-Encoding"] == "gzip, deflate, br"
        # assert headers["Connection"] == "keep-alive"
    finally:
        instance.session.close()


def test_fetch_page_return_beautiful_soup_object(scraper: ConcreteScraper) -> None:
    response = MagicMock()

    html = """
    <html>
        <head><title>Job Listings</title></head>
        <body><h1>Python Developer</h1></body>
    </html>
    """
    response.text = html
    response.raise_for_status.return_value = None

    scraper.session.get.return_value = response

    result = scraper.fetch_page("http://example.com/jobs", {"location": "Nairobi"})

    assert isinstance(result, BeautifulSoup)
    assert result.title.get_text(strip=True) == "Job Listings"
    assert result.find("h1").get_text(strip=True) == "Python Developer"


def test_fetch_page_returns_none_on_http_error(
    scraper: ConcreteScraper,
    caplog: pytest.LogCaptureFixture,
) -> None:
    scraper.session.get.side_effect = requests.HTTPError("404 Not Found")

    with caplog.at_level(logging.ERROR):
        result = scraper.fetch_page(
            "https://example.com/missing",
            {},
        )

    assert result is None
    assert "test_scraper failed to fetch" in caplog.text


def test_fetch_page_returns_none_on_timeout(
    scraper: ConcreteScraper,
) -> None:
    scraper.session.get.side_effect = requests.Timeout("Request timed out")

    result = scraper.fetch_page(
        "https://example.com/jobs",
        {},
    )

    assert result is None


def test_fetch_page_returns_none_on_connection_error(
    scraper: ConcreteScraper,
) -> None:
    scraper.session.get.side_effect = requests.ConnectionError("Connection failed")

    result = scraper.fetch_page(
        "https://example.com/jobs",
        {},
    )

    assert result is None


def test_fetch_json_returns_parsed_json(
    scraper: ConcreteScraper,
) -> None:
    expected_data = {
        "jobs": [
            {
                "title": "Python Developer",
                "company": "Example Ltd",
            }
        ]
    }

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = expected_data

    scraper.session.get.return_value = response

    result = scraper.fetch_json(
        "https://example.com/api/jobs",
        {"location": "Nairobi"},
    )

    assert result == expected_data
    response.json.assert_called_once_with()


def test_fetch_json_returns_none_on_http_error(
    scraper: ConcreteScraper,
    caplog: pytest.LogCaptureFixture,
) -> None:
    scraper.session.get.side_effect = requests.HTTPError("500 Internal Server Error")

    with caplog.at_level(logging.ERROR):
        result = scraper.fetch_json(
            "https://example.com/api/jobs",
            {},
        )

    assert result is None
    assert "test_scraper failed to json" in caplog.text


def test_fetch_json_returns_none_on_timeout(
    scraper: ConcreteScraper,
) -> None:
    scraper.session.get.side_effect = requests.Timeout("Request timed out")

    result = scraper.fetch_json(
        "https://example.com/api/jobs",
        {},
    )

    assert result is None


def test_fetch_json_returns_none_on_connection_error(
    scraper: ConcreteScraper,
) -> None:
    scraper.session.get.side_effect = requests.ConnectionError("Connection failed")

    result = scraper.fetch_json(
        "https://example.com/api/jobs",
        {},
    )

    assert result is None


def test_concrete_scraper_scrape_returns_jobs() -> None:
    instance = ConcreteScraper()

    result = instance.scrape(
        search_query="Python Developer",
        location="Nairobi",
        number_of_pages=2,
    )

    assert result == []


def test_job_data_initializes_required_field():
    job = JobData(title="Statistician", source="test_source")

    assert job.title == "Statistician"
    assert job.source == "test_source"


def test_job_data_optional_fields_default_correclty():
    job = JobData(title="Statistician", source="test_source")

    assert job.application_deadline == None
    assert job.industry == None
    assert job.apply_url == None
    assert job.company == None
    assert job.description == None
    assert job.experience_level == None
    assert job.url == None
    assert job.remote is False
    assert job.posted_date == None


def test_job_data_stores_all_supplied_fields() -> None:
    posted_date = datetime.datetime(2026, 10, 1, 9, 0, tzinfo=datetime.UTC)
    deadline = datetime.datetime(2026, 11, 1, 17, 0, tzinfo=datetime.UTC)

    job = JobData(
        title="Python Developer",
        source="test_source",
        company="Example Ltd",
        location="Nairobi",
        description="Build Python applications.",
        salary_min=100_000.0,
        salary_max=150_000.0,
        salary_currency="KES",
        job_type="Full-time",
        experience_level="Mid-level",
        remote=True,
        url="https://example.com/jobs/123",
        apply_url="https://example.com/apply/123",
        tags="Python, FastAPI",
        requirements="Python experience",
        posted_date=posted_date,
        application_deadline=deadline,
        external_id="123",
    )

    assert job.company == "Example Ltd"
    assert job.location == "Nairobi"
    assert job.description == "Build Python applications."
    assert job.salary_min == 100_000.0
    assert job.salary_max == 150_000.0
    assert job.salary_currency == "KES"
    assert job.job_type == "Full-time"
    assert job.experience_level == "Mid-level"
    assert job.remote is True
    assert job.url == "https://example.com/jobs/123"
    assert job.apply_url == "https://example.com/apply/123"
    assert job.tags == "Python, FastAPI"
    assert job.requirements == "Python experience"
    assert job.posted_date == posted_date
    assert job.application_deadline == deadline
    assert job.external_id == "123"


def test_job_data_to_dict_returns_all_fields() -> None:
    job = JobData(
        title="Python Developer",
        source="test_source",
        company="Example Ltd",
        remote=True,
        external_id="123",
    )

    result = job.to_dict()

    assert result == {
        "title": "Python Developer",
        "source": "test_source",
        "company": "Example Ltd",
        "industry": None,
        "location": None,
        "description": None,
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "job_type": None,
        "experience_level": None,
        "remote": True,
        "url": None,
        "apply_url": None,
        "tags": None,
        "requirements": None,
        "posted_date": None,
        "application_deadline": None,
        "external_id": "123",
    }
