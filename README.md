# osu! SG Map Finder
A simple Python script for calling the osu! API for checking ranked and loved maps by Singaporean mappers.

Used for updating the [SG Maps List Google Sheet](https://docs.google.com/spreadsheets/d/1O7z06_TnZUfj1Clme4CKKrmvqdZ3iV3owcOmQRwkMAE) in the osu! SG Discord.

## Dependencies
Use the python-dotenv package for using the osu! API key stored in the .env file (to be created in the next section)
```
pip install python-dotenv
```

## Getting Started
Get your osu! account's API key, as seen in https://github.com/ppy/osu-api/wiki

After getting the API key, create a .env file in the main project directory and store the API key as an environment variable:
```
API_KEY=<paste-the-api-key-here>
```

## Using the Code
Under main.py, edit the starting date for checking, e.g.
```
start_year = 2023
start_month = 4
start_day = 1
```

Optionally, it is also possible to filter the types of maps using an array. Currently, ranked, approved and loved maps are returned:
```
map_filter = ['1', '2', '4']
```

Run main.py. The output format is:
```
[Map Status] [Set/GD?] | [Approved Date] | [Map URL] | [Song Artist] - [Song Title] | [SG mappers found]
```

The code uses a JSON file containing a list of osu! mappers (names and ids). The code works by checking if:
- the mapper id of the mapset owner is from SG
- the mapset tags contain any SG mapper names stored in the JSON file

New mappers with their first ranked mapsets will be automatically added to the JSON file. However, any new SG mapper who has a GD but was not already in the JSON file will not be added, as GD names in tags are not checked.

The maximum number of maps returned per API call is 500, or about 150 mapsets per run. If the repeat flag in check() is set to true, the API will be called multiple times up to the latest map.