"""
clean_xlsx_files.py
-------------------
Cleans all XLSX files in the input folder, handling all 5 structural
patterns. Saves cleaned files to the output folder as XLSX.
Originals are never modified.

Usage:
    # Original imported files
    python clean_xlsx_files.py

    # Overlap files (or any other folder)
    python clean_xlsx_files.py --input overlap_raw_data --output overlap_cleaned_data

Requirements:
    pip install pandas openpyxl

What is fixed per pattern
─────────────────────────
Pattern 1 (10 files): drop numeric index row + EQUITIES row + blank row;
                       rename 'Total Traded Volume' → 'Volume';
                       replace '-' in Volume with 0
Pattern 2 (14 files): drop numeric index row + blank rows between data rows;
                       header already correct
Pattern 3 (44 files): drop numeric index row + EQUITIES row + 2 blank rows;
                       rename 'Total Traded Volume' → 'Volume'
Pattern 4  (1 file):  drop junk rows; Opening Price column missing —
                       added as blank and flagged in summary
Pattern 5  (3 files): drop numeric index row + EQUITIES row;
                       rename 'Total Traded Volume' → 'Volume'

All patterns produce: Company Name | Opening Price | Closing Price | Volume
"""

import os
import argparse
import pandas as pd

# Accepted variants for each target column name
COL_ALIASES = {
    "Company Name"  : {"Company Name", "Name"},
    "Opening Price" : {"Opening Price", "Opening_Price"},
    "Closing Price" : {"Closing Price", "Closing_Price"},
    "Volume"        : {"Volume", "Total Traded Volume", "Volume_Traded"},
}

TARGET_COLS = ["Company Name", "Opening Price", "Closing Price", "Volume"]


def normalise_header(raw_header: list) -> dict:
    """Map raw column positions to standardised target column names."""
    mapping = {}
    for i, col in enumerate(raw_header):
        c = str(col).strip()
        for target, aliases in COL_ALIASES.items():
            if c in aliases:
                mapping[i] = target
                break
        else:
            mapping[i] = c  # keep unknown columns as-is
    return mapping


def clean_xlsx(filepath: str):
    """
    Read and clean one XLSX file.
    Returns (DataFrame, warning_str_or_None).
    """
    df = pd.read_excel(filepath, header=None, dtype=str)

    # ── 1. Find the real header row ──────────────────────────────────────────
    header_idx = None
    for i, row in df.iterrows():
        vals = [str(v).strip().lower() for v in row]
        if any("company" in v or ("name" in v and "nan" not in v) for v in vals):
            header_idx = i
            break

    if header_idx is None:
        return None, "Could not locate a header row — skipped"

    # ── 2. Slice out header and everything below it ──────────────────────────
    raw_header = [str(v).strip() for v in df.loc[header_idx].tolist()]
    data = df.loc[header_idx + 1:].copy()

    # ── 3. Drop blank rows ───────────────────────────────────────────────────
    data = data[
        data.apply(lambda r: any(str(v).strip() not in ("", "nan") for v in r), axis=1)
    ]

    # ── 4. Drop label rows (EQUITIES etc.) ───────────────────────────────────
    data = data[~data.iloc[:, 0].astype(str).str.strip().str.upper().eq("EQUITIES")]

    # ── 5. Rename columns ────────────────────────────────────────────────────
    col_map = normalise_header(raw_header)
    data.columns = range(len(data.columns))
    data = data.rename(columns=col_map)

    # ── 6. Handle missing Opening Price column (Pattern 4) ───────────────────
    warning = None
    if "Opening Price" not in data.columns:
        data.insert(1, "Opening Price", float("nan"))
        warning = (
            "Opening Price column was missing in the source file. "
            "The column has been added but left blank — please fill it manually."
        )

    # ── 7. Ensure all 4 target columns exist ─────────────────────────────────
    for col in TARGET_COLS:
        if col not in data.columns:
            data[col] = float("nan")

    data = data[TARGET_COLS].copy()

    # ── 8. Replace '-' placeholders with 0 in numeric columns ────────────────
    for col in ["Opening Price", "Closing Price", "Volume"]:
        data[col] = data[col].apply(
            lambda v: "0" if str(v).strip() == "-" else v
        )
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.reset_index(drop=True)
    return data, warning


def main():
    parser = argparse.ArgumentParser(description="Clean messy ZSE XLSX files.")
    parser.add_argument(
        "--input", "-i",
        default="imported_raw_data",
        help="Folder containing raw XLSX files (default: imported_raw_data)"
    )
    parser.add_argument(
        "--output", "-o",
        default="imported_cleaned_data",
        help="Folder to save cleaned XLSX files (default: imported_cleaned_data)"
    )
    args = parser.parse_args()

    input_folder  = args.input
    output_folder = args.output

    os.makedirs(output_folder, exist_ok=True)

    xlsx_files = sorted(
        f for f in os.listdir(input_folder) if f.lower().endswith(".xlsx")
    )
    if not xlsx_files:
        print(f"No XLSX files found in '{input_folder}'.")
        return

    print(f"Input  : {input_folder}/")
    print(f"Output : {output_folder}/")
    print(f"Found  : {len(xlsx_files)} XLSX file(s)\n")

    ok, skipped, failed = 0, [], []

    for filename in xlsx_files:
        input_path  = os.path.join(input_folder,  filename)
        output_path = os.path.join(output_folder, filename)

        try:
            df, warning = clean_xlsx(input_path)

            if df is None:
                print(f"  ⚠  {filename}  —  SKIPPED: {warning}")
                skipped.append((filename, warning))
                continue

            df.to_excel(output_path, index=False, engine="openpyxl")

            status = f"  ✓  {filename}  →  {len(df)} rows"
            if warning:
                status += f"\n      ⚠  {warning}"
            print(status)
            ok += 1

        except Exception as e:
            print(f"  ✗  {filename}  —  ERROR: {e}")
            failed.append((filename, str(e)))

    print(f"\n{'─'*60}")
    print(f"  Cleaned : {ok} file(s)  →  '{output_folder}/'")
    if skipped:
        print(f"  Skipped : {len(skipped)} file(s)")
        for f, reason in skipped:
            print(f"    • {f}: {reason}")
    if failed:
        print(f"  Errors  : {len(failed)} file(s)")
        for f, err in failed:
            print(f"    • {f}: {err}")
    print(f"{'─'*60}")


if __name__ == "__main__":
    main()
