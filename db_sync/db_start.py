import os
import time
import dropbox
from datetime import timezone
import sys
import threading
from db_sync.db_uploader import db_uploader
from db_sync.db_downloader import db_downloader
from db_sync.db_auth import get_DB_account
from enc import encryption_module
import logging



class db_start (threading.Thread):
    my_logger=None

    def __init__(self,db_cm=None):
        threading.Thread.__init__(self)
        self.db_cm=db_cm
        self.dbx=get_DB_account()
        self.uploaded_from_client=[]
        self.debugging_identifier="DB Start "
        self.local_parts=[]
        self.cloud_parts=[]

        self.em=encryption_module()


        home=os.path.expanduser('~')
        self.cloud_paths=[
        home+"/Desktop/Dropbox",
        home+"/Desktop/GoogleDrive",
        home+"/Desktop/Box",
        ]

        ## uncompleted downloads , check them delete them
        for part_file in self.listdir_nohidden (self.cloud_paths[0]):
            fp=self.cloud_paths[0]+'/'+part_file
            if part_file.find(".dn_temp") >= 0: # a part file
                try:
                    os.remove(fp)
                    os.remove(fp[0:fp.rfind('.dn_temp')])
                except:
                    db_start.my_logger.info ("ERR")
        ##

        for part_file in self.listdir_nohidden (self.cloud_paths[0]):
            if part_file.find('FSFolder') < 0 : # a part file
                self.local_parts.append(part_file)

        parts_list=self.dbx.files_list_folder('')
        for entry in parts_list.entries:
            if entry.name.find('FSFolder') < 0: #indeed is a part file
                self.cloud_parts.append(entry.name)

        if db_start.my_logger is None:
            db_start.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/db_sync.log'))
            fh.setLevel(logging.DEBUG)
            db_start.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            fh.setFormatter(formatter)
            db_start.my_logger.addHandler(fh)


    def run(self):

        self.brig_to_consistent_state()

    def brig_to_consistent_state(self):
        local_parts_adjusted_list= [x+'.enc' for x in self.local_parts if '.enc' not in x] #add fake .enc extension to local parts just for comparison purposes
        in_cloud_not_local= list(set(self.cloud_parts) - set(local_parts_adjusted_list))
        
        for _item in in_cloud_not_local:
            if not 'ss' in _item:
                #self.dbx.files_download_to_file(self.cloud_paths[0]+'/'+_item,'/'+_item) #should each download be a thread?, later
                d=db_downloader(local_path=self.cloud_paths[0]+'/'+_item,db_path='/'+_item)
                d.start()
                d.join()
                db_start.my_logger.info("downloaded "+_item)
                self.my_logger.info('started download thread because of '+_item)
        in_local_not_cloud= list(set(local_parts_adjusted_list) - set(self.cloud_parts))
        for _item in in_local_not_cloud:
            if not 'ss' in _item:
                a=db_uploader(self.cloud_paths[0]+'/'+_item,"/"+_item,db_cm=self.db_cm)
                a.start()
                a.join()
                db_start.my_logger.info("uploaded"+_item)
        return
    
    def get_current_version (self,path):
        '''
        gets the vresion of the part specified by
        'path' from its associated md file
        '''
        with open(path+'.md') as f:
            version=f.read().strip()
            versionint=int(version.split('v')[1])
        return versionint

    def listdir_nohidden(self,path):
        for f in os.listdir(path):
            if not f.startswith('.'):
                yield f
