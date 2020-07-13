import os
import threading

from gd_sync.gd_downloader import gd_downloader
from gd_sync.gd_uploader import gd_uploader
from gd_sync.gd_auth import gd_auth

import logging

class gd_start (threading.Thread):
    my_logger=None
    def __init__(self,gd_cm=None):


        threading.Thread.__init__(self)

        service=gd_auth().get_drive_service()
        self.app_folder=service[1]
        self.drive_service=service[0]

        self.gd_cm=gd_cm
        self.uploaded_from_client=[]
        self.debugging_identifier="GD Start"
        self.local_parts=[]
        self.cloud_parts=[]


        home=os.path.expanduser('~')
        self.cloud_paths=[
        home+"/Desktop/Dropbox",
        home+"/Desktop/GoogleDrive",
        home+"/Desktop/Box",
        ]

        if gd_start.my_logger is None:
            gd_start.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/gd_sync.log'))
            fh.setLevel(logging.DEBUG)
            gd_start.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            fh.setFormatter(formatter)
            gd_start.my_logger.addHandler(fh)

        ## uncompleted downloads , check them delete them
        for part_file in self.listdir_nohidden (self.cloud_paths[1]):
            fp=self.cloud_paths[1]+'/'+part_file
            if part_file.find(".dn_temp") >= 0: # a part file
                os.remove(fp)
                os.remove(fp[0:fp.rfind('.dn_temp')])
        ##

        
        self.log_part_to_id={}

        for part_file in self.listdir_nohidden (self.cloud_paths[1]):
            if part_file.find('FSFolder') < 0 : # a part file
                self.local_parts.append(part_file)

        cloud_parts_list=self.get_files_in_folder(self.drive_service,self.app_folder)

        for entry in cloud_parts_list:
            if entry['name'].find('FSFolder') < 0: #indeed is a part file
                self.cloud_parts.append(entry['name'])
                self.log_part_to_id[entry['name']]=entry['id']


    def get_files_in_folder(self,service, folder_id):
        _list=[]
        file_list = self.drive_service.files().list(q=" trashed =false and '"+folder_id+"' in parents ").execute()
        return file_list['files']

    def run(self):

        self.brig_to_consistent_state()

    def brig_to_consistent_state(self):
        
        local_parts_adjusted_list= [x+'.enc' for x in self.local_parts if 'ss' not in x] #add fake .enc extension to local parts just for comparison purposes

        in_cloud_not_local= list(set(self.cloud_parts) - set(local_parts_adjusted_list))
        #print("in cloud , not local: ",in_cloud_not_local)
        for _item in in_cloud_not_local:
            if 'ss' not in _item:
                d=gd_downloader(self.log_part_to_id[_item],self.cloud_paths[1]+'/'+_item)
                d.start()
                self.my_logger.info('started download thread because of '+_item)
                d.join()

        in_local_not_cloud= list(set(local_parts_adjusted_list) - set(self.cloud_parts))
        #print("in local , not cloud: ",in_local_not_cloud)

        for _item in in_local_not_cloud:
            if 'ss' not in _item:
                a=gd_uploader(self.cloud_paths[1]+'/'+_item,gd_cm=self.gd_cm)
                a.start()
                self.my_logger.info('started upload thread because of '+_item)
                a.join()
        return
    
    def listdir_nohidden(self,path):

        for f in os.listdir(path):
            if not f.startswith('.'):
                yield f
