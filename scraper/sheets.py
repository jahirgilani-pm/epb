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

    # load existing rows to deduplicate by apply_url
    existing = worksheet.get_all_values()
    if not existing or existing[0] != SHEET_HEADERS:
        worksheet.clear()
        worksheet.append_row(SHEET_HEADERS)
        existing_urls = set()
    else:
        url_col = SHEET_HEADERS.index("Apply URL")
        existing_urls = {row[url_col] for row in existing[1:] if len(row) > url_col}

    new_rows = []
    for job in jobs:
        if job["apply_url"] in existing_urls:
            continue
        new_rows.append([
            job.get("title", ""),
            job.get("company", ""),
            job.get("location", ""),
            job.get("category", ""),
            job.get("experience", ""),
            job.get("salary", ""),
            job.get("description", ""),
            job.get("posted", ""),
            job.get("apply_url", ""),
            job.get("source", ""),
            today,
        ])
        existing_urls.add(job["apply_url"])

    if new_rows:
        worksheet.append_rows(new_rows, value_input_option="RAW")
        print(f"[Sheets] Added {len(new_rows)} new jobs")
    else:
        print("[Sheets] No new jobs to add")
