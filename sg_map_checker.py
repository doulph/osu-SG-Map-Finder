import datetime
import json
import urllib.request


class MapChecker:
    """
    Class for checking ranked/approved/qualified/loved SG maps from a starting date.
    """
    _MAX_API_CALLS = 500

    def __init__(self, api_key, file_name):
        self._api_key = api_key

        self._file_name = file_name
        self._sg_mapper_names = []
        self._sg_mapper_ids = []
        self._other_mapper_ids = []
        
        self._map_filter = []
        self._repeat = False
        
        self._start_date = None
        self._check_date = None
        self._end_date = None
        self._map_data = None
        self._maps_found = 0
        self._maps_checked = []
        
        self._beatmap = None
        self._is_sg_owner = False
        self._found_sg_mappers = []


    def check(self, year, month, day, map_filter=['1', '2', '4'], repeat=False):
        """
        Run to check and print ranked SG maps, given a starting check date and map filter.
        Set repeat to true to do repeated API calls up to the latest map.
        """
        # throw the default exceptions in datetime because i'm lazy
        self._start_date = datetime.datetime(year=year, month=month, day=day)
        
        assert type(map_filter) == list, 'map filter is not a list'
        for m in map_filter:
            assert m in ['1', '2', '3', '4'], 'map filter input is invalid'
        self._map_filter = map_filter

        assert type(repeat) == bool, 'repeat type is not bool'
        self._repeat = repeat

        self._read_file()
        self._get_and_check_maps()
        self._write_file()
    

    def manual_add_new_mapper(self, mapper_id):
        """
        Manually add new mapper or update SG mapper name to the JSON file.
        """
        self._read_file()
        self._check_new_mapper(mapper_id, None)
        self._write_file()

    
    def _read_file(self):
        """
        Read list of mappers from the JSON file at the start of checking.
        """
        with open(self._file_name, 'r') as f:
            data = json.load(f)

            self._sg_mapper_names = data['sg_mapper_names']
            self._sg_mapper_ids = data['sg_mapper_ids']
            self._other_mapper_ids = data['other_mapper_ids']


    def _write_file(self):
        """
        Write list of mappers to the JSON file at the end of checking.
        """
        data = {'sg_mapper_names': self._sg_mapper_names,
                'sg_mapper_ids': self._sg_mapper_ids,
                'other_mapper_ids': self._other_mapper_ids}

        with open(self._file_name, 'w') as f:
            json.dump(data, f)


    def _get_and_check_maps(self):
        """
        Check and print all SG maps returned by the osu! API and a summary afterwards.
        """
        self._maps_found = 0
        self._maps_checked = []
        self._check_date = self._start_date
        
        if not self._repeat:
            self._get_maps()
            self._check_maps()
        else:
            while self._repeat:    
                self._get_maps()
                self._check_maps()
                # second part is to avoid an infinite loop if some day returns >=500 map diffs (will never happen though)
                self._repeat = len(self._map_data) == MapChecker._MAX_API_CALLS and self._check_date.date() != self._end_date.date()
                if self._repeat:
                    self._check_date = self._end_date
        
        self._print_summary()


    def _get_maps(self):
        """
        Get the list of maps from the osu! API.
        """
        date_string = self._check_date.date().isoformat().replace('-', '')
        self._map_data = json.load(urllib.request.urlopen(f'https://osu.ppy.sh/api/get_beatmaps?k={self._api_key}&since={date_string}'))


    def _check_maps(self):
        """
        Check the list of maps returned.
        """
        for n, beatmap in enumerate(self._map_data):
            if beatmap['beatmapset_id'] not in self._maps_checked:
                self._maps_checked.append(beatmap['beatmapset_id'])
                if beatmap['approved'] in self._map_filter:
                    self._beatmap = beatmap
                    self._check_new_mapper(beatmap['creator_id'], beatmap['creator'])
                    self._check_mapset()

            if n == len(self._map_data) - 1:
                self._end_date = datetime.datetime.fromisoformat(beatmap['approved_date'])


    def _check_mapset(self):
        """
        Check each mapset and print if SG mappers are found.
        """
        self._found_sg_mappers = []

        self._is_sg_owner = self._beatmap['creator_id'] in self._sg_mapper_ids
        if self._is_sg_owner:
            self._found_sg_mappers.append(self._beatmap['creator'])

        tags = f" {self._beatmap['tags'].lower()} "
        for sg_mapper_name in self._sg_mapper_names:
            if tags.find(f" {sg_mapper_name.lower()} ") != -1:
                self._found_sg_mappers.append(sg_mapper_name)

        if self._found_sg_mappers:
            self._maps_found += 1
            self._print_map()


    def _check_new_mapper(self, mapper_id, mapper_name):
        """
        Check and update any new mapper or name changes to the mapper lists.
        """
        is_manual = mapper_name == None
        new_mapper = mapper_id not in self._sg_mapper_ids and mapper_id not in self._other_mapper_ids

        if is_manual or new_mapper:
            player_data = json.load(urllib.request.urlopen(f'https://osu.ppy.sh/api/get_user?k={self._api_key}&u={mapper_id}&type=id'))
            if is_manual:
                assert player_data, 'mapper not found'
                mapper_name = player_data[0]['username']

            country = player_data[0]['country'] if player_data else None
        
        if new_mapper:
            if not player_data:
                # for restricted or deleted mappers
                self._other_mapper_ids.append(mapper_id)
            else:
                if country == 'SG':
                    self._sg_mapper_names.append(mapper_name)
                    self._sg_mapper_ids.append(mapper_id)
                else:
                    self._other_mapper_ids.append(mapper_id)

        name_change = mapper_id in self._sg_mapper_ids and mapper_name not in self._sg_mapper_names
        if name_change:
            self._sg_mapper_names.append(mapper_name)


    def _print_map(self):
        """
        Print the SG map found.
        """
        status_dict = {'1': 'Ranked', '2': 'Approved', '3': 'Qualified', '4': 'Loved'}
        map_status = status_dict[self._beatmap['approved']]
        map_type = 'Set' if self._is_sg_owner else 'GD?'
        sg_time = str(MapChecker._convert_to_sg_time(datetime.datetime.fromisoformat(self._beatmap['approved_date'])))
        url = f"https://osu.ppy.sh/beatmapsets/{self._beatmap['beatmapset_id']}"
        mappers = self._found_sg_mappers[0]
        for mapper in self._found_sg_mappers[1:]:
            mappers += ' | ' + mapper

        print(f"{map_status} {map_type} | {sg_time} | {url} | {self._beatmap['artist']} - {self._beatmap['title']} | {mappers}")


    def _print_summary(self):
        """
        Print summary after checking.
        """
        print('------------------------------------------------------------------------------------------------------------------------')
        print(f'Checked from: (UTC+0) {str(self._start_date)} | (SG time) {str(MapChecker._convert_to_sg_time(self._start_date))}')
        print(f'Checked until: (UTC+0) {str(self._end_date)} | (SG time) {str(MapChecker._convert_to_sg_time(self._end_date))}')
        print(f'Potential SG maps found: {str(self._maps_found)}')
        print(f'Total maps checked: {str(len(self._maps_checked))}')


    def _convert_to_sg_time(date):
        """
        Add 8 hours to a datetime object to convert from UTC+0 to SG local time (UTC+8).
        """
        sg_utc = datetime.timedelta(hours=8)
        sg_time = date + sg_utc
        return sg_time
