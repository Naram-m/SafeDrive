import httplib2
import os

from apiclient import discovery
from apiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import argparse


#flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()

class gd_auth:

    #SCOPES = 'https://www.googleapis.com/auth/drive.file'
    SCOPES ='https://www.googleapis.com/auth/drive'
    CLIENT_SECRET_FILE = 'gd_sync/client_secret.json'
    APPLICATION_NAME = '_SafeDrive_demo_nm'

    folder_id=''
    drive_service=None

    def __init__(self):
        pass
    def get_drive_service(self):
        
        with open ("gd_sync/failure_sim","r") as f:
            content=f.read()
        if content =='1':
            return (None,None)
 
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,'drive-python-quickstart.json')

        store = Storage(credential_path)
        credentials = store.get()

        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(gd_auth.CLIENT_SECRET_FILE, gd_auth.SCOPES)
            flow.user_agent = gd_auth.APPLICATION_NAME

            flags=tools.argparser.parse_args(args=[])########## googles argparse will have some flags if we passed empty.
            if flags:
              pass
              credentials = tools.run_flow(flow, store, flags)
            print('Storing credentials to ' + credential_path)

        # service has to be built each time, otherwise there will be unknown parsing errors 
        drive_service=discovery.build('drive', 'v3', http=credentials.authorize(httplib2.Http()))

        ## checking the app folde
        if gd_auth.folder_id == '':
            folder_list = drive_service.files().list(q="name='_SafeDrive_demo_nm' and trashed=false").execute()
            if len (folder_list['files']) ==0:
                #print(" Creating App folder for the first time")
                file_metadata = {'name': '_SafeDrive_demo_nm','mimeType': 'application/vnd.google-apps.folder'}
                _folder = drive_service.files().create(body=file_metadata,fields='id').execute()
                folder_id=_folder.get('id')
            else:
                if folder_list['files'][0].get('name')=='_SafeDrive_demo_nm':
                    folder_id=folder_list['files'][0].get('id')

            gd_auth.folder_id=folder_id
            gd_auth.drive_service=drive_service

            return [drive_service,folder_id]
        else:
            #drive_service=discovery.build('drive', 'v3', http=credentials.authorize(httplib2.Http()))
            return [drive_service,gd_auth.folder_id]
