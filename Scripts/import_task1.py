import os
import shutil
from datetime import datetime

# 1. Define the folder paths
source_csv_folder = './Zimbabwe-Stock-Exchange-Daily-Pricesheets/csv-daily-pricesheets'
source_xlsx_folder = './Zimbabwe-Stock-Exchange-Daily-Pricesheets/xls-daily-price-sheets'
destination_folder = './ZimStock-Project/imported_raw_data'

# Automatically create destination folder if it doesn't exist
if not os.path.exists(destination_folder):
    os.makedirs(destination_folder)

# 2. Define the exact date window for Task 1
start_date = datetime.strptime("2020-10-08", "%Y-%m-%d")
end_date = datetime.strptime("2024-11-08", "%Y-%m-%d")

successfully_imported_dates = set()

def import_files_from_folder(folder_path, file_extension):
    print(f"\nScanning {folder_path} for {file_extension} files...")
    
    if not os.path.exists(folder_path):
        print(f"Error: Could not find folder {folder_path}")
        return

    all_files = os.listdir(folder_path)
    total_files_in_folder = len(all_files)
    print(f"-> Total items found inside this folder: {total_files_in_folder}")
    
    if total_files_in_folder == 0:
        print("-> Warning: This folder is completely empty. Please verify your unzipped files.")
        return

    # Look at the first 3 files matching the extension to diagnose their naming style
    samples = [f for f in all_files if f.endswith(file_extension)][:3]
    if samples:
        print(f"-> Sample files detected: {samples}")
    else:
        print(f"-> Warning: No files ending in '{file_extension}' found here.")
        return

    count = 0
    for filename in all_files:
        if not filename.endswith(file_extension):
            continue
            
        date_string = filename.replace(file_extension, "").strip()
        
        # Smart Date Parsing: Checks for YYYY-MM-DD, DD-MM-YYYY, or YYYYMMDD
        file_date = None
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y%m%d"):
            try:
                file_date = datetime.strptime(date_string, fmt)
                break  
            except ValueError:
                continue

        # Skip if the filename text couldn't be read as a valid date format
        if file_date is None:
            continue 

        # 3. Check if the file's date falls within our window
        if start_date <= file_date <= end_date:
            normalized_date_str = file_date.strftime("%Y-%m-%d")
            
            if normalized_date_str not in successfully_imported_dates:
                source_file = os.path.join(folder_path, filename)
                destination_file = os.path.join(destination_folder, filename)
                
                shutil.copy2(source_file, destination_file)
                successfully_imported_dates.add(normalized_date_str)
                count += 1
                
    print(f"Done! Successfully imported {count} files from this folder.")

# Run the process
import_files_from_folder(source_csv_folder, ".csv")
import_files_from_folder(source_xlsx_folder, ".xlsx")

print(f"\nTask 1 Complete! Total unique daily records imported: {len(successfully_imported_dates)}")