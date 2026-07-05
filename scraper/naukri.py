import time
import requests
from playwright.sync_api import sync_playwright

CITIES = {
    "bangalore": "fresher-jobs-in-bangalore",
}

API_URL = "https://www.naukri.com/jobapi/v3/search"
BASE_HEADERS = {
    "appid": "109",
    "systemid": "Naukri",
    "clientid": "d3skt0p",
    "accept": "application/json",
    "content-type": "application/json",
    "gid": "LOCATION,INDUSTRY,EDUCATION,FAREA_ROLE",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/149.0.0.0 Safari/537.36"
    ),
}


def get_nkparam() -> str:
    """Load Naukri in a real browser and intercept the API call to capture nkparam."""
    nkparam = None

    def handle_request(request):
        nonlocal nkparam
        if "jobapi/v3/search" in request.url and nkparam is None:
            nkparam = request.headers.get("nkparam", "")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/149.0.0.0 Safari/537.36"
            )
        )
        page.on("request", handle_request)
        try:
            page.goto(
                "https://www.naukri.com/fresher-jobs-in-bangalore",
                wait_until="domcontentloaded",
                timeout=30000,
            )
            # wait for API call to fire
            for _ in range(20):
                if nkparam:
                    break
                time.sleep(0.5)
        except Exception as e:
            print(f"[Naukri] Browser error: {e}")
        finally:
            browser.close()

    if not nkparam:
        print("[Naukri] Warning: could not capture nkparam")
    return nkparam or ""


def fetch_city(city_key: str, nkparam: str) -> list[dict]:
    seo_key = CITIES[city_key]
    params = {
        "noOfResults": 30,
        "urlType": "search_by_key_loc",
        "searchType": "adv",
        "location": city_key,
        "keyword": "fresher",
        "pageNo": 1,
        "seoKey": seo_key,
        "src": "directSearch",
        "latLong": "",
    }
    headers = {
        **BASE_HEADERS,
        "nkparam": nkparam,
        "referer": f"https://www.naukri.com/{seo_key}",
    }

    try:
        resp = requests.get(API_URL, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        raw_jobs = resp.json().get("jobDetails", [])
    except Exception as e:
        print(f"[Naukri] API error for {city_key}: {e}")
        return []

    jobs = []
    for j in raw_jobs:
        try:
            title = j.get("title", "")
            company = j.get("companyName", "")
            apply_url = "https://www.naukri.com" + j.get("jdURL", "")

            placeholders = {p["type"]: p["label"] for p in j.get("placeholders", [])}
            experience = placeholders.get("experience", "Fresher")
            salary = placeholders.get("salary", "")
            location_raw = placeholders.get("location", city_key.capitalize())
            location = normalize_location(location_raw, city_key)

            skills_raw = j.get("tagsAndSkills", "")
            skills = [s.strip() for s in skills_raw.split(",") if s.strip()]

            description = j.get("jobDescription", "")[:500]
            posted = j.get("footerPlaceholderLabel", "")
            category = infer_category(title, skills)

            jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "category": category,
                "experience": experience,
                "salary": salary,
                "description": description,
                "posted": posted,
                "apply_url": apply_url,
                "source": "Naukri",
            })
        except Exception as e:
            print(f"[Naukri] Error parsing job: {e}")
            continue

    print(f"[Naukri] {city_key}: {len(jobs)} jobs found")
    return jobs


def scrape() -> list[dict]:
    print("[Naukri] Capturing session token...")
    nkparam = get_nkparam()

    all_jobs = []
    for city_key in CITIES:
        all_jobs.extend(fetch_city(city_key, nkparam))
        time.sleep(2)
    return all_jobs


def normalize_location(raw: str, city_key: str) -> str:
    raw_lower = raw.lower()
    parts = []
    if "bengaluru" in raw_lower or "bangalore" in raw_lower:
        parts.append("Bengaluru")
    if "hyderabad" in raw_lower:
        parts.append("Hyderabad")
    return ", ".join(parts) if parts else raw[:50]


def infer_category(title: str, skills: list[str]) -> str:
    combined = (title + " " + " ".join(skills)).lower()
    if any(k in combined for k in ["software", "developer", "engineer", "data", "python", "java", "frontend", "backend", "fullstack", "devops", "qa", "testing", "analyst", "cloud", "ml", "ai", "unity", "android", "ios"]):
        return "IT / Tech"
    if any(k in combined for k in ["sales", "business development", "bd "]):
        return "Sales"
    if any(k in combined for k in ["marketing", "seo", "content", "social media", "digital"]):
        return "Marketing"
    if any(k in combined for k in ["finance", "accounting", "ca ", "tax", "audit"]):
        return "Finance"
    if any(k in combined for k in ["hr", "human resource", "recruiter", "talent"]):
        return "HR"
    if any(k in combined for k in ["design", "ui", "ux", "graphic", "creative"]):
        return "Design"
    if any(k in combined for k in ["customer", "support", "service", "helpdesk", "voice process"]):
        return "Customer Service"
    if any(k in combined for k in ["operations", "admin", "office", "coordinator"]):
        return "Operations"
    return "Other"
