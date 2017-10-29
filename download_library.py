import os

from envparse import env
import requests

"""
    Downloads all files from the Constant Contact Library and puts them in directories under the download directory 
    that match the folders on Constant Contact. The name attribute of the file is used (as opposed to the GUID 
    of the S3 file) and if there are duplicate names (which Constant Contact allows), a number is appended to the 
    file name of subsequent files.
"""

env.read_envfile()

API_KEY = env('API_KEY')
ACCESS_TOKEN = env('ACCESS_TOKEN')
DOWNLOAD_DIR = env('DOWNLOAD_DIR')
BASE_URL = 'https://api.constantcontact.com/v2/'
HEADERS = {'Authorization': 'Bearer {}'.format(ACCESS_TOKEN)}

download_count = 0
download_errors = 0


def write_files(files):
    global download_count
    global download_errors

    for f in files:
        name = f.get('name')
        folder = f.get('folder')
        file_url = f.get('url')

        print('Getting {} ...'.format(name))

        fr = requests.get(file_url, stream=True)
        if fr.status_code == 200:
            file_path = '{}/Library'.format(DOWNLOAD_DIR)

            if folder:
                file_path = '{}/{}'.format(file_path, folder)

                if not os.path.exists(file_path):
                    os.mkdir(file_path)

            file_path += '/{}'.format(name)

            # CC allows for file names to be duplicated, so tack a number on the end if the file exists
            if os.path.exists(file_path):
                while True:
                    fn_modifier = 1
                    n = file_path.split('.')[0]
                    ext = file_path.split('.')[1]
                    file_path = '{}_{}.{}'.format(n, fn_modifier, ext)

                    if not os.path.exists(file_path):
                        print('FILE NAME DUPLICATED, RENAMED TO {}'.format(file_path))
                        break

            with open(file_path, 'wb') as nf:
                for chunk in fr:
                    nf.write(chunk)

            download_count += 1
        else:
            print('ERROR DOWNLOADING {}! {}: {}'.format(name, fr.status_code, fr.reason))
            download_errors += 1
            continue


def process_files(data):
    global download_count
    global download_errors

    files = data.get('results')

    if not files:
        print('NO FILES!')
        print(data)
        exit(0)

    write_files(files)

    # if we have a next link, that means there are more pages of files to get
    next_link = data.get('meta').get('pagination').get('next_link')

    while next_link:
        next_code = next_link.split('=')[1]
        res = requests.get(
            '{}library/files?api_key={}&next={}'.format(BASE_URL, API_KEY, next_code),
            headers=HEADERS
        )

        if res.status_code == 200:
            data = res.json()
            files = data.get('results')

            if not files:
                print('NO FILES!')
                print(data)
                exit(0)

            write_files(files)

            next_link = data.get('meta').get('pagination').get('next_link')
        else:
            next_link = None
            print('*** ERROR! {}'.format(res.status_code))

    print('*** ALL DONE! ***')
    print('{} files downloaded, {} download errors.'.format(download_count, download_errors))


def run():
    # make sure DOWNLOAD_DIR and a Library dir under it exist
    if not os.path.exists(DOWNLOAD_DIR):
        os.mkdir(DOWNLOAD_DIR)

    if not os.path.exists('{}/Library'.format(DOWNLOAD_DIR)):
        os.mkdir('{}/Library'.format(DOWNLOAD_DIR))

    # get the first page of results; process_files function handles the paging
    res = requests.get(
        '{}library/files?limit=1000&type=ALL&source=ALL&api_key={}'.format(BASE_URL, API_KEY),
        headers=HEADERS
    )

    if res.status_code == 200:
        process_files(res.json())
    else:
        print('*** ERROR: {}'.format(res.status_code))
        print(res.reason)


if __name__ == '__main__':
    run()
