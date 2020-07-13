import os
import time
import sys
import threading
# from gd_downloader import gd_downloader
# from gd_auth import get_drive_service
from gd_sync.gd_downloader import gd_downloader

from gd_sync.gd_auth import gd_auth
from gd_sync.gd_lremove import gd_lremove
from gd_sync.gd_uploader import gd_uploader

import re
import logging
import shutil

class gd_cm(threading.Thread):
    my_logger=None
    def __init__(self,FS):
        threading.Thread.__init__(self)
        self.FS=FS
        
        # service=gd_auth().get_drive_service()
        # self.app_folder=service[1]
        # self.drive_service=service[0]

        self.uploaded_from_client=[]
        self.debugging_identifier="GD Cloud Monitor"

        home=os.path.expanduser('~')
        self.cloud_paths=[
        home+"/Desktop/Dropbox",
        home+"/Desktop/GoogleDrive",
        home+"/Desktop/Box",
        ]

        self.p=re.compile('\d+')
        self.data_file=re.compile('[a-zA-Z]{10}_\d+_2(.md){0,1}.enc')
        self.log_folder_re=re.compile('log(\d){1,2}')

        ## Logger
        if gd_cm.my_logger is None:
            gd_cm.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/gd_sync.log'))
            fh.setLevel(logging.DEBUG)
            gd_cm.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(threadName)s : %(message)s ')
            fh.setFormatter(formatter)
            gd_cm.my_logger.addHandler(fh)

    def run (self):
        
        service=gd_auth().get_drive_service()
        self.app_folder=service[1]
        self.drive_service=service[0]

        initial_page_token = self.drive_service.changes().getStartPageToken().execute()
        page_token = initial_page_token.get('startPageToken')
        try:
            while True:
                time.sleep(1)
                while page_token is not None:

                    fi='changes(file(createdTime,description,explicitlyTrashed,fileExtension,fullFileExtension,id,kind,lastModifyingUser,md5Checksum,mimeType,modifiedTime,name,originalFilename,ownedByMe,parents,permissionIds,properties,shared,sharedWithMeTime,sharingUser,size,spaces,starred,trashed,trashedTime,trashingUser,version),fileId,kind,removed,time,type),newStartPageToken,nextPageToken'

                    response = self.drive_service.changes().list(pageToken=page_token,includeRemoved=True,fields=fi).execute()
                    for change in response.get('changes'):
                        if change.get('file') is None: # resulting from deleting a log file 
                            pass
                        elif change['file']['trashed']:
                            #gd_cm.my_logger.info('Deletion : '+ change['file'])                            
                            if self.p.match(change['file']['name']):
                                gd_cm.my_logger.info("log deletion form the cloud")
                                a=change['file']['parents'][0]
                                parent_name=self.drive_service.files().get(fileId=a,fields="name").execute()['name']
                                name=change['file']['name']
                                name_no_enc=name[0:name.find('.enc')]
                                path=self.cloud_paths[1]+'/FSFolder/'+parent_name+'/'+name_no_enc
                                
                                try:
                                    os.remove(path)
                                    gd_cm.my_logger.info(' deleted : '+path)
                                except Exception as e:
                                    pass
                                    gd_cm.my_logger.info("did not delete the log file," + path)
                            
                                #log_folder_path=self.cloud_paths[1]+'/FSFolder/'+parent_name
                            elif self.log_folder_re.match(change['file']['name']):
                                try:
                                    os.rmdir(self.cloud_paths[1]+'/FSFolder/'+change['file']['name'])
                                    gd_cm.my_logger.info(' deleted folder : '+self.cloud_paths[1]+'/FSFolder/'+change['file']['name'])
                                    gd_uploader.reset_log_session_folder_id()
                                except:
                                    gd_cm.my_logger.info('GD CM did not remove '+change['file']['name']+' because it has a dangling log, or it doesnt exist')

                                # try:
                                #     os.rmdir(log_folder_path)
                                #     a=gd_lremove(log_folder_path,True)
                                #     a.start()
                                #     a.join()
                                #     gd_cm.my_logger.info(' deleted folder : '+path)
                                # except Exception as e:
                                #     pass
                                #     gd_cm.my_logger.info("did not delete {} folder".format(path))               

                            else:
                                gd_cm.my_logger.info("data deletion from the cloud")
                                if not os.path.exists(self.cloud_paths[1]+"/FSFolder/Deleted"):
                                    gd_cm.my_logger.info(" created \"Deleted\" ")
                                    os.mkdir(self.cloud_paths[1]+"/FSFolder/Deleted")
                                if not os.path.exists(self.cloud_paths[1]+"/FSFolder/Deleted/names"):
                                    open (self.cloud_paths[1]+"/FSFolder/Deleted/names",'wb+').close()
                                    gd_cm.my_logger.info(" created file and truncated ")
                                f=open (self.cloud_paths[1]+"/FSFolder/Deleted/names",'a')
                                f.write(change['file']['name']+"\n")
                                f.close()
                                gd_cm.my_logger.info("wrote this to the file : "+change['file']['name']+"\n")
                        
                        elif not change['file']['name'] in self.uploaded_from_client and  self.data_file.match(change['file']['name']): # modify or upload

                            gd_cm.my_logger.info(" GD CM Started a downloader thread for this :"+change['file']['name'])
                            a=gd_downloader(change['fileId'],local_path=self.cloud_paths[1]+'/'+change['file']['name'])
                            a.start()
                        
                        elif change['file']['name'] == 'FSF.enc':
                            pass
                            # below is for monitoringn FSF #
                            
                            gd_cm.my_logger.info('captured new FSF')
                            a=gd_downloader(file_id=change['file']['id'],local_path=self.cloud_paths[1]+'/FSFolder/FSF.enc')
                            a.start()
                            a.join() ## necessary to re initialize.

                            f= open('./reinitializing_cloud.txt','r')
                            cloud=f.read().strip()
                            f.close()
                            if cloud == 'GoogleDrive':
                            #if self.FS.reinitialization_lock.acquire(blocking=False):
                                #gd_cm.my_logger.info('calling reinitialize tree ..')
                                try:
                                    gd_cm.my_logger.info('calling reinitialize tree ..')
                                    self.FS.reinitialize_tree(c='gd')
                                except Exception as e :
                                    gd_cm.my_logger.info('error in re initializing the tree: '+ str(e))
                                else:
                                    #time.sleep(5)
                                    pass
                                    #self.FS.reinitialization_lock.release()
                        else:
                            pass
                            self.uploaded_from_client=[x for x in self.uploaded_from_client if x != change['file']['name']]
                            gd_cm.my_logger.info(" ignored event on :"+change['file']['name'])

                    if 'newStartPageToken' in response:
                        initial_page_token = response.get('newStartPageToken')
                    page_token = response.get('nextPageToken')
                page_token = response.get('newStartPageToken');

        except (KeyboardInterrupt):
            gd_cm.my_logger.info('GDCM interrupted!')
            return

    def set_uploaded_from_client(self,name):
        self.uploaded_from_client.append(name)
