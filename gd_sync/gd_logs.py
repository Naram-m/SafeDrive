import os
import io
import threading
# from gd_auth import get_drive_service
from gd_sync.gd_auth import gd_auth
from apiclient.http import MediaIoBaseDownload
from apiclient.http import MediaFileUpload

import logging

class gd_logs():
    
    my_logger=None

    def __init__(self,current_session=''):
        self.current_session=current_session
        self.debugging_identifier='GD Log Sync: '

        self.service=gd_auth().get_drive_service()
        

        self.app_folder=self.service[1]
        self.drive_service=self.service[0]

        self.other_sessions={}

        home=os.path.expanduser('~')
        self.cloud_paths=[
        home+"/Desktop/Dropbox",
        home+"/Desktop/GoogleDrive",
        home+"/Desktop/Box",
        ]

        folder_list = self.drive_service.files().list(q=" name = 'FSFolder' and trashed =false").execute()
        self.FSFolder_id=folder_list['files'][0].get('id')

        if gd_logs.my_logger is None:
            gd_logs.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/gd_sync.log'))
            fh.setLevel(logging.DEBUG)
            gd_logs.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            fh.setFormatter(formatter)
            gd_logs.my_logger.addHandler(fh)

    def download_others_logs(self):
        gd_logs.my_logger.info("Getting the logs ...")

        ##1- List Log sessions
        q="name contains 'log' and trashed = false and '" + self.FSFolder_id +"' in parents"
        log_folders_list = self.drive_service.files().list(q=q).execute()
        #gd_logs.my_logger.info(' the list of sessions on the cloud : {}'.format(log_folders_list['files']))


        ##2- determin what new sessions
        local_session=self.listdir_nohidden_logs_sessions(self.cloud_paths[1]+'/FSFolder')
        gd_logs.my_logger.info('local list of sessions : {}'.format(local_session))

        other_sessions=[x for x in log_folders_list['files'] if x['name'] not in local_session]

        other_sessions_names =[x['name'] for x in other_sessions]
        gd_logs.my_logger.info('other sesseions names'+str(other_sessions_names))

        other_sessions_ids =[x['id'] for x in other_sessions]


        ## 3- downlaod the logs of other sessions;
        for other_sessions_id,other_sessions_name in zip(other_sessions_ids,other_sessions_names):
            self.my_logger.info('downloading the log session: '+other_sessions_name)
            q="trashed = false and '" + other_sessions_id +"' in parents"
            log_files_list = self.drive_service.files().list(q=q).execute()
            if not os.path.exists(self.cloud_paths[1]+'/FSFolder/'+other_sessions_name):
                os.makedirs(self.cloud_paths[1]+'/FSFolder/'+other_sessions_name)
            sesseion_folder=self.cloud_paths[1]+'/FSFolder/'+other_sessions_name
            for log_file in log_files_list['files']:
                ## download each log file id into
                file_id = log_file['id']
                request = self.drive_service.files().get_media(fileId=file_id)
                fh = io.FileIO(sesseion_folder+'/'+log_file['name'],'wb')
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                gd_logs.my_logger.info(" downloaded "+sesseion_folder+'/'+log_file['name'])

    def write_FSF_again(self,fpath):

        folder_list = self.drive_service.files().list(q=" name = 'FSF.enc' and trashed =false").execute()

        media = MediaFileUpload(fpath)
        _name=fpath[fpath.rfind('/')+1:]

        try:
            FSF_id=folder_list['files'][0].get('id')
        except:
            request = self.drive_service.files().create(media_body=media, body={'name': _name,'parents': [self.FSFolder_id]})
        else:
            request = self.drive_service.files().update(fileId=FSF_id,media_body=media, body={'name': _name})

        request.execute()
        os.remove(fpath)
        gd_logs.my_logger.info("new FSF.enc uploaded...")

    def download_FSF(self): ## download the latest FSF
        try:
            folder_list = self.drive_service.files().list(q=" name = 'FSF.enc' and trashed =false").execute()
            FSF_id=folder_list['files'][0].get('id')

            request = self.drive_service.files().get_media(fileId=FSF_id)
            fh = io.FileIO(self.cloud_paths[1]+'/FSFolder/FSF.enc','wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk() #it will use the default chunk 
            gd_logs.my_logger.info(" downloaded "+self.cloud_paths[1]+'/FSFolder/FSF.enc')
        except:
            gd_logs.my_logger.info ("FSF not found on the cloud")

    def listdir_nohidden_logs_sessions(self,path):
        a=[]
        for f in os.listdir(path):
            if not f.startswith('.') and 'log' in f:
                a.append(f)
        return a
