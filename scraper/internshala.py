import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://internshala.com"
CITIES = ["bangalore"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_city(city: str) -> list[dict]:
    url = f"{BASE_URL}/fresher-jobs/fresher-jobs-in-{city}/"
    jobs = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[Internshala] Failed to fetch {city}: {e}")
        return jobs

    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select(".individual_internship")

    for card in cards:
        try:
            title_tag = card.select_one(".job-internship-name a.job-title-href")
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            apply_url = BASE_URL + title_tag["href"]

            company_tag = card.select_one(".company-name")
            company = company_tag.get_text(strip=True) if company_tag else ""

            location_tag = card.select_one(".locations span")
            location = location_tag.get_text(strip=True) if location_tag else city.capitalize()

            # salary: row-1-item containing the money icon
            salary = ""
            for item in card.select(".row-1-item"):
                if item.select_one(".ic-16-money"):
                    span = item.select_one(".desktop") or item.select_one("span")
                    salary = span.get_text(strip=True) if span else ""
                    break

            # experience
            experience = ""
            for item in card.select(".row-1-item"):
                if item.select_one(".ic-16-briefcase"):
                    span = item.select_one("span")
                    experience = span.get_text(strip=True) if span else ""
                    break

            desc_tag = card.select_one(".about_job .text")
            description = desc_tag.get_text(strip=True)[:500] if desc_tag else ""

            posted_tag = card.select_one(".color-labels .status-inactive span")
            posted = posted_tag.get_text(strip=True) if posted_tag else ""

            # infer category from title keywords
            category = infer_category(title)

            jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "category": category,
                "experience": experience or "Fresher",
                "salary": salary,
                "description": description,
                "posted": posted,
                "apply_url": apply_url,
                "source": "Internshala",
            })
        except Exception as e:
            print(f"[Internshala] Error parsing card: {e}")
            continue

    print(f"[Internshala] {city}: {len(jobs)} jobs found")
    return jobs


def scrape() -> list[dict]:
    all_jobs = []
    for city in CITIES:
        all_jobs.extend(scrape_city(city))
        time.sleep(2)
    return all_jobs


def infer_category(title: str) -> str:
    title_lower = title.lower()
    if any(k in title_lower for k in ["software", "developer", "engineer", "data", "python", "java", "frontend", "backend", "fullstack", "devops", "qa", "testing", "analyst", "cloud", "ml", "ai"]):
        return "IT / Tech"
    if any(k in title_lower for k in ["sales", "business development", "bd "]):
        return "Sales"
    if any(k in title_lower for k in ["marketing", "seo", "content", "social media", "digital"]):
        return "Marketing"
    if any(k in title_lower for k in ["finance", "accounting", "ca ", "tax", "audit"]):
        return "Finance"
    if any(k in title_lower for k in ["hr", "human resource", "recruiter", "talent"]):
        return "HR"
    if any(k in title_lower for k in ["design", "ui", "ux", "graphic", "creative"]):
        return "Design"
    if any(k in title_lower for k in ["customer", "support", "service", "helpdesk"]):
        return "Customer Service"
    if any(k in title_lower for k in ["operations", "admin", "office", "coordinator"]):
        return "Operations"
    return "Other"
