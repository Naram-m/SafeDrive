import threading

from b_sync.b_auth import b_auth
# from b_auth import b_auth
from b_sync.b_downloader import b_downloader
# from b_downloader import b_downloader
# from b_uploader import b_uploader
from b_sync.b_uploader import b_uploader

import time
from boxsdk.exception import BoxAPIException
from boxsdk.object import events
import os
import re
import logging

#from enc import encryption_module
import math

class b_start(threading.Thread):
    my_logger=None
    def __init__(self,b_cm=None):
        threading.Thread.__init__(self)
        self.b_cm=b_cm
        self.client,self.app_folder=b_auth().get_authenticated_client()

        self.uploaded_from_client=[]
        self.debugging_identifier="Box Start "
        self.local_parts=[]
        self.cloud_parts=[]
        self.name_to_box_obj={}
        # self.em=encryption_module()


        home=os.path.expanduser('~')
        self.cloud_paths=[
        home+"/Desktop/Dropbox",
        home+"/Desktop/GoogleDrive",
        home+"/Desktop/Box",
        ]

        ## uncompleted downloads , check them and delete them
        for part_file in self.listdir_nohidden (self.cloud_paths[0]):
            fp=self.cloud_paths[0]+'/'+part_file
            if part_file.find(".dn_temp") >= 0: # a part file
                try:
                    os.remove(fp)
                    os.remove(fp[0:fp.rfind('.dn_temp')])
                except Exception as e:
                    b_start.my_logger.info ("ERR: could not deleted uncompleted part file ",e)
        ##

        for part_file in self.listdir_nohidden (self.cloud_paths[2]):
            if part_file.find('FSFolder') < 0 : # a part file
                self.local_parts.append(part_file)

        parts_list=self.app_folder.get_items(limit=200)
        for entry in parts_list:
            if entry.name.find('FSFolder') < 0: #indeed is a part file
                self.cloud_parts.append(entry.name)
                self.name_to_box_obj[entry.name]=entry

        # print ("this is the local list:",self.local_parts)
        # print('\n')
        # print("this is the cloud list: ",self.cloud_parts)

        if b_start.my_logger is None:
            b_start.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/b_sync.log'))
            fh.setLevel(logging.DEBUG)
            b_start.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            fh.setFormatter(formatter)
            b_start.my_logger.addHandler(fh)
    
    def run(self):
        self.brig_to_consistent_state()
    def brig_to_consistent_state(self):
        local_parts_adjusted_list= [x+'.enc' for x in self.local_parts if '.enc' not in x] #add fake .enc extension to local parts just for comparison purposes
        
        #if local list is [x x.enc y y.enc] the adjusted is [x.enc y.enc]
        in_cloud_not_local= list(set(self.cloud_parts) - set(local_parts_adjusted_list))
        #b_start.my_logger.info("in cloud , not local: " + str(in_cloud_not_local))
        for _item in in_cloud_not_local:
            if not 'ss' in _item:
                a=b_downloader(self.name_to_box_obj[_item].id,self.cloud_paths[2]+'/'+_item)
                a.start()
                a.join()
                b_start.my_logger.info("started downloader thread because of  "+_item)



        in_local_not_cloud= list(set(local_parts_adjusted_list) - set(self.cloud_parts))
        #b_start.my_logger.info("in local , not cloud: " + str(in_local_not_cloud))
        ## below code will not work, there is a problem in uploader regarding the .enc extension
        for _item in in_local_not_cloud:
            if not '.md' in _item and not 'ss' in _item:
                a=b_uploader(self.cloud_paths[2]+'/'+_item,b_cm=self.b_cm)
                a.start()
                a.join()
                b_start.my_logger.info(' started uploaded thread for :'+_item)

    def get_current_version (self,path):
        '''
        gets the vresion of the part specified by
        'path' from its associated md file
        '''
        with open(path+'.md') as f:
            version=f.read().strip()
            versionint=int(version.split('v')[1])
        return versionint;
   
    def listdir_nohidden(self,path):
        for f in os.listdir(path):
            if not f.startswith('.'):
                yield f

