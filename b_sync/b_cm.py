import threading
from b_sync.b_auth import b_auth
#from b_auth import b_auth
from b_sync.b_downloader import b_downloader
from b_sync.b_lremove import b_lremove
from b_sync.b_uploader import b_uploader
import time
from boxsdk.exception import BoxAPIException
from boxsdk.object import events
import os
import re
#from enc import encryption_modul
import math
import shutil

import logging

class b_cm(threading.Thread):
    my_logger=None
    def __init__(self,FS):
        threading.Thread.__init__(self)
        self.FS=FS
        self.uploaded_from_client=[]
        self.debugging_identifier="Box Cloud monitor "
        self.client,self.app_folder=b_auth().get_authenticated_client()
        self.uploaded_from_client=[]

        home=os.path.expanduser('~')
        self.cloud_paths=[
        home+"/Desktop/Dropbox",
        home+"/Desktop/GoogleDrive",
        home+"/Desktop/Box",
        ]

        self.log_file_re=re.compile('\d+')
        self.data_file_re=re.compile('[a-zA-Z]{10}_\d+_3(.md){0,1}.enc')# x_1.md.enc, or x_1.enc
        self.log_folder_re=re.compile('log(\d){1,2}')

        if b_cm.my_logger is None:
            b_cm.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/b_sync.log'))
            fh.setLevel(logging.DEBUG)
            b_cm.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            fh.setFormatter(formatter)
            b_cm.my_logger.addHandler(fh)

    def run (self):
        latest_stream=self.client.events().get_latest_stream_position() # this will not give latests position, it will give latest used position 
        s=self.client.events().get_events(limit=100, stream_position='now')
        current_pos=s['next_stream_position']


        for event in self.client.events().generate_events_with_long_polling(stream_position=current_pos,stream_type=events.UserEventsStreamType.CHANGES): # blocking
            if event['event_type'] == 'ITEM_UPLOAD' :
                
                if not event['source']['name'] in self.uploaded_from_client and self.data_file_re.match(event['source']['name']) :  # new file or new version of a file
                    a=b_downloader(file_id=event['source']['id'],local_path=self.cloud_paths[2]+'/'+event['source']['name'])
                    a.start()
                    b_cm.my_logger.info(" started downloader thread because of this entry"+ event['source']['name'])
                
                elif event['source']['name']== 'FSF.enc':
                    pass
                    
                    # below is FSF Monitor #

                    b_cm.my_logger.info('captured new FSF')
                    a2=b_downloader(file_id=event['source']['id'],local_path=self.cloud_paths[2]+'/FSFolder/FSF.enc')
                    a2.start()
                    a2.join()

                    f= open('./reinitializing_cloud.txt','r')
                    cloud=f.read().strip()
                    f.close()
                    if cloud == 'Box':
                        b_cm.my_logger.info('Box found its name in the file and it is reinitializing')
                    #if self.FS.reinitialization_lock.acquire(blocking=False):
                        try:
                            b_cm.my_logger.info('calling reinitialize tree ..')
                            self.FS.reinitialize_tree(c='b')
                        except Exception as e :
                            b_cm.my_logger.info('error in re initializing the tree: '+ str(e))
                        else:
                            pass
                            #time.sleep(5)
                            #self.FS.reinitialization_lock.release()
                else:# file name in list, or ,its not data file 
                    b_cm.my_logger.info("ignoring and event of :"+ event['source']['name'])
                    self.uploaded_from_client=[x for x in self.uploaded_from_client if x!=event['source']['name']]

                ## you should handle new FSF.enc
            
            elif event['event_type'] == 'ITEM_TRASH' :

                if self.log_file_re.match(event['source']['name']):
                    try:
                        b_cm.my_logger.info ('deletion of this log file'+event['source']['name'])
                        path=self.cloud_paths[2]+'/FSFolder/'+event['source']['parent']['name']+'/'+event['source']['name']
                        path_without_enc=path[0:path.find('.enc')]
                        os.remove(path_without_enc)
                    except Exception as e: # the deleted log is not local 
                        b_cm.my_logger.info ('log deletion not reflected locally, the log might not exist: ')
                                    
                    # try:
                    #     log_folder_path=path[0:path.rfind('/')]
                    #     os.rmdir(log_folder_path)
                        
                    #     a3=b_lremove(log_folder_path,True)
                    #     a3.start()
                    #     a3.join()
                    #     b_cm.my_logger.info(' deleted folder : '+path)
                        
                    #     b_cm.my_logger.info(' deleted this log folder locally : '+log_folder_path)
                    # except:
                    #     b_cm.my_logger.info(' did not delete :'+log_folder_path)


                elif self.log_folder_re.match(event['source']['name']):
                    try:
                        b_uploader.reset_log_session_folder_id()
                        os.rmdir(self.cloud_paths[2]+'/FSFolder/'+event['source']['name'])
                        b_cm.my_logger.info('deleted folder : '+path)
                    except:
                        b_cm.my_logger.info('did not remove '+event['source']['name']+' because it contains a dangling log, or it does not exist ...')
                        
                elif self.data_file_re.match(event['source']['name']):
                    b_cm.my_logger.info ('deletion of data file'+event['source']['name'])
                    if not os.path.exists(self.cloud_paths[2]+"/FSFolder/Deleted"):
                        b_cm.my_logger.info(" created Deleted ")
                        os.mkdir(self.cloud_paths[0]+"/FSFolder/Deleted")
                    if not os.path.exists(self.cloud_paths[0]+"/FSFolder/Deleted/names"):
                        open (self.cloud_paths[0]+"/FSFolder/Deleted/names",'wb+').close()
                        b_cm.my_logger.info(" created file and truncated ")

                    ## below, make sure name does not already exists
                    f=open (self.cloud_paths[0]+"/FSFolder/Deleted/names",'a')
                    f.write(event['source']['name']+"\n")
                    f.close()
                    b_cm.my_logger.info("wrote this to the file : "+event['source']['name']+"\n")
                
    def set_uploaded_from_client(self,name):
        b_cm.my_logger.info(" Insertion of :"+name)
        self.uploaded_from_client.append(name)
