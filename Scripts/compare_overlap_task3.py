import json
import csv
from pathlib import Path

ORIGINAL_DIR = Path("archive-single-file-original")
NORMALIZED_DIR = Path("archive-single-file")

FILES = [
    "open_price.json",
    "close_price.json",
    "vol_traded.json"
]

OUTPUT_FILE = "overlap_mismatch_report.csv"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


total_matches = 0
total_mismatches = 0
total_overlap_records = 0
total_missing_dates = 0
total_missing_companies = 0

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:

    writer = csv.writer(csvfile)

    writer.writerow([
        "file",
        "date",
        "company",
        "original_value",
        "normalized_value",
        "difference_type"
    ])

    for filename in FILES:

        print(f"\nComparing {filename}")

        original = load_json(ORIGINAL_DIR / filename)
        normalized = load_json(NORMALIZED_DIR / filename)

        overlap_dates = set(original.keys()) & set(normalized.keys())

        for date in overlap_dates:

            original_companies = original[date]
            normalized_companies = normalized[date]

            overlap_companies = (
                set(original_companies.keys())
                & set(normalized_companies.keys())
            )

            for company in overlap_companies:

                total_overlap_records += 1

                original_value = original_companies[company]
                normalized_value = normalized_companies[company]

                if original_value == normalized_value:
                    total_matches += 1
                else:
                    total_mismatches += 1

                    writer.writerow([
                        filename,
                        date,
                        company,
                        original_value,
                        normalized_value,
                        "value_mismatch"
                    ])

            missing_from_normalized = (
                set(original_companies.keys())
                - set(normalized_companies.keys())
            )

            for company in missing_from_normalized:

                total_missing_companies += 1

                writer.writerow([
                    filename,
                    date,
                    company,
                    original_companies[company],
                    "",
                    "missing_from_normalized"
                ])

            missing_from_original = (
                set(normalized_companies.keys())
                - set(original_companies.keys())
            )

            for company in missing_from_original:

                total_missing_companies += 1

                writer.writerow([
                    filename,
                    date,
                    company,
                    "",
                    normalized_companies[company],
                    "missing_from_original"
                ])

        missing_dates_original = (
            set(original.keys()) - set(normalized.keys())
        )

        missing_dates_normalized = (
            set(normalized.keys()) - set(original.keys())
        )

        total_missing_dates += (
            len(missing_dates_original)
            + len(missing_dates_normalized)
        )

print("\n" + "=" * 60)
print("TASK 3 OVERLAP SUMMARY")
print("=" * 60)

print(f"Overlap records: {total_overlap_records:,}")
print(f"Exact matches:   {total_matches:,}")
print(f"Mismatches:      {total_mismatches:,}")
print(f"Missing dates:   {total_missing_dates:,}")
print(f"Missing companies: {total_missing_companies:,}")

print(f"\nSaved report: {OUTPUT_FILE}")