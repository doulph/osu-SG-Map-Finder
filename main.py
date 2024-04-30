# Checks for ranked/approved/qualified/loved SG maps from a starting date for updating the SG Maps Google Sheet
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
file_name = "mapper_records.json"

# Input starting check date in UTC+0 (NOT SG local time)
start_year = 2024
start_month = 4
start_day = 1

# Input beatmap status in array for filtering: '1' = ranked, '2' = approved, '3' = qualified, '4' = loved
map_filter = ["1", "2", "3", "4"]

# Check for maps from starting datez
# It is NOT recommended to set repeat=True for starting dates from a month ago or earlier (to avoid API rate limit)
if __name__ == "__main__":
    checker = MapChecker(api_key, file_name)
    checker.check(
        start_year, start_month, start_day, map_filter=map_filter, repeat=True
    )

    # Uncomment to manually add mappers or update mapper name using mapper id
    # mapper_id = "2123087"
    # checker.manual_add_new_mapper(mapper_id)

    # Uncomment to manually remove SG mappers
    # mapper_id = "7823498"
    # names = ["Ayucchi", "Kotoha", "achyoo"]
    # checker.manual_remove_sg_mapper(mapper_id, names)

    # Uncomment to add alias for SG mappers (to detect GDs, not 100% reliable)
    # mapper_name = "arcpotato"
    # alias = "arc"
    # checker.add_mapper_alias(mapper_name, alias)
