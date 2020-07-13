import os
import time
import threading

from gd_sync.gd_downloader import gd_downloader
from gd_sync.gd_uploader import gd_uploader
from gd_sync.gd_auth import gd_auth


import logging


class gd_lremove(threading.Thread):
    my_logger=None
    log_folder_id=''
    FSFolder_id=''
    def __init__(self,path,isLogFolder):
        threading.Thread.__init__(self)
        if not isLogFolder:
            self.path=path+'.enc'
        else:
            self.path=path
        self.isLogFolder=isLogFolder
        self.service=gd_auth().get_drive_service()
        self.app_folder=self.service[1]
        self.drive_service=self.service[0]

        self.debugging_identifier='GD LRemover :'
        
        if gd_lremove.my_logger is None:
            gd_lremove.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/gd_sync.log'))
            fh.setLevel(logging.DEBUG)
            gd_lremove.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(threadName)s : %(message)s ')
            fh.setFormatter(formatter)
            gd_lremove.my_logger.addHandler(fh)

        pass

    def run (self):

        sesseion_folder=self.path[self.path.find('log'):self.path.rfind('/')]
        log_name=self.path[self.path.rfind('/')+1:]

        if not gd_lremove.FSFolder_id:
            folder_list = self.drive_service.files().list(q=" name = 'FSFolder' and trashed =false").execute()
            FSFolder_id=folder_list['files'][0].get('id')
 
        if not gd_lremove.log_folder_id:
            q="name contains '"+sesseion_folder+"' and trashed = false and '" + FSFolder_id +"' in parents"
            log_folders_list = self.drive_service.files().list(q=q).execute()
            try:
                log_folder_id=log_folders_list['files'][0].get('id')
            except:# folder already deleted .. 
                pass 
                return # if we wanted to delete it, its already deleted, and if we want to delete a child of it, also already done
        
        if self.isLogFolder:
            #self.drive_service.files().delete(fileId=log_folder_id).execute()
            self.drive_service.files().update(fileId=log_folder_id,body={'trashed': True}).execute()
            gd_uploader.reset_log_session_folder_id()
            gd_lremove.my_logger.info("deleted log folder "+ log_name)
            ## not sure about below ? 
            gd_lremove.log_folder_id=''
            
                        
        else:
            try:
            # get the log itself
                q="name contains '"+log_name+"' and trashed = false and '" + log_folder_id +"' in parents"
                log_file = self.drive_service.files().list(q=q).execute()
                fileId=log_file['files'][0].get('id')
            # deletion
                self.drive_service.files().update(fileId=fileId,body={'trashed': True}).execute()
                gd_lremove.my_logger.info("deleted log  "+ sesseion_folder+'/ '+log_name)
            except: # when gd is up again but it does not see the logs.
                pass
        return
