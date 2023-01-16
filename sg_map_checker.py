import datetime
import json
import urllib.request


class MapChecker:
    def __init__(self, api_key):
        self.api_key = api_key
        self.map_data = ''
        self.maps_found = 0

        self.file_name = 'mapper_records.json'
        self.sg_mapper_names = []
        self.sg_mapper_ids = []
        self.other_mapper_ids = []

    # Run for checking
    def check(self, start_year, start_month, start_day, map_filter):
        self.read_file()
        self.get_maps(start_year, start_month, start_day)
        self.check_maps(map_filter)
        self.write_file()

    # Read and write list of mappers using json file at the start and end to minimize API calls
    def read_file(self):
        with open(self.file_name, 'r') as f:
            data = json.load(f)

            self.sg_mapper_names = data['sg_mapper_names']
            self.sg_mapper_ids = data['sg_mapper_ids']
            self.other_mapper_ids = data['other_mapper_ids']

    def write_file(self):
        data = {'sg_mapper_names': self.sg_mapper_names,
                'sg_mapper_ids': self.sg_mapper_ids,
                'other_mapper_ids': self.other_mapper_ids}

        with open(self.file_name, 'w') as f:
            json.dump(data, f)

    # API call for map list (max 500)
    def get_maps(self, start_year, start_month, start_day):
        self.map_data = json.load(urllib.request.urlopen('https://osu.ppy.sh/api/get_beatmaps?k=' + self.api_key +
                                                         '&since=' + start_year + start_month + start_day))

    # Iterate and check all maps
    def check_maps(self, map_filter):
        prev_id = ''
        for n, beatmap in enumerate(self.map_data):
            if prev_id != beatmap['beatmapset_id']:
                prev_id = beatmap['beatmapset_id']
                if beatmap['approved'] in map_filter:
                    self.check_mapset(beatmap)

            # print the date of the last map for checking next batch
            if n == len(self.map_data) - 1:
                self.print_summary(beatmap['approved_date'])

    # Check each mapset and print if SG mappers are found
    def check_mapset(self, beatmap):
        found_sg_mappers = []
        mapper_id = beatmap['creator_id']
        mapper_name = beatmap['creator']
        is_sg_owner = mapper_id in self.sg_mapper_ids

        # add mapper if record not found (i.e. new mapper)
        if not is_sg_owner and mapper_id not in self.other_mapper_ids:
            self.add_new_mapper(mapper_id, mapper_name)

        # update SG name list if SG mapper changes name
        if is_sg_owner and mapper_name not in self.sg_mapper_names:
            self.sg_mapper_names.append(mapper_name)

        # find and print SG mappers if mapset owner or in tags (possible GD)
        if is_sg_owner:
            found_sg_mappers.append(mapper_name)

        tags = ' ' + beatmap['tags'].lower() + ' '
        for sg_mapper_name in self.sg_mapper_names:
            if tags.find(' ' + sg_mapper_name.lower() + ' ') != -1:
                found_sg_mappers.append(sg_mapper_name)

        if found_sg_mappers:
            self.maps_found += 1
            print_map(beatmap, found_sg_mappers, is_sg_owner)

    # Add new mappers to list
    def add_new_mapper(self, mapper_id, mapper_name):
        player_url = urllib.request.urlopen('https://osu.ppy.sh/api/get_user?k=' + self.api_key +
                                            '&u=' + mapper_id + '&type=id')
        player_data = json.load(player_url)

        if not player_data:
            # for restricted or deleted mappers
            self.other_mapper_ids.append(mapper_id)
        else:
            country = player_data[0]['country']
            if country == 'SG':
                self.sg_mapper_names.append(mapper_name)
                self.sg_mapper_ids.append(mapper_id)
            else:
                self.other_mapper_ids.append(mapper_id)

    # Print check summary
    def print_summary(self, last_date):
        print("------------------------------------------------------------------------------------------------------")
        print("Checked until: (UTC+0) " + last_date +
              " | (SG time) " + convert_to_sg_time(last_date))
        print("Potential SG maps found: " + str(self.maps_found))
        print("Total maps checked: " + str(len(self.map_data)))

    # Manually add new mapper
    def manual_add_new_mapper(self, mapper_id, mapper_name):
        self.read_file()
        self.add_new_mapper(mapper_id, mapper_name)
        self.write_file()

    # Manually add new name for existing SG mapper
    def manual_add_new_name_sg(self, mapper_name):
        self.read_file()
        self.sg_mapper_names.append(mapper_name)
        self.write_file()


# Returns approved date in SG local time (UTC+8)
def convert_to_sg_time(date):
    utc0_time = datetime.datetime.fromisoformat(date)
    sg_utc = datetime.timedelta(hours=8)
    sg_time = utc0_time + sg_utc
    return str(sg_time)


# Print format for SG maps found
def print_map(beatmap, found_sg_mappers, is_sg_owner):
    status_dict = {'1': "Ranked", '2': "Approved", '3': "Qualified", '4': "Loved"}
    map_status = status_dict[beatmap['approved']]
    map_type = "Set" if is_sg_owner else "GD?"
    sg_time = convert_to_sg_time(beatmap['approved_date'])
    url = "https://osu.ppy.sh/beatmapsets/" + beatmap['beatmapset_id']

    mappers = found_sg_mappers[0]
    for mapper in found_sg_mappers[1:]:
        mappers += " | " + mapper

    print(map_status + ' ' + map_type + ' | '
          + sg_time + ' | '
          + url + ' | '
          + beatmap['artist'] + ' - ' + beatmap['title'] + ' | '
          + mappers)
