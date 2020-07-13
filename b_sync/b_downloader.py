import threading
from b_sync.b_auth import b_auth
import time
from boxsdk.exception import BoxAPIException
import os
from enc import encryption_module
import math
import logging

## this downloader exptects a file id , and a local path which ends with .enc
class b_downloader(threading.Thread):
    my_logger=None
    def __init__(self,file_id='',local_path=''):
        threading.Thread.__init__(self)
        self.debugging_identifier='Box Downloader Thread:'
        self.file_id=file_id
        self.em=encryption_module()
        self.local_path=local_path
        self.client,self.app_folder=b_auth().get_authenticated_client()

        #self.start()
        
        if b_downloader.my_logger is None:
            b_downloader.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/b_sync.log'))
            fh.setLevel(logging.DEBUG)
            b_downloader.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            fh.setFormatter(formatter)
            b_downloader.my_logger.addHandler(fh)
    
    def run(self):
        if not os.path.exists(self.local_path):
            open (self.local_path+'.dn_temp','wb').close()
        f=open (self.local_path,'wb')

        self.client.file(file_id=self.file_id).download_to(f) # box sdk is chunked by default ,, (noticed from the source code)
        f.close()
        b_downloader.my_logger.info(" Downloaded to "+self.local_path)
        try:
            os.remove(self.local_path+'.dn_temp')
        except Exception as e :
            b_downloader.my_logger.info ('ERR: could not delete temp download file :')
        
        self.decrypt_downloaded_file()

    def decrypt_downloaded_file(self):
        try:
            _lmt= 500 * 1024  * 1024
            file_size=os.stat(self.local_path).st_size

            if file_size <= _lmt:

                with open (self.local_path,'rb') as encrypted_file:
                    with open (self.local_path[0:self.local_path.find('.enc')],'wb') as _file:
                        rd=encrypted_file.read()

                        _file.write(self.em.decrypt_(rd))
                
            else:
                div=math.ceil(file_size/_lmt)
                with open (self.local_path,'rb') as encrypted_file:
                    with open (self.local_path[0:self.local_path.find('.enc')],'wb') as _file:
                        for i in range (0,div):
                            e_read=self.em.decrypt_(encrypted_file.read(32+_lmt)) # this 32 is specific to the chosen encryption library
                            _file.write(e_read)
            
            b_downloader.my_logger.info("decrypted file is written")
            os.remove(self.local_path)
        
        except Exception as e: ##TODO revise ?:
            b_downloader.my_logger.info (' could not decrypt downloaded file:')
            os.remove(self.local_path[0:self.local_path.find('.enc')]) # delete the created unencrypted files