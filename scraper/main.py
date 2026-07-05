import internshala
import naukri
import indeed
import sheets


def job_key(job: dict) -> tuple:
    return (
        job["apply_url"],
        job["title"].strip().lower(),
        job["company"].strip().lower(),
    )


def deduplicate(jobs: list[dict]) -> list[dict]:
    seen_urls = set()
    seen_title_company = set()
    unique = []
    for job in jobs:
        url = job["apply_url"]
        tc = (job["title"].strip().lower(), job["company"].strip().lower())
        if url in seen_urls or tc in seen_title_company:
            continue
        seen_urls.add(url)
        seen_title_company.add(tc)
        unique.append(job)
    return unique


def main():
    print("Starting EPB Job Tracker scrape...")

    print("\n-- Internshala --")
    is_jobs = internshala.scrape()

    print("\n-- Indeed --")
    indeed_jobs = indeed.scrape()

    print("\n-- Naukri --")
    naukri_jobs = naukri.scrape()

    all_jobs = deduplicate(is_jobs + indeed_jobs + naukri_jobs)
    print(f"\nTotal unique jobs scraped: {len(all_jobs)}")

    print("\n-- Writing to Google Sheets --")
    sheets.write_jobs(all_jobs)

    print("\nDone.")


if __name__ == "__main__":
    main()
