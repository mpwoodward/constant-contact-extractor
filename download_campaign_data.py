import json
import os

from dateutil.parser import parse as dateparse
from envparse import env
import requests
from slugify import slugify


"""
    Downloads the JSON representation of all campaign data. Mostly important if for some reason you want to retain 
    campaign stats such as sends, opens, clicks, etc. Might make sense at some point to throw all this in a database 
    if you really care about having ready access to the data, but this at least gets it out of Constant Contact for 
    potential future use.
"""

env.read_envfile()

API_KEY = env('API_KEY')
ACCESS_TOKEN = env('ACCESS_TOKEN')
DOWNLOAD_DIR = env('DOWNLOAD_DIR')
BASE_URL = 'https://api.constantcontact.com/v2/'
HEADERS = {'Authorization': 'Bearer {}'.format(ACCESS_TOKEN)}

download_count = 0
download_errors = 0


def write_campaigns(campaigns):
    global download_count
    global download_errors

    for c in campaigns:
        id = c.get('id')
        name = c.get('name')
        campaign_url = '{}emailmarketing/campaigns/{}?api_key={}'.format(BASE_URL, id, API_KEY)

        print("Getting {} (ID {}) ...".format(name, id))

        cr = requests.get(campaign_url, headers=HEADERS)

        if cr.status_code == 200:
            campaign_data = cr.json()
            created_date = dateparse(campaign_data.get('created_date')).strftime('%Y-%m-%d')
            file_path = '{}/CampaignData/{}_{}.json'.format(DOWNLOAD_DIR, created_date, slugify(name))

            with open(file_path, 'w') as outfile:
                json.dump(campaign_data, outfile, indent=4)
            download_count += 1
        else:
            print("ERROR DOWNLOADING {}! {}: {}".format(name, cr.status_code, cr.reason))
            download_errors += 1
            continue


def process_data(data):
    global download_count
    global download_errors

    campaigns = data.get('results')

    if not campaigns:
        print('NO CAMPAIGNS!')
        print(data)
        exit(0)

    write_campaigns(campaigns)

    # if we have a next link, that means there are more pages of campaigns to get
    next_link = data.get('meta').get('pagination').get('next_link')

    while next_link:
        next_code = next_link.split('=')[1]
        res = requests.get(
            '{}emailmarketing/campaigns?api_key={}&next={}'.format(BASE_URL, API_KEY, next_code),
            headers=HEADERS
        )

        if res.status_code == 200:
            data = res.json()
            campaigns = data.get('results')

            if not campaigns:
                print('NO CAMPAIGNS!')
                print(data)
                exit(0)

            write_campaigns(campaigns)

            next_link = data.get('meta').get('pagination').get('next_link')
        else:
            next_link = None
            print('*** ERROR! {}'.format(res.status_code))

    print('*** ALL DONE! ***')
    print('{} campaigns downloaded, {} download errors.'.format(download_count, download_errors))


def run():
    # make sure DOWNLOAD_DIR and a Campaigns dir under it exist
    if not os.path.exists(DOWNLOAD_DIR):
        os.mkdir(DOWNLOAD_DIR)

    if not os.path.exists('{}/CampaignData'.format(DOWNLOAD_DIR)):
        os.mkdir('{}/CampaignData'.format(DOWNLOAD_DIR))

    # get the first page of results; process_files function handles the paging
    res = requests.get(
        '{}emailmarketing/campaigns?status=ALL&api_key={}'.format(BASE_URL, API_KEY),
        headers=HEADERS
    )

    if res.status_code == 200:
        process_data(res.json())
    else:
        print('*** ERROR: {}'.format(res.status_code))
        print(res.reason)


if __name__ == '__main__':
    run()
