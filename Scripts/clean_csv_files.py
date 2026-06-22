"""
clean_csv_files.py
------------------
Cleans all CSV files in the input folder, handling all 11 structural
patterns. Cleaned files are saved to the output folder.
Originals are never modified.

Usage:
    # Original imported files
    python clean_csv_files.py

    # Overlap files (or any other folder)
    python clean_csv_files.py --input overlap_raw_data --output overlap_cleaned_data

Requirements:
    pip install pandas
"""

import os
import argparse
import pandas as pd


def detect_and_clean(filepath: str):
    """
    Detect which CSV pattern this file matches and clean it.
    Returns (DataFrame, None) on success, or (None, error_message) on failure.

    Pattern summary
    ───────────────
    Patterns 5,6,7  — first row is 'Name, Opening_Price, Closing_Price, Volume_Traded'
      Pattern 6     — clean except for column names                        (1 file)
      Pattern 7     — has a stray 'EQUITIES' row under the header          (1 file)
      Pattern 5     — company names missing (numbers only) — UNFIXABLE     (3 files)

    Patterns with junk header row (['','0','1',...]):
      5 cols — Pattern 4:    idx | Company | Open | Close | Volume
      6 cols — Patterns 2,3: idx | counter | Company | Open | Close | Volume
      9 cols — Patterns 1,8,9,10,11: idx | Company(x2-3) | blanks | Open | Close | Volume
    """
    df_raw    = pd.read_csv(filepath, header=None, dtype=str)
    ncols     = df_raw.shape[1]
    first_row = df_raw.iloc[0].tolist()

    # ── Patterns 5, 6, 7 — real 'Name' header row ────────────────────────────
    if str(first_row[0]).strip() == 'Name':
        df = df_raw.copy()
        df.columns = df.iloc[0].str.strip()
        df = df.iloc[1:].copy()

        # Drop EQUITIES label rows and blank Name rows
        df = df[
            df['Name'].notna() &
            (df['Name'].str.strip() != '') &
            (df['Name'].str.strip() != 'EQUITIES')
        ]

        # Pattern 5 check: Name column contains numbers not company names
        sample = df['Name'].dropna().head(5).tolist()
        all_numeric = all(
            s.strip().replace('.', '', 1).lstrip('-').isdigit()
            for s in sample if s.strip()
        )
        if all_numeric:
            return None, (
                "Company names are missing — Name column contains only index numbers. "
                "This file cannot be cleaned automatically."
            )

        df = df[['Name', 'Opening_Price', 'Closing_Price', 'Volume_Traded']].copy()
        df.columns = ['Company Name', 'Opening Price', 'Closing Price', 'Volume']
        for col in ['Opening Price', 'Closing Price', 'Volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df.reset_index(drop=True), None

    # ── Patterns 1, 2, 3, 4, 8–11 — junk header row ──────────────────────────
    # Drop the junk first row (['', '0', '1', ...])
    df = df_raw.iloc[1:].copy()

    if ncols == 5:
        # Pattern 4: idx | Company Name | Open | Close | Volume
        df.columns = ['_idx', 'Company Name', 'Opening Price', 'Closing Price', 'Volume']

    elif ncols == 6:
        # Patterns 2 & 3: idx | counter | Company Name | Open | Close | Volume
        df.columns = ['_idx', '_ctr', 'Company Name', 'Opening Price', 'Closing Price', 'Volume']

    elif ncols == 9:
        # Patterns 1, 8, 9, 10, 11: idx | Company(repeated) | blanks | Open | Close | Volume
        df.columns = ['_idx', 'Company Name', '_c2', '_c3', '_c4', '_c5',
                      'Opening Price', 'Closing Price', 'Volume']

    else:
        return None, f"Unrecognised structure: {ncols} columns — manual inspection needed."

    # Keep only rows where Opening Price is a valid number
    # (drops blank rows, EQUITIES label rows, and end-of-file total rows)
    df = df[pd.to_numeric(df['Opening Price'], errors='coerce').notna()].copy()
    df = df[['Company Name', 'Opening Price', 'Closing Price', 'Volume']].copy()

    for col in ['Opening Price', 'Closing Price', 'Volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Safety check: Company Name column should not be all-numeric
    sample = df['Company Name'].dropna().head(5).tolist()
    all_numeric = all(
        str(s).strip().replace('.', '', 1).lstrip('-').isdigit()
        for s in sample if str(s).strip()
    )
    if all_numeric:
        return None, "Company Name column appears to be numeric — manual inspection needed."

    return df.reset_index(drop=True), None


def main():
    parser = argparse.ArgumentParser(description="Clean messy ZSE CSV files.")
    parser.add_argument(
        "--input", "-i",
        default="imported_raw_data",
        help="Folder containing raw CSV files (default: imported_raw_data)"
    )
    parser.add_argument(
        "--output", "-o",
        default="imported_cleaned_data",
        help="Folder to save cleaned CSV files (default: imported_cleaned_data)"
    )
    args = parser.parse_args()

    input_folder  = args.input
    output_folder = args.output

    os.makedirs(output_folder, exist_ok=True)

    csv_files = sorted(f for f in os.listdir(input_folder) if f.lower().endswith('.csv'))
    if not csv_files:
        print(f"No CSV files found in '{input_folder}'.")
        return

    print(f"Input  : {input_folder}/")
    print(f"Output : {output_folder}/")
    print(f"Found  : {len(csv_files)} CSV file(s)\n")

    ok, skipped, failed = 0, [], []

    for filename in csv_files:
        input_path  = os.path.join(input_folder,  filename)
        output_path = os.path.join(output_folder, filename)

        try:
            df, error = detect_and_clean(input_path)
            if error:
                print(f"  ⚠  {filename}  —  SKIPPED: {error}")
                skipped.append((filename, error))
            else:
                df.to_csv(output_path, index=False)
                print(f"  ✓  {filename}  →  {len(df)} rows")
                ok += 1
        except Exception as e:
            print(f"  ✗  {filename}  —  ERROR: {e}")
            failed.append((filename, str(e)))

    print(f"\n{'─'*60}")
    print(f"  Cleaned : {ok} file(s)  →  '{output_folder}/'")
    if skipped:
        print(f"  Skipped : {len(skipped)} file(s) (see warnings above)")
    if failed:
        print(f"  Errors  : {len(failed)} file(s) (see errors above)")
    print(f"{'─'*60}")


if __name__ == "__main__":
    main()
