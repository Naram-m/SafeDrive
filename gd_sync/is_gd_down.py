import httplib2
import os

from apiclient import discovery
from apiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import argparse


#flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()


#SCOPES = 'https://www.googleapis.com/auth/drive.file'
SCOPES ='https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'gd_sync/client_secret.json'
APPLICATION_NAME = '_SafeDrive_demo_nm'

folder_id=''
drive_service=None



home_dir = os.path.expanduser('~')
credential_dir = os.path.join(home_dir, '.credentials')
credential_path = os.path.join(credential_dir,'drive-python-quickstart.json')

store = Storage(credential_path)
credentials = store.get()


# service has to be built each time, otherwise there will be unknown parsing errors 
drive_service=discovery.build('drive', 'v3', http=credentials.authorize(httplib2.Http()))

 