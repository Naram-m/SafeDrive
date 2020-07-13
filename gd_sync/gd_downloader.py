import httplib2
import os
import io

from apiclient import discovery
from apiclient.http import MediaIoBaseDownload
from apiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import math

from enc import encryption_module



# from gd_auth import get_drive_service

from gd_sync.gd_auth import gd_auth

import threading
import logging
class gd_downloader(threading.Thread):
    my_logger=None
    def __init__(self,file_id='',local_path=''):

        threading.Thread.__init__(self)
        self.debugging_identifier='GD Downloader Thread:'
        self.local_path=local_path
        self.file_id=file_id
        self.FSFolder_id=-1
        global uploaded
        uploaded=[]
        self.em=encryption_module()

        service=gd_auth().get_drive_service()
        self.app_folder=service[1]
        self.drive_service=service[0]


        home=os.path.expanduser('~')
        self.cloud_paths=[
        home+"/Desktop/Dropbox",
        home+"/Desktop/GoogleDrive",
        home+"/Desktop/Box",
        ]

        ## Logger
        if gd_downloader.my_logger is None:
            gd_downloader.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/gd_sync.log'))
            fh.setLevel(logging.DEBUG)
            gd_downloader.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            fh.setFormatter(formatter)
            gd_downloader.my_logger.addHandler(fh)

    def run(self):
        request = self.drive_service.files().get_media(fileId=self.file_id)
        fh = io.FileIO(self.local_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request,chunksize=100*1024*1024)
        if not os.path.exists(self.local_path+'.dn_temp'):
            open (self.local_path+'.dn_temp','wb+').close()
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        short_p=self.local_path[self.local_path.find('/Google'):]
        gd_downloader.my_logger.info('downloaded to '+ short_p)
        try:
            os.remove(self.local_path+'.dn_temp')
        except Exception as e :
            gd_downloader.my_logger.info ('ERR: could not delete temp download file :'+e)
        self.decrypt_downloaded_file()   
    def decrypt_downloaded_file(self):
        _lmt= 500 * 1024  * 1024
        file_size=os.stat(self.local_path).st_size
        if file_size <= _lmt:
            with open (self.local_path,'rb') as encrypted_file:
                with open (self.local_path[0:self.local_path.find('.enc')],'wb') as _file:
                    _file.write(self.em.decrypt_(encrypted_file.read()))
            
        else:
            div=math.ceil(file_size/_lmt)
            with open (self.local_path,'rb') as encrypted_file:
                with open (self.local_path[0:self.local_path.find('.enc')],'wb') as _file:
                    for i in range (0,div):
                        e_read=self.em.decrypt_(encrypted_file.read(32+_lmt)) # this 32 is specific to the chosen encryption library
                        _file.write(e_read)
        
        gd_downloader.my_logger.info("decrypted file is written")  
        os.remove(self.local_path)