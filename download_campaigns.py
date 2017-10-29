import os

from dateutil.parser import parse as dateparse
from envparse import env
import pdfkit
import requests
from slugify import slugify


"""
    Downloads all campaigns and stores as a PDF. Uses the name of the campaign and either the sent date (preferred) or 
    created date (if there is no sent date) as the file name. Uses PDFKit to generate the PDFs which in my testing 
    seemed to yield better results than Weasyprint for this use case, and is also a heckuva lot easier to install on 
    Windows.
    
    Note that this leverages the campaign's permalink_url to pull up the HTML that is then converted into a PDF. In the 
    case of the project for which these scripts were created, some of the campaigns didn't have a permalink_url. When 
    that occurs I simply output that there's no permalink_url and move on to the next campaign, since without a 
    permalink_url there's no real way to get an HTML representation of the campaign through the API.
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
            campaign_date = campaign_data.get('last_run_date')

            if not campaign_date:  # if it wasn't ever sent this won't exist, so use the date created
                campaign_date = campaign_data.get('created_date')

            campaign_date = dateparse(campaign_date).strftime('%Y-%m-%d')
            permalink_url = campaign_data.get('permalink_url')
            file_path = '{}/Campaigns/{}_{}.pdf'.format(DOWNLOAD_DIR, campaign_date, slugify(name))

            if permalink_url:
                try:
                    pdfkit.from_url(permalink_url, file_path)
                    download_count += 1
                except Exception as e:
                    print('DOWNLOAD OF CAMPAIGN {} FAILED! {}'.format(id, str(e)))
                    download_errors += 1
            else:
                print('NO PERMALINK FOR CAMPAIGN {}!'.format(id))
                download_errors += 1
        else:
            print("ERROR DOWNLOADING {}! {}: {}".format(name, cr.status_code, cr.reason))
            download_errors += 1
            continue


def process_campaigns(data):
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

    if not os.path.exists('{}/Campaigns'.format(DOWNLOAD_DIR)):
        os.mkdir('{}/Campaigns'.format(DOWNLOAD_DIR))

    # get the first page of results; process_files function handles the paging
    res = requests.get(
        '{}emailmarketing/campaigns?status=ALL&api_key={}'.format(BASE_URL, API_KEY),
        headers=HEADERS
    )

    if res.status_code == 200:
        process_campaigns(res.json())
    else:
        print('*** ERROR: {}'.format(res.status_code))
        print(res.reason)


if __name__ == '__main__':
    run()
