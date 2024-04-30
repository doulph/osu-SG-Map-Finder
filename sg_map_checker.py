import datetime
import json
import urllib.request


class MapChecker:
    """
    Class for checking ranked/approved/qualified/loved SG maps from a starting date.
    """

    _MAX_API_LIMIT = 500

    def __init__(self, api_key, file_name):
        self._api_key = api_key

        # from JSON file
        self._file_name = file_name
        self._sg_mapper_names = []
        self._sg_mapper_ids = []
        self._other_mapper_ids = []
        self._sg_name_aliases = {}

        # for checking
        self._map_filter = []
        self._repeat = False

        self._start_date = None
        self._check_date = None
        self._end_date = None
        self._map_data = None
        self._sg_beatmaps = None
        self._maps_checked = []
        self._num_sg_maps = 0
        self._new_sg_mappers = {"new_mappers": [], "name_changes": []}

    def check(self, year, month, day, map_filter=["1", "2", "4"], repeat=False):
        """
        Run to check and print ranked SG maps, given a starting check date and map filter.
        Set repeat to true to do repeated API calls up to the latest map.
        """
        # use the default exceptions in datetime
        self._start_date = datetime.datetime(year=year, month=month, day=day)

        assert type(map_filter) == list, "map filter is not a list"
        for m in map_filter:
            assert m in ["1", "2", "3", "4"], "map filter input is invalid"
        self._map_filter = map_filter

        assert type(repeat) == bool, "repeat type is not bool"
        self._repeat = repeat

        self._init_beatmaps()

        self._read_file()
        self._find_maps()
        self._write_file()

        self._print_maps()
        self._print_new_mappers()

    def manual_add_new_mapper(self, mapper_id):
        """
        Manually add new mapper or update SG mapper name to the JSON file.
        """
        self._read_file()
        self._check_new_mapper(mapper_id)
        self._write_file()

        self._print_new_mappers()

    def manual_remove_sg_mapper(self, mapper_id, names):
        """
        Manually remove SG mapper from the JSON file.
        """
        self._read_file()
        if mapper_id in self._sg_mapper_ids:
            mapper_index = self._sg_mapper_ids.index(mapper_id)
            id = self._sg_mapper_ids.pop(mapper_index)
            self._other_mapper_ids.append(id)

            for name in names:
                if name in self._sg_mapper_names:
                    name_index = self._sg_mapper_names.index(name)
                    self._sg_mapper_names.pop(name_index)

            self._write_file()
            print(
                f"Removed SG mapper with id {mapper_id} and names {names} from JSON file."
            )
        else:
            print(f"SG mapper with id {mapper_id} and names {names} not found.")

    def add_mapper_alias(self, sg_mapper_name, alias):
        """
        Manually add SG mapper name alias to the JSON file.
        """
        self._read_file()
        assert sg_mapper_name in self._sg_mapper_names, "SG mapper name not found"

        if sg_mapper_name not in self._sg_name_aliases:
            self._sg_name_aliases[sg_mapper_name] = []
        self._sg_name_aliases[sg_mapper_name].append(alias)

        self._write_file()
        print(f"Added alias {alias} to mapper {sg_mapper_name} in JSON file.")

    def _read_file(self):
        """
        Read list of mappers from the JSON file at the start of checking.
        """
        with open(self._file_name, "r") as f:
            data = json.load(f)

            self._sg_mapper_names = data.get("sg_mapper_names", [])
            self._sg_mapper_ids = data.get("sg_mapper_ids", [])
            self._other_mapper_ids = data.get("other_mapper_ids", [])
            self._sg_name_aliases = data.get("sg_name_aliases", {})

    def _write_file(self):
        """
        Write list of mappers to the JSON file at the end of checking.
        """
        data = {
            "sg_mapper_names": self._sg_mapper_names,
            "sg_mapper_ids": self._sg_mapper_ids,
            "other_mapper_ids": self._other_mapper_ids,
            "sg_name_aliases": self._sg_name_aliases,
        }

        with open(self._file_name, "w") as f:
            json.dump(data, f)

    def _init_beatmaps(self):
        """
        Initialise the dictionary for SG maps.
        """
        self._sg_beatmaps = {}
        for m in self._map_filter:
            self._sg_beatmaps[m] = {"Sets": [], "Tags (Potential GD/Collab)": []}

    def _find_maps(self):
        """
        Find all SG maps returned by the osu! API.
        """
        self._maps_checked = []
        self._check_date = self._start_date

        self._get_and_check_maps()
        if self._repeat:
            while len(self._map_data) == MapChecker._MAX_API_LIMIT:
                self._check_date = self._end_date
                self._get_and_check_maps()

    def _get_and_check_maps(self):
        """
        Get and check the list of maps returned from the osu! API.
        """
        date_string = self._check_date.date().isoformat().replace("-", "")
        self._map_data = json.load(
            urllib.request.urlopen(
                f"https://osu.ppy.sh/api/get_beatmaps?k={self._api_key}&since={date_string}"
            )
        )

        beatmaps = {}
        for n, beatmap in enumerate(self._map_data):
            if beatmap["beatmapset_id"] not in self._maps_checked:
                self._maps_checked.append(beatmap["beatmapset_id"])

            if beatmap["approved"] in self._map_filter:
                if beatmap["beatmapset_id"] not in beatmaps:
                    beatmaps[beatmap["beatmapset_id"]] = []
                beatmaps[beatmap["beatmapset_id"]].append(beatmap)

            if n == len(self._map_data) - 1:
                self._end_date = datetime.datetime.fromisoformat(
                    beatmap["approved_date"]
                )

        for beatmap in beatmaps.values():
            self._check_new_mapper(beatmap[0]["creator_id"], beatmap[0]["creator"])
            self._check_mapset(beatmap)

    def _check_new_mapper(self, mapper_id, mapper_name=None):
        """
        Check and update any new mapper or name changes to the mapper lists.
        """
        new_mapper = (
            mapper_id not in self._sg_mapper_ids
            and mapper_id not in self._other_mapper_ids
        )

        if new_mapper or not mapper_name:
            player_data = json.load(
                urllib.request.urlopen(
                    f"https://osu.ppy.sh/api/get_user?k={self._api_key}&u={mapper_id}&type=id"
                )
            )

            # for manual adding of mappers
            if not mapper_name:
                assert player_data, "mapper not found"
                mapper_name = player_data[0]["username"]

            country = player_data[0]["country"] if player_data else None

        if new_mapper:
            if not player_data:
                # for restricted or deleted mappers
                self._other_mapper_ids.append(mapper_id)
            else:
                if country == "SG":
                    self._sg_mapper_names.append(mapper_name)
                    self._sg_mapper_ids.append(mapper_id)
                    self._new_sg_mappers["new_mappers"].append(mapper_name)
                else:
                    self._other_mapper_ids.append(mapper_id)

        name_change = (
            mapper_id in self._sg_mapper_ids
            and mapper_name not in self._sg_mapper_names
        )
        if name_change:
            self._sg_mapper_names.append(mapper_name)
            self._new_sg_mappers["name_changes"].append(mapper_name)

    def _check_mapset(self, beatmap):
        """
        Store each SG mapset into a dictionary, to be printed later.
        """
        is_sg_owner = beatmap[0]["creator_id"] in self._sg_mapper_ids
        sg_mappers = []

        if is_sg_owner:
            sg_mappers.append(beatmap[0]["creator"])

        tags = f" {beatmap[0]['tags'].lower()} "
        for sg_mapper_name in self._sg_mapper_names:
            if tags.find(f" {sg_mapper_name.lower()} ") != -1:
                sg_mappers.append(sg_mapper_name)

        if sg_mappers:
            modes = []
            mapper_to_diff = {}

            for diff in beatmap:
                if diff["mode"] not in modes:
                    modes.append(diff["mode"])

                diff_name = diff["version"]
                for sg_mapper_name in self._sg_mapper_names:
                    sg_mapper_names = [sg_mapper_name] + self._sg_name_aliases.get(
                        sg_mapper_name, []
                    )
                    has_diff = [
                        diff_name.lower().find(name.lower()) != -1
                        for name in sg_mapper_names
                    ]
                    if any(has_diff):
                        if sg_mapper_name not in mapper_to_diff:
                            mapper_to_diff[sg_mapper_name] = []
                        mapper_to_diff[sg_mapper_name].append(diff_name)

            map_dict = {
                "is_sg_owner": is_sg_owner,
                "beatmapset_id": beatmap[0]["beatmapset_id"],
                "approved_date": beatmap[0]["approved_date"],
                "artist": beatmap[0]["artist"],
                "title": beatmap[0]["title"],
                "sg_mappers": sg_mappers,
                "modes": modes,
                "mapper_to_diff": mapper_to_diff,
            }

            map_type = "Sets" if is_sg_owner else "Tags (Potential GD/Collab)"

            # ignore if the mapset is already in the list (due to multiple API calls)
            for mapset in self._sg_beatmaps[beatmap[0]["approved"]][map_type]:
                if mapset["beatmapset_id"] == beatmap[0]["beatmapset_id"]:
                    return

            self._sg_beatmaps[beatmap[0]["approved"]][map_type].append(map_dict)
            self._num_sg_maps += 1

    def _print_maps(self):
        """
        Print the SG maps found and a summary.
        """

        # Add 8 hours to a datetime object to convert from UTC+0 to SG local time (UTC+8).
        def convert_to_sg_time(date):
            sg_utc = datetime.timedelta(hours=8)
            sg_time = date + sg_utc
            return sg_time

        status_dict = {"1": "Ranked", "2": "Approved", "3": "Qualified", "4": "Loved"}
        modes_dict = {"0": "Standard", "1": "Taiko", "2": "Catch", "3": "Mania"}

        for map_status, map_data in self._sg_beatmaps.items():
            for map_type, mapsets in map_data.items():
                if mapsets:
                    print(f"[{status_dict[map_status]} {map_type}]")

                    for num, mapset in enumerate(mapsets):
                        modes = [modes_dict[mode] for mode in mapset["modes"]]
                        modes_str = ", ".join(modes)

                        url = (
                            f"https://osu.ppy.sh/beatmapsets/{mapset['beatmapset_id']}"
                        )
                        sg_time = str(
                            convert_to_sg_time(
                                datetime.datetime.fromisoformat(mapset["approved_date"])
                            )
                        )
                        beatmap = f"{mapset['artist']} - {mapset['title']}"

                        mappers = ""
                        for i, mapper in enumerate(mapset["sg_mappers"]):
                            if mapset["is_sg_owner"] and i == 0:
                                mapper_diff = ""
                            elif mapper in mapset["mapper_to_diff"]:
                                mapper_diff = " " + str(
                                    mapset["mapper_to_diff"][mapper]
                                )
                            else:
                                mapper_diff = " [?]"
                            mappers += " | " + mapper + mapper_diff
                        mappers = mappers[3:]

                        print(
                            f"{num + 1}. {modes_str} | {url} | {sg_time} | {beatmap} | {mappers}"
                        )

                    print()

        print(
            "------------------------------------------------------------------------------------------------------------------------"
        )
        print(
            f"Checked from: (UTC+0) {str(self._start_date)} | (SG time) {str(convert_to_sg_time(self._start_date))}"
        )
        print(
            f"Checked until: (UTC+0) {str(self._end_date)} | (SG time) {str(convert_to_sg_time(self._end_date))}"
        )
        print(f"Potential SG maps found: {str(self._num_sg_maps)}")
        print(f"Total maps checked: {str(len(self._maps_checked))}")

    def _print_new_mappers(self):
        """
        Print new SG mappers or name changes found (if any).
        """

        def convert_to_str(mapper_list):
            mapper_str = mapper_list[0]
            for mapper in mapper_list[1:]:
                mapper_str += ", " + mapper

            return mapper_str

        if self._new_sg_mappers["new_mappers"]:
            mappers = convert_to_str(self._new_sg_mappers["new_mappers"])
            print(f"New SG mappers added: {mappers}")

        if self._new_sg_mappers["name_changes"]:
            mappers = convert_to_str(self._new_sg_mappers["name_changes"])
            print(f"SG mapper name changes added: {mappers}")
