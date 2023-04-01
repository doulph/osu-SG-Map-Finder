# Checks for ranked/approved/qualified/loved SG maps from a starting date for updating the SG maps google sheet
# Print format: [map status] [set/gd?] | [approved date and time (SG time)] | [url] | [artist] - [title] | [SG mappers]

# osu! API (v1) ref: https://github.com/ppy/osu-api/wiki
# SG Maps Google Sheet: https://docs.google.com/spreadsheets/u/1/d/1O7z06_TnZUfj1Clme4CKKrmvqdZ3iV3owcOmQRwkMAE

from dotenv import load_dotenv
from os import getenv
from sg_map_checker import MapChecker

# Input API key
load_dotenv()
api_key = getenv("API_KEY")

# Input JSON file name for loading and saving
file_name = 'mapper_records.json'

# Input starting check date in UTC+0 (NOT SG time)
start_year = 2023
start_month = 4
start_day = 1

# Input beatmap status in array for filtering: '1' = ranked, '2' = approved, '3' = qualified, '4' = loved
map_filter = ['1', '2', '4']

# Check for maps from starting date
if __name__ == "__main__":
    checker = MapChecker(api_key, file_name)
    checker.check(start_year, start_month, start_day, map_filter, repeat=True)

    # Uncomment below to manually add mappers or update mapper name using mapper id
    # mapper_id = '12345678' 
    # checker.manual_add_new_mapper(mapper_id)
