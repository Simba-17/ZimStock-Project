import os
import pandas as pd
from pathlib import Path

# ==========================================
# 1. CONFIGURATION (CHECK THESE NAMES!)
# ==========================================
# Look at one of your raw CSVs. Make sure these match the column headers EXACTLY.
DATE_COLUMN = 'Date'
COMPANY_COLUMN = 'Security'  # Might be 'Ticker', 'Company', or 'Symbol' depending on your data
OPEN_COLUMN = 'Open'
CLOSE_COLUMN = 'Close'
VOLUME_COLUMN = 'Volume'

# The format you want the final dates to be in. 
# '%Y-%m-%d' creates the standard format: 2023-05-14
TARGET_DATE_FORMAT = '%Y-%m-%d'

# ==========================================
# 2. SETUP PATHS
# ==========================================
# This automatically finds your Desktop and points to your project folder
desktop_path = Path.home() / "Desktop"
project_folder = desktop_path / "zimstock project" # Ensure this exactly matches your folder name
imported_data_folder = project_folder / "imported data"
archive_folder = project_folder / "archive-single-file"

# Create the archive folder if it doesn't exist
archive_folder.mkdir(parents=True, exist_ok=True)

# Lists to hold the extracted data from all 372 files
all_open_prices = []
all_close_prices = []
all_volumes = []

# ==========================================
# 3. PROCESS THE FILES & CONVERT DATES
# ==========================================
print(f"Reading files from: {imported_data_folder}...")

for file_path in imported_data_folder.iterdir():
    # Only process spreadsheet files
    if file_path.suffix in ['.csv', '.xlsx', '.xls']:
        
        # Read the file based on whether it is CSV or Excel
        try:
            if file_path.suffix == '.csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
        except Exception as e:
            print(f"Skipping {file_path.name} - Could not read file: {e}")
            continue
            
        # --- THE DATE CONVERSION ---
        if DATE_COLUMN in df.columns:
            # dayfirst=True tells Python to expect Day-Month-Year format!
            df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], dayfirst=True, errors='coerce')
            
            # Format it to match the destination files
            df[DATE_COLUMN] = df[DATE_COLUMN].dt.strftime(TARGET_DATE_FORMAT)
        else:
            print(f"Warning: No '{DATE_COLUMN}' column found in {file_path.name}. Skipping.")
            continue

        # --- EXTRACTING THE TARGET DATA ---
        # Ensure the file actually has the company column before trying to pull data
        if COMPANY_COLUMN in df.columns:
            
            if OPEN_COLUMN in df.columns:
                all_open_prices.append(df[[DATE_COLUMN, COMPANY_COLUMN, OPEN_COLUMN]])
                
            if CLOSE_COLUMN in df.columns:
                all_close_prices.append(df[[DATE_COLUMN, COMPANY_COLUMN, CLOSE_COLUMN]])
                
            if VOLUME_COLUMN in df.columns:
                all_volumes.append(df[[DATE_COLUMN, COMPANY_COLUMN, VOLUME_COLUMN]])

print(f"Successfully processed {len(all_open_prices)} files. Normalizing shape...")

# ==========================================
# 4. NORMALIZE (PIVOT) AND EXPORT
# ==========================================
def save_archive_file(data_list, value_column, output_filename):
    if not data_list:
        return
    
    # Combine all individual daily dataframes into one giant table
    combined_df = pd.concat(data_list, ignore_index=True)
    
    # Drop rows that are missing critical info
    combined_df = combined_df.dropna(subset=[DATE_COLUMN, COMPANY_COLUMN, value_column])
    
    # PIVOT SHAPE: Dates as rows, Companies as Columns. 
    # This is the standard "Single-file archive" shape for stock data.
    normalized_df = combined_df.pivot_table(
        index=DATE_COLUMN, 
        columns=COMPANY_COLUMN, 
        values=value_column
    )
    
    # Save the final file
    output_path = archive_folder / output_filename
    normalized_df.to_csv(output_path)
    print(f"Saved: {output_filename}")

# Run the save function for our three categories
save_archive_file(all_open_prices, OPEN_COLUMN, "open_price.csv")
save_archive_file(all_close_prices, CLOSE_COLUMN, "close_price.csv")
save_archive_file(all_volumes, VOLUME_COLUMN, "volume_traded.csv")

print("Task 2 complete! Check your archive-single-file folder.")