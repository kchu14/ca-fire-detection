#!/bin/bash/python
import argparse
import pandas as pd
import pprint
from math import sin, cos, sqrt, atan2, radians
import requests
import time

# Outline of california, based on wikipedia:
# Latitude	32°32′ N to 42° N (32 to 42)
# Longitude	114°8′ W to 124°26′ W (-114 to -124)
# (This is obviously a rectangle, but it's fine for now)
CA_LAT_LOW = 32
CA_LAT_HIGH = 42
CA_LONG_LOW = -124
CA_LONG_HIGH = -114


# Downloads the fire csv file and returns a list of raw data
def get_csv():
    r = requests.get(
        'https://firms.modaps.eosdis.nasa.gov/data/active_fire/c6/csv/MODIS_C6_USA_contiguous_and_Hawaii_24h.csv')
    if r.status_code == 200:
        # Top line is headers: https://earthdata.nasa.gov/what-is-new-collection-6-modis-active-fire-data
        # LAT, LONG, Brightness, SScan, Track, Acq_date, Acq_time, satellite, confidence, verison, bright_t31, frp, daynight
        return r.text.split("\n")[1:-1]  # Top line is headers, last line is blank for some reason
    # Might want to change how we handle errors eventually.
    else:
        time.sleep(5)
        return get_csv()


# Extracts data exclusively within CA Lat/Long bounds
def parse_csv(response):
    ca_data = []

    for line in range(len(response)):
        data_line = response[line].split(",")
        lat = float(data_line[0])
        lon = float(data_line[1])

        # We can also make limits based off of confidence, date, etc.
        if lat > CA_LAT_LOW and lat < CA_LAT_HIGH and lon > CA_LONG_LOW and lon < CA_LONG_HIGH and int(
                data_line[8]) >= 50:
            ca_data.append(data_line)

    return ca_data


def get_list_of_zip_codes(lat, long, range, zip_codes_table):
    '''range in km'''
    list_of_zip_codes = []
    for index, row in zip_codes_table.iterrows():
        p1 = (lat, long)
        p2 = (zip_codes_table.iloc[index]['latitude'], zip_codes_table.iloc[index]['longitude'])
        distance = dist(p1, p2)
        if distance <= range:
            list_of_zip_codes.append(zip_codes_table.iloc[index]['ZIP'])
    return list_of_zip_codes


def dist(p1, p2):
    # radius of earth
    R = 6373.0
    lat1 = radians(p1[0])
    lon1 = radians(p1[1])
    lat2 = radians(p2[0])
    lon2 = radians(p2[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def main(csv_file, radius):
    fire_data = parse_csv(get_csv())
    zip_codes_table = pd.read_csv(csv_file)

    zip_codes_effected = set()
    for list in fire_data:
        [zip_codes_effected.add(result) for result in
         get_list_of_zip_codes(float(list[0]), float(list[1]), radius, zip_codes_table)]

    pprint.pprint(zip_codes_effected)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-z', '--zip-codes', help='file location of zip codes, long, lat table', required=True)
    parser.add_argument('-r', '--radius', help='radius in km for affected area', required=True)
    args = parser.parse_args()
    csv_file = args.zip_codes
    radius = float(args.radius)
    main(csv_file, radius)
