import sys
import internshala
import naukri
import sheets


def deduplicate(jobs: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for job in jobs:
        key = job["apply_url"]
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique


def main():
    print("Starting EPB Job Tracker scrape...")

    print("\n-- Internshala --")
    is_jobs = internshala.scrape()

    print("\n-- Naukri --")
    naukri_jobs = naukri.scrape()

    all_jobs = deduplicate(is_jobs + naukri_jobs)
    print(f"\nTotal unique jobs scraped: {len(all_jobs)}")

    print("\n-- Writing to Google Sheets --")
    sheets.write_jobs(all_jobs)

    print("\nDone.")


if __name__ == "__main__":
    main()
