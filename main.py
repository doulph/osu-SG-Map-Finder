# Checks for ranked/approved/qualified/loved SG maps from a starting date, max number of maps per API call is 500
# osu! API ref: https://github.com/ppy/osu-api/wiki
import os
from dotenv import load_dotenv
from sg_map_checker import MapChecker

# Input API key
load_dotenv()
api_key = os.getenv("API_KEY")

# Input starting check date in UTC+0 (NOT SG time)
start_year = '2023'
start_month = '01'
start_day = '16'

# Input beatmap status in array for filtering: '1' = ranked, '2' = approved, '3' = qualified, '4' = loved
map_filter = ['1', '2', '4']

# Check for maps from starting date (at most 500 per run)
checker = MapChecker(api_key)
checker.check(start_year, start_month, start_day, map_filter)

# Uncomment to manually add new mappers / to add new SG mapper name during name change
# checker.manual_add_new_mapper(mapper_id, mapper_name)
# checker.manual_add_new_name_sg(mapper_name)
