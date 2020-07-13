import httplib2
import os
import time
from apiclient import discovery
from apiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from gd_sync.gd_auth import gd_auth

import threading
import logging

from data_locking import remove_locks
class gd_uploader(threading.Thread):

    ## CLASS VARIABLES
    on_the_way=[]
    FSFolder_id=''
    log_folder_id=''

    my_logger=None
    

    def __init__(self,path,gd_cm=None,is_log=False,session='',upload_md=False):
        threading.Thread.__init__(self)
        self.session=session
        self.debugging_identifier='Google Drive Uploading Thread :'
        self.path=path
        self.gd_cm=gd_cm
        self.is_log=is_log
        self.upload_md=upload_md

        ## logger:
        if gd_uploader.my_logger is None:
            gd_uploader.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/gd_sync.log'))
            fh.setLevel(logging.DEBUG)
            gd_uploader.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(threadName)s : %(message)s ')
            fh.setFormatter(formatter)
            gd_uploader.my_logger.addHandler(fh)
        
        if self.upload_md:
            path_without_enc=self.path[0:self.path.find('.enc')]
            self.md_file_path=path_without_enc+'.md.enc'

    def run(self):

         ## Reliability Try 
        try: 
            #raise Exception ('cloud down ...')
            self.service=gd_auth().get_drive_service()
            self.app_folder=self.service[1]
            self.drive_service=self.service[0]

            if self.is_log is True:
                if gd_uploader.FSFolder_id=='':
                    folder_list = self.drive_service.files().list(q="name='FSFolder' and trashed=false").execute()
                    if len (folder_list['files']) ==0  : ## does not exist, create it 
                        file_metadata = {'name': 'FSFolder','mimeType': 'application/vnd.google-apps.folder','parents':[self.app_folder]}
                        _folder = self.drive_service.files().create(body=file_metadata,fields='id').execute()
                        gd_uploader.FSFolder_id=_folder.get('id')
                        gd_uploader.my_logger.info (" created FSFolder with this id "+ gd_uploader.FSFolder_id)
                    else: # it exists, only set its id 
                        if folder_list['files'][0].get('name')=='FSFolder':
                            gd_uploader.FSFolder_id=folder_list['files'][0].get('id')
                        gd_uploader.my_logger.info ("found  FSFolder with a ready id")
                else: # another thread already got the id ready for currently executing thread 
                    pass
                
                if gd_uploader.log_folder_id =='' :
                    log_session_folder=self.path[self.path.find('log'):self.path.rfind('/')]

                    folder_list = self.drive_service.files().list(q=" name contains '"+log_session_folder+"' and trashed =false and '"+gd_uploader.FSFolder_id+"' in parents ").execute()
                    if len (folder_list['files']) ==0 and not log_session_folder in gd_uploader.on_the_way:
                        ## create the log session folder 
                        gd_uploader.on_the_way.append(log_session_folder)
                        file_metadata = {'name': log_session_folder,'mimeType': 'application/vnd.google-apps.folder','parents':[gd_uploader.FSFolder_id]}
                        _folder = self.drive_service.files().create(body=file_metadata,fields='id').execute()
                        ## set the id globally
                        gd_uploader.log_folder_id=_folder.get('id')
                        gd_uploader.my_logger.info (" created log folder "+ log_session_folder)
                        gd_uploader.on_the_way.remove(log_session_folder)
                    else:
                        while log_session_folder in gd_uploader.on_the_way: # some other thread is still creating the log folder, wait for it to set its id 
                            time.sleep(1)
                else:
                    pass


                media = MediaFileUpload(self.path)
                _name=self.path[self.path.rfind('/')+1:]
                request = self.drive_service.files().create(media_body=media, body={'name': _name, 'parents': [gd_uploader.log_folder_id]})
                request.execute()
            
                os.remove(self.path) # this will remove the log1.enc file 
                short_p=self.path[self.path.find('/Google'):]
                gd_uploader.my_logger.info ("done uploading log "+short_p)
            
                

            else: # not log
                
                ## for data conflict testing ... 
                # print('     GD Uploader sleeping ')
                # time.sleep(20)
                

                short_p=self.path[self.path.find('/Google'):]
                gd_uploader.my_logger.info ("uploading a data file "+ short_p)
                _gdlmt=150 * 1024 * 1024
                file_size=os.stat(self.path).st_size

                ## Upload file

                if self.gd_cm :
                    pass
                    _name=self.path[self.path.rfind('/')+1:]
                    self.gd_cm.set_uploaded_from_client(_name)
                    if self.upload_md:
                        self.gd_cm.set_uploaded_from_client(os.path.basename(self.md_file_path))


                media = MediaFileUpload(self.path, chunksize=_gdlmt, resumable=True)
                _name=self.path[self.path.rfind('/')+1:]
                
                try: # does the file exist ?
                    _list = self.drive_service.files().list(q=" name = '"+_name+"' and trashed =false and '"+ self.app_folder+"' in parents").execute()
                    file_id=_list['files'][0].get('id')
                except: # no 
                    request = self.drive_service.files().create(media_body=media, body={'name': _name,'parents':[self.app_folder]})
                else: # yes => update
                    request = self.drive_service.files().update(fileId=file_id,media_body=media, body={'name': _name})

                response = None

                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        pass
                
                ## Uploade MD 
                md_media = MediaFileUpload(self.md_file_path)
                try: # does the file exist ?
                    _list = self.drive_service.files().list(q=" name = '"+os.path.basename(self.md_file_path)+"' and trashed =false and '"+ self.app_folder+"' in parents").execute()
                    file_id=_list['files'][0].get('id')
                except: # no 
                    request = self.drive_service.files().create(media_body=md_media, body={'name': os.path.basename(self.md_file_path),'parents':[self.app_folder]}).execute()
                else: # yes => update
                    request = self.drive_service.files().update(fileId=file_id,media_body=md_media, body={'name': os.path.basename(self.md_file_path)}).execute()

                short_p=self.path[self.path.find('/Google'):]
                gd_uploader.my_logger.info ("done uploading data "+short_p)

                if not 'ss' in self.path: # this will remove the file_name.enc file
                    os.remove(self.path)
                    if self.upload_md:
                        os.remove(self.md_file_path)

                if not '.md' in self.path and not 'ss' in self.path and self.session:
                    part_name=os.path.basename(self.path)
                    pn=part_name[0:part_name.rfind('_')]
                    arg=pn+'_'+self.session
                    try:
                        remove_locks(name=arg,cloud='gd')
                    except Exception as e:
                        print ('.')        
                return
    
        except:
            with open('./down_clouds.txt','w') as f:
                f.write('GoogleDrive')  
            gd_uploader.my_logger.info("uploading"+self.path[self.path.find('/Google'):]+" failed," )                
            gd_uploader.my_logger.info(" Detected and registered a down status, ")
            
            if self.is_log:
                os.remove(self.path)
            else:
                
                os.remove(self.path)
                
                if self.upload_md: # this try is for shares (ss files) only, since they dont have me 
                    # os.remove(self.path[0:self.path.find('.enc')])
                    os.remove(self.md_file_path)
                    # os.remove(self.md_file_path[0:self.md_file_path.find('.enc')])
            
            with open('./reinitializing_cloud.txt','r+') as f:
                cloud=f.read().strip()
                if cloud == 'GoogleDrive':
                    f.seek(0)
                    f.truncate()
                    f.write('Dropbox')

        else:
            ## Reliability check if cloud up again 
            
            
            if not self.gd_cm.is_alive():
                print("Starting GD Cloud Monitor ")
                self.gd_cm.start()

            if os.path.exists('./down_clouds.txt'):
                with open('./down_clouds.txt','r') as f:
                    saved_mc=f.read().strip()
                if saved_mc == 'GoogleDrive':
                    pass            
    
    @classmethod
    def reset_log_session_folder_id(cls):   
        cls.log_folder_id=''
        if cls.my_logger is not None: # will be none for the (my_sessions) of the log merger ...
            cls.my_logger.info('log_folder_id has been reset ...')
        return