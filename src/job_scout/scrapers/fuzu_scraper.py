from __future__ import annotations

import datetime
import json
import logging

from bs4 import BeautifulSoup

from job_scout.scrapers.base import BaseScraper, JobData
from job_scout.scrapers.utils import clean_job_description
from typing import ClassVar


# * get and configure the logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class FuzuScraper(BaseScraper):
    SOURCE_NAME = "Fuzu"
    BASE_URL = "https://www.fuzu.com"

    COUNTRY_IDS: ClassVar[dict[str, int]] = {"kenya": 1, "nigeria": 165, "uganda": 232}

    def scrape(
        self, location: str | None = None, number_of_pages: int = 3
    ) -> list[JobData]:
        """Scrape job listings from Fuzu"""

        if number_of_pages < 1:
            raise ValueError("number of pages must be at least 1.")

        location: str | None = (location or "kenya").lower()

        country_id: int | None = None
        if location not in self.COUNTRY_IDS:
            raise ValueError(
                f"Unsupported location: {location}."
                f" Please choose from these locations: {
                    ','.join(list(self.COUNTRY_IDS.keys()))
                }"
            )

        country_id = self.COUNTRY_IDS[location]
        jobs: list[JobData] = []

        for page in range(1, number_of_pages + 1):
            params = {"page": page, "filters[country_id]": country_id}
            url = f"{self.BASE_URL}/job"
            soup = self.fetch_page(url=url, parameters=params)

            if not soup:
                logger.warning("%s failed to fetch page %s", self.SOURCE_NAME, page)
                continue

            jobs_json = self._parse_job_listings(soup, location)
            if jobs_json:
                jobs.extend(jobs_json)
                logger.info(
                    f"{self.SOURCE_NAME} page {page} found {len(jobs_json)} jobs."
                )
            else:
                logger.warning(f"page {page} contained no jobs.")

        logger.info(f"{self.SOURCE_NAME} found {len(jobs)} total jobs.")
        return self._enrich_jobs(self._deduplicate_jobs(jobs))

    def _parse_job_listings(self, soup: BeautifulSoup, location: str) -> list[JobData]:
        """Extract job listings from JSON-LD data."""
        return self._parse_job_listings_json(soup, location)

    def _parse_job_listings_json(
        self, soup: BeautifulSoup, location: str
    ) -> list[JobData]:
        """Extract job listings from JSON-LD data."""

        jobs = []
        scripts = soup.find_all(
            "script",
            type="application/ld+json",
        )

        for script in scripts:
            try:
                data = json.loads(script.get_text())

                if data.get("@type") != "ItemList":
                    continue
                job_cards = data.get("itemListElement", [])
                if job_cards:
                    for job_card in job_cards:
                        position = job_card.get("name")
                        url = job_card.get("url")
                        source = self.SOURCE_NAME

                        if not position or not url:
                            continue

                        jobs.append(
                            JobData(
                                title=position,
                                source=source,
                                location=location,
                                url=url,
                                apply_url=url,
                            )
                        )
            except (json.JSONDecodeError, TypeError, KeyError):
                continue
        return jobs

    def _enrich_jobs(self, jobs: list[JobData]) -> list[JobData]:
        enriched_jobs: list[JobData] = []

        for job in jobs:
            if not job.url:
                enriched_jobs.append(job)
                continue

            soup = self.fetch_page(job.url, {})
            if not soup:
                enriched_jobs.append(job)
                continue

            enriched_jobs.append(self._parse_job_details(soup, job))
        return enriched_jobs

    def _parse_job_details(self, soup: BeautifulSoup, job: JobData) -> JobData:
        scripts = soup.find_all("script", type="application/ld+json")

        # * attempt enrichment
        for script in scripts:
            try:
                data = json.loads(script.get_text())

                if data.get("@type") != "JobPosting":
                    continue

                cleaned_job_description = clean_job_description(data)

                if cleaned_job_description:
                    job.description = cleaned_job_description.description
                    job.minimum_experience = cleaned_job_description.experience
                    job.qualifications = cleaned_job_description.qualifications
                    job.tags = cleaned_job_description.tags
                    job.skills = cleaned_job_description.skills

                self._parse_company(data, job)
                self._parse_identifier(data, job)
                self._parse_job_type(data, job)
                self._parse_industry(data, job)
                self._parse_date(data, job)
                self._parse_tags(data, job)
            except json.JSONDecodeError:
                continue
        return job

    def _parse_description(self, data: dict, job: JobData) -> JobData:
        job.description = data.get("description", None)

    def _parse_date(self, data: dict, job: JobData) -> JobData:
        job.posted_date = self._parse_datetime(data.get("datePosted", None))
        job.application_deadline = self._parse_datetime(data.get("validThrough", None))

    def _parse_industry(self, data: dict, job: JobData) -> JobData:
        job.industry = data.get("industry", None)

    def _parse_job_type(self, data: dict, job: JobData) -> JobData:
        job.job_type = data.get("employmentType", None)

    def _parse_tags(self, data: dict, job: JobData) -> JobData:
        job.tags = data.get("skills", None)

    def _parse_identifier(self, data: dict, job: JobData) -> JobData:
        identifier = data.get("identifier")
        if identifier and isinstance(identifier, dict):
            value = identifier.get("value", None)
            if value is not None:
                job.external_id = str(value)

    # def _parse_experience(self, data: dict, job: JobData) -> JobData:
    #     experience_requirement = data.get("experienceRequirement", None)
    #     if experience_requirement and isinstance(experience_requirement, dict):
    #         experience_months = experience_requirement.get("monthsOfExperience", None)
    #         if experience_months is not None:
    #             job.minimum_experience = (f"{(experience_months / 12):g} years")

    def _parse_education(self, data: dict, job: JobData) -> JobData:
        education_requirements = data.get("educationRequirements", None)
        if education_requirements and isinstance(education_requirements, dict):
            education_requirements = education_requirements.get(
                "credentialCategory", None
            )
            if education_requirements is not None:
                job.requirements = education_requirements

    def _parse_company(self, data: dict, job: JobData) -> JobData:
        company_info = data.get("hiringOrganization", None)
        if company_info and isinstance(company_info, dict):
            job.company = company_info.get("name")
        elif company_info and isinstance(company_info, str):
            job.company = company_info

    def _parse_datetime(self, value: str | None) -> datetime.datetime | None:
        if not value:
            return

        try:
            return datetime.datetime.fromisoformat(value("Z", "+00:00"))
        except ValueError:
            return None

    def _deduplicate_jobs(self, jobs: list[JobData]):
        "Check if a job has been scraped already."
        seen = set()
        unique_jobs = []

        for job in jobs:
            identifier = job.external_id or job.url

            if not identifier:
                unique_jobs.append(job)
                continue

            if identifier in seen:
                continue

            seen.add(identifier)
            unique_jobs.append(job)

        return unique_jobs
