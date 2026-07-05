import requests
from bs4 import BeautifulSoup
import time

CITIES = {
    "bangalore": "bengaluru",
    "hyderabad": "hyderabad",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def scrape_city(city_key: str) -> list[dict]:
    url = f"https://www.naukri.com/fresher-jobs-in-{city_key}"
    jobs = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[Naukri] Failed to fetch {city_key}: {e}")
        return jobs

    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select(".srp-jobtuple-wrapper .cust-job-tuple")

    for card in cards:
        try:
            title_tag = card.select_one("h2 a.title")
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            apply_url = title_tag["href"]

            company_tag = card.select_one("a.comp-name")
            company = company_tag.get_text(strip=True) if company_tag else ""

            exp_tag = card.select_one(".expwdth")
            experience = exp_tag.get_text(strip=True) if exp_tag else "Fresher"

            sal_tag = card.select_one(".sal span[title]")
            salary = sal_tag["title"].strip() if sal_tag else ""

            loc_tag = card.select_one(".locWdth")
            location_raw = loc_tag.get_text(strip=True) if loc_tag else city_key.capitalize()
            # normalize to just BLR/HYD label if it contains target city
            location = normalize_location(location_raw, city_key)

            desc_tag = card.select_one(".job-desc")
            description = desc_tag.get_text(strip=True)[:500] if desc_tag else ""

            skills = [li.get_text(strip=True) for li in card.select(".tag-li")]

            posted_tag = card.select_one(".job-post-day")
            posted = posted_tag.get_text(strip=True) if posted_tag else ""

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
            print(f"[Naukri] Error parsing card: {e}")
            continue

    print(f"[Naukri] {city_key}: {len(jobs)} jobs found")
    return jobs


def scrape() -> list[dict]:
    all_jobs = []
    for city_key in CITIES:
        all_jobs.extend(scrape_city(city_key))
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
