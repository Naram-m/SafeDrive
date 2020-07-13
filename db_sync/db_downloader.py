import os
import time
import dropbox
from datetime import timezone
import sys
import threading
from db_sync.db_auth import get_DB_account
from enc import encryption_module
import math
import logging


class db_downloader(threading.Thread):

    data=None
    dbx=get_DB_account()

    my_logger=None

    def __init__(self,local_path='',db_path='',db_cm=None,is_log=False):
        threading.Thread.__init__(self)
        self.debugging_identifier='Dropbox Downloader Thread:'
        self.em=encryption_module()
        self.db_path=db_path
        self.local_path=local_path
        self.db_cm=db_cm
        self.is_log=is_log

        if db_downloader.my_logger is None:
            db_downloader.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/db_sync.log'))
            fh.setLevel(logging.DEBUG)
            db_downloader.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            fh.setFormatter(formatter)
            db_downloader.my_logger.addHandler(fh)

    def run(self):

        if not os.path.exists(self.local_path):
            open (self.local_path+'.dn_temp','wb').close()

        self.dbx.files_download_to_file(self.local_path,self.db_path) #should each download be a thread?
        db_downloader.my_logger.info(" Downloaded to "+self.local_path)
        try:
            os.remove(self.local_path+'.dn_temp')
        except Exception as e :
            db_downloader.my_logger.info ('ERR: could not delete temp download file :'+str(e))
        self.decrypt_downloaded_file()

    # a method to decrypt the downloaded part, and then remove the encrypted part
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
        
        db_downloader.my_logger.info("decrypted file is written")
        
        os.remove(self.local_path)