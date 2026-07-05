import os
import json
from datetime import date
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_HEADERS = [
    "Job Title", "Company", "Location", "Category",
    "Experience", "Salary", "Description", "Posted",
    "Apply URL", "Source", "Scraped Date",
]


def get_client() -> gspread.Client:
    creds_json = os.environ["GOOGLE_CREDENTIALS"]
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def write_jobs(jobs: list[dict]) -> None:
    client = get_client()
    sheet_id = os.environ["SHEET_ID"]
    spreadsheet = client.open_by_key(sheet_id)

    try:
        worksheet = spreadsheet.worksheet("Jobs")
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title="Jobs", rows=5000, cols=len(SHEET_HEADERS))

    today = date.today().isoformat()

    # load existing rows to deduplicate by url and title+company
    existing = worksheet.get_all_values()
    if not existing or existing[0] != SHEET_HEADERS:
        worksheet.clear()
        worksheet.append_row(SHEET_HEADERS)
        existing_urls = set()
        existing_title_company = set()
    else:
        url_col = SHEET_HEADERS.index("Apply URL")
        title_col = SHEET_HEADERS.index("Job Title")
        company_col = SHEET_HEADERS.index("Company")
        existing_urls = set()
        existing_title_company = set()
        for row in existing[1:]:
            if len(row) > url_col:
                existing_urls.add(row[url_col])
            if len(row) > max(title_col, company_col):
                existing_title_company.add(
                    (row[title_col].strip().lower(), row[company_col].strip().lower())
                )

    new_rows = []
    for job in jobs:
        url = job.get("apply_url", "")
        tc = (job.get("title", "").strip().lower(), job.get("company", "").strip().lower())
        if url in existing_urls or tc in existing_title_company:
            continue
        # strip newlines from description to prevent CSV row corruption
        description = job.get("description", "").replace("\n", " ").replace("\r", " ").strip()
        new_rows.append([
            job.get("title", ""),
            job.get("company", ""),
            job.get("location", ""),
            job.get("category", ""),
            job.get("experience", ""),
            job.get("salary", ""),
            description,
            job.get("posted", ""),
            url,
            job.get("source", ""),
            today,
        ])
        existing_urls.add(url)
        existing_title_company.add(tc)

    if new_rows:
        worksheet.append_rows(new_rows, value_input_option="RAW")
        print(f"[Sheets] Added {len(new_rows)} new jobs")
    else:
        print("[Sheets] No new jobs to add")
