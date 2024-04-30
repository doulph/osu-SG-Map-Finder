# osu! SG Map Finder

A simple Python script for calling the osu! API for checking ranked and loved maps by Singaporean osu! mappers from a starting date.

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
start_year = 2024
start_month = 4
start_day = 1
```

Optionally, it is possible to filter the types of maps using a list. It is recommended to return the ranked, approved and loved maps:

```
map_filter = ['1', '2', '4']
```

Run main.py. The output format is:

```
[Map Status]
[#]. [Game Mode] | [Map URL] | [Ranked/Loved/Qualified Date] | [Song Artist] - [Song Title] | [SG Mappers] [[Mapper Diffs (if any)]] ...
```

The code uses a JSON file containing a list of osu! mappers (names and ids). The code works by checking if:

- the mapper id of the mapset owner is from SG
- the mapset tags contain any known SG mapper names

New SG mappers with their first ranked/loved mapsets will also be checked and automatically added to the JSON file. However, any collabs or GDs from new SG mappers will not be checked or added.

The maximum number of maps returned per API call is 500, or about 150 mapsets per run. If the repeat flag in check() is set to true, the API will be called multiple times up to the latest map.
