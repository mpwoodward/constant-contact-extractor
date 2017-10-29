# Constant Contact Extractor
Simple scripts to get your library files, campaigns, and campaign data out of Constant Contact.

## Requirements
* Python 3.x (I developed against 3.6.2 but I'm not using anything specific to 3.6)
* Other requirements in requirements.txt
* A Constant Contact developer account so you can access their API

Note that the Constant Contact API I was working against was v2, so if they've updated that by the time you come across this, these scripts may or may not work.

## Installation
The usual drill -- I'd recommend creating a virtualenv:
```python
python -m venv myenv
```

Next, activate the virtualenv. On Linux/Mac:
```python
source /path/to/myenv/bin/activate
```

On Windows:
```python
# PowerShell
/path/to/myenv/Scripts/Activate.ps1

# Command Prompt
/path/to/myenv/Scripts/activate.bat
```

Then install the requirements:
```
pip install -r requirements.txt
```

## Configuration
To use these scripts you'll need to have already registered with the Constant Contact API, which you can do [here](http://developer.constantcontact.com/get-started.html).

Once you have an API key and an access token, you'll need to create a `.env` file in the root of the project, and using the `.envsample` file as a guide, include the following variables:
```python
API_KEY
ACCESS_TOKEN
DOWNLOAD_DIR
```

The `DOWNLOAD_DIR` is the top-level root directory under which you want all the files to be downloaded from Constant Contact. The scripts put files in subdirectories under `DOWNLOAD_DIR`.

## Usage
There are three scripts in this package:
* `download_campaign_data.py` -- downloads the raw JSON of each individual campaign
* `download_campaigns.py` -- downloads the HTML version of each individual campaign as a PDF
* `download_library.py` -- downloads all the files in your Constant Contact library (images you've uploaded, etc.)

With the installation and configuration complete, and your virtualenv activated, you can just run each script as needed, e.g.:
```python
python ./download_campaign_data.py
```

I tested pretty thoroughly against the Constant Contact account I was working against when writing these scripts, but if you run into issues with yours, I'd appreciate you submitting an issue or doing a pull request so we can continue to make this useful to others.

## Future Enhancements
What's here scratched my particular itch but I didn't go through every nook and cranny of the API so there are obviously things that could be added.

For example, I didn't worry about contacts since Constant Contact does allow a one-click way to export all your contacts to CSV or Excel.

Another thing that comes to mind is campaign data -- I'm just downloading the raw JSON that contains all the stats for each campaign, but maybe doing that as Excel or even a SQLite datbase would be slick.
