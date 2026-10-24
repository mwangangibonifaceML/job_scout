from __future__ import annotations

from bs4 import BeautifulSoup

from job_scout.scrapers.base import BaseScraper
from job_scout.scrapers.fuzu_scraper import FuzuScraper


def test_fuzu_is_an_instance_of_base_scraper():
    scraper = FuzuScraper()
    
    assert isinstance(scraper, BaseScraper), """
    Expected the scraper to be an instance of base scraper."""
    

def test_the_scraper_scrapes_one_job():
    html = """
    <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "ItemList",
                "itemListElement": [
                    {
                        "name": "Python Developer",
                        "url": "https://www.fuzu.com/job/123"
                    }
                ]
            }
            </script>
        </head>
    </html>
    """
    scraper = FuzuScraper()
    soup = BeautifulSoup(html, "lxml")
    jobs = scraper._parse_job_listings_json(soup, location="Kenya")
    jobs = [job.__dict__ for job in jobs]
    
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Python Developer"
    assert jobs[0]["location"] == 'Kenya'
    assert jobs[0]["url"] == "https://www.fuzu.com/job/123"
    assert jobs[0]["apply_url"] == "https://www.fuzu.com/job/123"
    assert jobs[0]["source"] == 'Fuzu'
    

def test_the_scraper_scrapes_multiple_job():
    html = """
    <html> 
        <head>
            <script type="application/ld+json"> 
            {
                "@type": "ItemList",
                "itemListElement" : [
                    {
                        "name": "Python Developer",
                        "url": "http://www.fuzu.com/job/122"
                    },
                    {
                        "name": "Machine Learning Engineer",
                        "url": "http://www.fuzu.com/job/123"
                    },
                    {
                        "name": "AI Engineer",
                        "url": "http://www.fuzu.com/job/124"
                    }
                ]
            }
            
            </script>
        </head>
    </html>
    
    """
    scraper = FuzuScraper()
    soup = BeautifulSoup(html, "lxml")
    jobs = scraper._parse_job_listings_json(soup, location="Kenya")
    jobs = [job.__dict__ for job in jobs]
    
    assert len(jobs) == 3
    assert jobs[0]["title"] == "Python Developer"
    assert jobs[1]["title"] == "Machine Learning Engineer"
    assert jobs[2]["title"] == "AI Engineer"
    
    
def test_unrelated_json_are_ignored():
    html = """
        <html> 
            <head>
                <script type="application/ld+json">
                {
                    "@type": "WeSite",
                    "name": "Fuzu,
                    "itemListElement": [
                        {
                            "name": "Finance Officer",
                            "url": "https://www.fuzu.com/job/123"
                        },
                        {
                            "name": "Python Developer",
                            "url": "https://www.fuzu.com/job/124"
                        }
                    ]
                }
                </script>
                
                <script type="application/ld+json"> 
                {
                    "@type": "ItemList",
                    "itemListElement" : [
                        {
                            "name": "Python Developer",
                            "url": "http://www.fuzu.com/job/122"
                        },
                        {
                            "name": "Machine Learning Engineer",
                            "url": "http://www.fuzu.com/job/123"
                        },
                        {
                            "name": "AI Engineer",
                            "url": "http://www.fuzu.com/job/124"
                        }
                    ]
                }
                
                </script>
            </head>
        </html>
        
        """
    scraper = FuzuScraper()
    soup = BeautifulSoup(html, "lxml")
    jobs = scraper._parse_job_listings_json(soup, location="Kenya")
    jobs = [job.__dict__ for job in jobs]
    
    
    assert len(jobs) == 3
    assert jobs[0]["title"] == "Python Developer"
    assert jobs[1]["title"] == "Machine Learning Engineer"
    assert jobs[2]["title"] == "AI Engineer"
    
def test_parse_job_listings_json_ignores_invalid_json():
    html = """
    <script type="application/ld+json">
    {
        this is not valid JSON
    }
    </script>

    <script type="application/ld+json">
    {
        "@type": "ItemList",
        "itemListElement": [
            {
                "name": "Finance Officer",
                "url": "https://www.fuzu.com/job/123"
            }
        ]
    }
    </script>
    """

    soup = BeautifulSoup(html, "lxml")

    scraper = FuzuScraper()

    jobs = scraper._parse_job_listings_json(
        soup=soup,
        location="kenya",
    )

    assert len(jobs) == 1
    assert jobs[0].title == "Finance Officer"
    
    
def test_scrape_skips_jobs_without_url():
    html = """
        <html> 
            <head>
                <script type="application/ld+json"> 
                {
                    "@type": "ItemList",
                    "itemListElement" : [
                        {
                            "name": "Python Developer",
                            "url": "http://www.fuzu.com/job/122"
                        },
                        {
                            "name": "Machine Learning Engineer"
                        },
                        {
                            "name": "Data Scientist"
                        },
                        {
                            "name": "AI Engineer",
                            "url": "http://www.fuzu.com/job/124"
                        }
                    ]
                }
                
            </script>
        </head>
    </html>
    
    """
    scraper = FuzuScraper()
    soup = BeautifulSoup(html, "lxml")
    jobs = scraper._parse_job_listings_json(soup, location="Kenya")
    jobs = [job.__dict__ for job in jobs]
    
    assert len(jobs) == 2
    assert jobs[0]["title"] == "Python Developer"
    assert jobs[1]["title"] == "AI Engineer"
    
    
def test_location_ids():
    scraper = FuzuScraper()
    
    assert scraper.COUNTRY_IDS["kenya"] == 1
    assert scraper.COUNTRY_IDS["nigeria"] == 165
    assert scraper.COUNTRY_IDS["uganda"] == 232
    
    
# def test_invalid_location():
#     scraper = FuzuScraper()
    
#     with pytest.raises(TypeError, match="Unsupported location: Tanzania. Please choose from these locations: kenya,nigeria,uganda"):
#         scraper.scrape(location="Tanzania")
        

def test_scraper_collects_jobs_using_fake_fetch_page():
    html = """
            <html> 
                <head>
                    <script type="application/ld+json"> 
                    {
                        "@type": "ItemList",
                        "itemListElement" : [
                            {
                                "name": "Python Developer",
                                "url": "https://www.fuzu.com/job"
                            },
                            {
                                "name": "AI Engineer",
                                "url": "https://www.fuzu.com/job"
                            }
                        ]
                    }
                    
            </script>
        </head>
    </html>
    
    """
    soup = BeautifulSoup(html, "lxml")
    scraper = FuzuScraper()
    
    def fake_fetch_page(url, parameters=None):
        assert url == "https://www.fuzu.com/job"
        # assert parameters["filters[country_id]"] == 1
        
        return soup
    
    scraper.fetch_page = fake_fetch_page
    jobs = scraper.scrape(location="Kenya", number_of_pages=2)
    jobs = [job.__dict__ for job in jobs]
    
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Python Developer"
    # assert jobs[1]["title"] == "AI Engineer"
    

# def test_scrape_requests_each_page():
#     scraper = FuzuScraper()

#     requested_pages = []

#     html = """
#     <script type="application/ld+json">
#     {
#         "@type": "ItemList",
#         "itemListElement": [
#             {
#                 "name": "Finance Officer",
#                 "url": "https://www.fuzu.com/job/123"
#             }
#         ]
#     }
#     </script>
#     """

#     soup = BeautifulSoup(html, "lxml")

#     def fake_fetch_page(url, parameters=None):
#         requested_pages.append(parameters["page"])
#         return soup

#     scraper.fetch_page = fake_fetch_page

#     jobs = scraper.scrape(
#         location="kenya",
#         number_of_pages=3,
#     )

#     assert requested_pages == [1, 2, 3]
#     assert len(jobs) == 3
    

# def test_scraper_continues_when_page_fetch_fails():
#     scraper = FuzuScraper()
    
#     html = """
#     <script type="application/ld+json">
#     {
#         "@type": "ItemList",
#         "itemListElement": [
#             {
#                 "name": "Finance Officer",
#                 "url": "https://www.fuzu.com/job/123"
#             }
#         ]
#     }
#     </script>
#     """

#     soup = BeautifulSoup(html, "lxml")

#     def fake_fetch_page(url, parameters=None):
#         if parameters["page"] == 1:
#             return None
        
#         return soup

#     scraper.fetch_page = fake_fetch_page

#     jobs = scraper.scrape(
#         location="kenya",
#         number_of_pages=3,
#     )
#     jobs = [job.__dict__ for job in jobs]
    
#     assert jobs[0]["title"] == "Finance Officer"
#     assert len(jobs) == 2
    