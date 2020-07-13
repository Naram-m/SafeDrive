import argparse
import contextlib
import datetime
import os
import six
import sys
import time
import unicodedata
import dropbox
import asyncio
import threading
from db_sync.db_auth import get_DB_account
import logging

from data_locking import remove_locks

class db_uploader(threading.Thread):

    data=None


    
    my_logger=None 

    debugging_identifier='Dropbox Uploading Thread'
    def __init__(self,path,dest,db_cm=None,is_log=False,session='',upload_md=False):
        threading.Thread.__init__(self)
        self.session=session
        self.path=path
        self.dest=dest
        self.db_cm=db_cm
        self.is_log=is_log
        self.upload_md=upload_md
        uploaded=[]

        if db_uploader.my_logger is None:
            db_uploader.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/db_sync.log'))
            fh.setLevel(logging.DEBUG)
            db_uploader.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s -%(threadName)s- %(message)s')
            fh.setFormatter(formatter)
            db_uploader.my_logger.addHandler(fh)

        if self.upload_md:
            path_without_enc=self.path[0:self.path.find('.enc')]
            self.md_file_path=path_without_enc+'.md.enc'

        self.dbx=get_DB_account()

    def run(self):
        try:
            if self.is_log:
                with open(self.path, 'rb') as f:
                    self.dbx.files_upload(f.read(), self.dest,mode= dropbox.files.WriteMode.overwrite)
                os.remove(self.path)
                a=db_uploader.my_logger.info(" done uploading a log :"+ os.path.basename(self.path))

            else:
                
                ## for data conflict testing ...
                # print('     DB Uploader sleeping ')
                # time.sleep(20)
                

                db_uploader.my_logger.info ("started uploading a data file: "+ os.path.basename(self.path))
                _dblmt=150  * 1024 * 1024
                file_size=os.stat(self.path).st_size

                ## Upload file

                if self.db_cm:
                    self.db_cm.set_uploaded_from_client(self.dest)
                    if self.upload_md:
                        self.db_cm.set_uploaded_from_client(self.md_file_path[self.md_file_path.rfind('/'):])

                if  file_size<= _dblmt:
                    with open(self.path, 'rb') as f:
                        self.dbx.files_upload(f.read(), self.dest,mode= dropbox.files.WriteMode.overwrite)

                else : # bigger than 150 MB
                    with open(self.path, 'rb') as f:
                        upload_session_start_result = self.dbx.files_upload_session_start(f.read(_dblmt))
                        cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,offset=f.tell())
                        commit = dropbox.files.CommitInfo(path=self.dest,mode= dropbox.files.WriteMode.overwrite)
                        while f.tell() < file_size:
                            if ((file_size - f.tell()) <= _dblmt):
                                self.dbx.files_upload_session_finish(f.read(_dblmt),cursor,commit)
                            else:
                                self.dbx.files_upload_session_append(f.read(_dblmt),cursor.session_id,cursor.offset)
                                cursor.offset = f.tell()


                ## Upload MD
                if self.upload_md:
                    with open(self.md_file_path, 'rb') as fmd:
                        self.dbx.files_upload(fmd.read(), '/'+os.path.basename(self.md_file_path),mode= dropbox.files.WriteMode.overwrite)
                ## uploading done, remove the encrypted locally
                db_uploader.my_logger.info ("done uploading a data file: "+ os.path.basename(self.path))
                if not 'ss' in self.path:
                    os.remove(self.path)
                    if self.upload_md:
                        os.remove(self.md_file_path)
                
                if not '.md' in self.path and not 'ss' in self.path and self.session:
                    part_name=os.path.basename(self.dest)
                    pn=part_name[0:part_name.rfind('_')]
                    arg=pn+'_'+self.session
                    try:
                        remove_locks(name=arg,cloud='db')
                    except Exception as e:
                        print ('.')        
                return
        except Exception as e:
            with open('./down_clouds.txt','w') as f:
                f.write('Dropbox')
            
            a=db_uploader.my_logger.info("Uploading "+self.dest+" failed .. ")
            a=db_uploader.my_logger.info(" Detected and registered a down status, ")
        
            if self.is_log:
                os.remove(self.path)
            else:
                os.remove(self.path)     
                if self.upload_md: 
                    os.remove(self.md_file_path)
            
            ## modifying reinitialize cloud file
            
            with open('./reinitializing_cloud.txt','r+') as f:
                cloud=f.read().strip()
                if cloud == 'Dropbox':
                    f.seek(0)
                    f.truncate()
                    f.write('GoogleDrive')            
        else:
            ## Reliability check if a cloud is up again
            
            if not self.db_cm.is_alive():
                print("Starting DB Cloud Monitor ")
                self.db_cm.start()
            if os.path.exists('./down_clouds.txt'):
                with open('./down_clouds.txt','r') as f:
                    saved_mc=f.read().strip()
                if saved_mc == 'Dropbox':
                    pass
                    print("Dropbox up again, sould repair...") # should erase down_clouds
    
