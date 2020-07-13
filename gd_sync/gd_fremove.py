import os
import time
import dropbox
from datetime import timezone
import sys
import threading

from gd_sync.gd_downloader import gd_downloader
from gd_sync.gd_uploader import gd_uploader
from gd_sync.gd_auth import gd_auth

import logging
class gd_fremove():
    my_logger=None
    def __init__(self,p):

        service=gd_auth().get_drive_service()
        self.app_folder=service[1]
        self.drive_service=service[0]

        self.debugging_identifier='GD Remover :'
        
        ## logger:
        if gd_fremove.my_logger is None:
            gd_fremove.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/gd_sync.log'))
            fh.setLevel(logging.DEBUG)
            gd_fremove.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            fh.setFormatter(formatter)
            gd_fremove.my_logger.addHandler(fh)
        
        self._run(p)
       

    def _run(self,path_in_gd):

        name=path_in_gd[1:]

        folder_list = self.drive_service.files().list(q=" name contains '"+name+"' and trashed =false and '"+self.app_folder+"' in parents ").execute()
        for file in folder_list['files']:
            if '.md' in file['name']:
                MdfileId=file['id']
            else :
                fileId=file['id']
        #self.drive_service.files().delete(fileId=fileId).execute()
        self.drive_service.files().update(fileId=fileId,body={'trashed':True}).execute()
        try:
            #self.drive_service.files().delete(fileId=MdfileId).execute()
            self.drive_service.files().update(fileId=MdfileId,body={'trashed':True}).execute()
        except :
            gd_fremove.my_logger.info ("couldnt delete md ")
