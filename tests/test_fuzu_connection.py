import requests


def test_fuzu_homepage():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    response = requests.get("https://www.fuzu.com", timeout=30, headers=headers)

    print("Status:", response.status_code)
    print("URL:", response.url)
    print("Content-Type:", response.headers.get("Content-Type"))

    assert response.status_code == 200


test_fuzu_homepage()
