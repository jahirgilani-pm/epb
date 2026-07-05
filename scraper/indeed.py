import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URL = "https://in.indeed.com"
SEARCH_URL = f"{BASE_URL}/jobs"
MAX_PAGES = 3
RESULTS_PER_PAGE = 15


def scrape() -> list[dict]:
    jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = context.new_page()

        # load page 1 first to establish session, then navigate via Next button
        try:
            page.goto(
                f"{SEARCH_URL}?q=fresher&l=Bangalore&explvl=entry_level",
                wait_until="domcontentloaded",
                timeout=30000,
            )
            page.wait_for_selector(".job_seen_beacon", timeout=15000)
        except Exception as e:
            print(f"[Indeed] Failed to load page 1: {e}")
            browser.close()
            return jobs

        for p_num in range(MAX_PAGES):
            # scroll to trigger lazy-loaded cards
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            soup = BeautifulSoup(page.content(), "html.parser")
            cards = soup.select(".job_seen_beacon")

            if not cards:
                break

            for card in cards:
                try:
                    title_tag = card.select_one("h3 a span[title]")
                    if not title_tag:
                        continue
                    title = title_tag["title"].strip()

                    jk = card.select_one("a[data-jk]")
                    if not jk:
                        continue
                    apply_url = f"{BASE_URL}/viewjob?jk={jk['data-jk']}"

                    company_tag = card.select_one("[data-testid='company-name']")
                    company = company_tag.get_text(strip=True) if company_tag else ""

                    loc_tag = card.select_one("[data-testid='text-location']")
                    location = loc_tag.get_text(strip=True) if loc_tag else "Bengaluru"

                    salary_tag = card.select_one(".salary-snippet-container")
                    salary = salary_tag.get_text(strip=True) if salary_tag else ""

                    desc_tag = card.select_one(".underShelfFooter, [class*='snippet']")
                    description = desc_tag.get_text(strip=True)[:500] if desc_tag else ""

                    category = infer_category(title)

                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": "Bengaluru",
                        "category": category,
                        "experience": "Fresher",
                        "salary": salary,
                        "description": description,
                        "posted": "",
                        "apply_url": apply_url,
                        "source": "Indeed",
                    })
                except Exception as e:
                    print(f"[Indeed] Error parsing card: {e}")
                    continue

            print(f"[Indeed] Page {p_num + 1}: {len(cards)} cards found")

            # click Next to go to the next page
            if p_num < MAX_PAGES - 1:
                try:
                    next_btn = page.query_selector('a[aria-label="Next Page"]')
                    if not next_btn:
                        break
                    next_btn.click()
                    page.wait_for_selector(".job_seen_beacon", timeout=15000)
                    time.sleep(2)
                except Exception:
                    break

        browser.close()

    print(f"[Indeed] Total: {len(jobs)} jobs found")
    return jobs


def infer_category(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ["software", "developer", "engineer", "data", "python", "java", "frontend", "backend", "fullstack", "devops", "qa", "testing", "analyst", "cloud", "ml", "ai", "android", "ios"]):
        return "IT / Tech"
    if any(k in t for k in ["sales", "business development", "bd "]):
        return "Sales"
    if any(k in t for k in ["marketing", "seo", "content", "social media", "digital"]):
        return "Marketing"
    if any(k in t for k in ["finance", "accounting", "ca ", "tax", "audit"]):
        return "Finance"
    if any(k in t for k in ["hr", "human resource", "recruiter", "talent"]):
        return "HR"
    if any(k in t for k in ["design", "ui", "ux", "graphic", "creative"]):
        return "Design"
    if any(k in t for k in ["customer", "support", "service", "helpdesk", "voice"]):
        return "Customer Service"
    if any(k in t for k in ["operations", "admin", "office", "coordinator"]):
        return "Operations"
    return "Other"
