import threading
from b_sync.b_auth import b_auth
from b_sync.b_downloader import b_downloader
import time
from boxsdk.exception import BoxAPIException
import os
from enc import encryption_module
import math
import os
import logging


class b_logs():
    my_logger=None

    def __init__(self,current_session=''):
        #threading.Thread.__init__(self)
        self.client,self.app_folder=b_auth().get_authenticated_client()

        self.debugging_identifier='Box Log Sync: '

        self.current_session=current_session
        self.other_sessions={}

        home=os.path.expanduser('~')
        self.cloud_paths=[
        home+"/Desktop/Dropbox",
        home+"/Desktop/GoogleDrive",
        home+"/Desktop/Box",
        ]
    
        if b_logs.my_logger is None:
            b_logs.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/b_sync.log'))
            fh.setLevel(logging.DEBUG)
            b_logs.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            fh.setFormatter(formatter)
            b_logs.my_logger.addHandler(fh)

    def download_others_logs(self):
        
        b_logs.my_logger.info("Getting the logs ...")
        fs_folder=self.get_box_obj('FSFolder')
        try:
            log_sessions=fs_folder.get_items(limit=100) # list folders inside it 
        except Exception as e :
            #print ('no others sessions ',e)
            pass
        else:
            #print (len(log_sessions))
            a=None
            local_session=self.listdir_nohidden_logs_sessions(self.cloud_paths[2]+'/FSFolder')
            for log_session in log_sessions:
                if log_session.name not in local_session:
                    b_logs.my_logger.info("log session : "+log_session.name)
                    #print ('outer : ',log_session)
                    if log_session.name !=self.current_session and  log_session.type =='folder': # second part always false
                        if not os.path.exists(self.cloud_paths[2]+'/FSFolder/'+log_session.name):
                            os.mkdir(self.cloud_paths[2]+'/FSFolder/'+log_session.name)
                        log_files=log_session.get_items(limit=200)
                        for log_file in log_files:
                            # download manually 
                            path=self.cloud_paths[2]+'/FSFolder/'+log_session.name+'/'+log_file.name
                            with open (path,'wb') as f :
                                log_file.download_to(f)
                                b_logs.my_logger.info("downloaded this :"+path)
                if a :
                    a.join() # wait for the last initiated one, normally you should add threads to list and join every element in that list
            return

    def write_FSF_again(self,fpath):
        fs_folder=self.get_box_obj('FSFolder')
        if fs_folder is None :
            res=self.app_folder.create_subfolder('FSFolder')
            res.upload(fpath)        
        else:
            try: # attempt to upload
                fs_folder.upload(fpath) 
            except BoxAPIException as e :
                f_id=e.context_info['conflicts']['id']
                self.client.file(file_id=f_id).update_contents(fpath)
        
        os.remove(fpath)
        b_logs.my_logger.info('wrote FSF again')

    def download_FSF(self):
        try: # important try for first time initiation
            fsf=self.get_box_obj('FSF.enc')
            f = open (self.cloud_paths[2]+'/FSFolder/FSF.enc','wb')
            fsf.download_to(f)
            f.close()
        ## this will happen each time the local dirs and clouds are cleaned, lm will then just use the newly created local one
        except Exception as e : 
            ## necessary to remove the .enc, so that the method decrypt_downloaded_fsf in lm does not truncate the normal fsf
            os.remove(self.cloud_paths[2]+'/FSFolder/FSF.enc')
            b_logs.my_logger.info (" FSF not found on the cloud:")
    
    def get_box_obj(self,name):
        items=self.app_folder.get_items(limit=200)     
        for item in items:
            if item.name=='FSFolder' and name=='FSFolder':
                return item
            elif item.name=='FSFolder' and name =='FSF.enc':
                sis=item.get_items(limit=200)
                for si in sis:
                    if si.name=='FSF.enc':
                        return si
    def listdir_nohidden_logs_sessions(self,path):
        a=[]
        for f in os.listdir(path):
            if not f.startswith('.') and 'log' in f:
                a.append(f)
        return a