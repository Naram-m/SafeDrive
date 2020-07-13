import threading
from b_sync.b_auth import b_auth
import time
from boxsdk.exception import BoxAPIException
import os
import logging
from data_locking import remove_locks

class b_uploader(threading.Thread):
    box_log_session_folder=None
    my_logger=None
    
    def __init__(self,path,b_cm=None,is_log=False,session='',upload_md=False):
        threading.Thread.__init__(self)
        
        self.session=session
        self.path=path
        self.b_cm=b_cm
        self.is_log=is_log
        self.debugging_identifier='Box Uploader Thread '
        
        ## failure simulation here

        self.client,self.app_folder=b_auth().get_authenticated_client()

        ## end failure simulation
        
        self.upload_md=upload_md

        ## logger:
        if b_uploader.my_logger is None:
            b_uploader.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/b_sync.log'))
            fh.setLevel(logging.DEBUG)
            b_uploader.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(threadName)s : %(message)s ')
            fh.setFormatter(formatter)
            b_uploader.my_logger.addHandler(fh)

        if self.upload_md:
            path_without_enc=self.path[0:self.path.find('.enc')]
            self.md_file_path=path_without_enc+'.md.enc'

    def run(self):
        try:
            log_session_folder=self.path[self.path.find('log'):self.path.rfind('/')]
            if self.is_log:
                ## Reliability try 
                
                #raise Exception ('hello')
                if b_uploader.box_log_session_folder is None:
                    fsfolder=None
                    ## get the fsfolder, create if does not exist
                    for sf in self.app_folder.get_items(limit=100, offset=0):
                        if sf.name=='FSFolder':
                            fsfolder=sf
                            break
                    if fsfolder is None: # no fs folder
                        fsfolder=self.app_folder.create_subfolder('FSFolder') # create fs folder
                        b_uploader.box_log_session_folder=fsfolder.create_subfolder(log_session_folder) # creat log session

                    # fs folder will exist here( either created or found)
                    # now look for log_session_folder, the same way you loked fsfolder
                    for sf in fsfolder.get_items(limit=100, offset=0):
                        if sf.name==log_session_folder:
                            b_uploader.box_log_session_folder=sf
                            break
                    if b_uploader.box_log_session_folder is None: # no fs folder
                        b_uploader.box_log_session_folder=fsfolder.create_subfolder(log_session_folder) # creat log session

                else:
                    pass
                    #print('log session folder  ready for me ')
                try:
                    b_uploader.box_log_session_folder.upload(self.path)
                except BoxAPIException as e :
                    print ('HERE ALSO ')
                    #print(e.context_info)
                    log_id=e.context_info['conflicts']['id']
                    self.client.file(file_id=log_id).update_contents(self.path)  #without .methd , this is not a request 
                else:
                    os.remove(self.path)          
                    b_uploader.my_logger.info('uploaded a log file '+self.path)



                ## end Reliabailiy try 
            else: # normal file
                
                ## for data conflict testing ... 
                # print('     B Uploader sleeping ')
                # time.sleep(20)
                

                if self.b_cm:
                    file_name=os.path.basename(self.path)
                    self.b_cm.set_uploaded_from_client(file_name)
                    if self.upload_md:
                        self.b_cm.set_uploaded_from_client(os.path.basename(self.md_file_path))

                try: # attempt to upload
                    self.app_folder.upload(self.path) # box does not support chunked sdk yet
                except BoxAPIException as e : # upload failed, file exists , update content
                    f_id=e.context_info['conflicts']['id']
                    self.client.file(file_id=f_id).update_contents(self.path)  #without .methd , this is not a request 

                ## Upload MD 
                if self.upload_md:
                    try: 
                        self.app_folder.upload(self.md_file_path) # box does not support chunked sdk yet
                    except BoxAPIException as e : # upload failed, file exists , update content
                        f_id=e.context_info['conflicts']['id']
                        self.client.file(file_id=f_id).update_contents(self.md_file_path)  #without .methd , this is not a request 

                b_uploader.my_logger.info("done uploading a data file :  ... "+self.path)

                if not 'ss' in self.path:
                    try:
                        os.remove(self.path)
                        if self.upload_md:
                            os.remove(self.md_file_path)
                    except Exception as e  :
                        b_uploader.my_logger.info ("ERR : could not remove encrypted file by the uploader  ")
                
                if not '.md' in self.path and not 'ss' in self.path and self.session:
                    part_name=os.path.basename(self.path)
                    pn=part_name[0:part_name.rfind('_')]
                    arg=pn+'_'+self.session
                    try:
                        remove_locks(name=arg,cloud='b')
                    except Exception as e:
                        print ('.')
        
        except Exception as e:
            #print ('EEEEEEEEEEEXXXXXXXXXXCCCCCCCCCCCCCCC',e)
            with open('./down_clouds.txt','w') as f:
                f.write('Box')
            b_uploader.my_logger.info(" Detected and registered a down status, ")
            if self.is_log:
                os.remove(self.path)
            else:
                os.remove(self.path)
                if self.upload_md: # this try is for shares (ss files) only, since they dont have me 
                    os.remove(self.md_file_path)

            ## modifing reinitialize cloud
            with open('./reinitializing_cloud.txt','r+') as f:
                cloud=f.read().strip()
                if cloud == 'Box':
                    f.seek(0)
                    f.truncate()
                    f.write('Dropbox')
            ## 
        else:
            ## start cloud check if up again ..
            
            if not self.b_cm.is_alive():
                print("Starting Box Cloud Monitor ")
                self.b_cm.start()
            if os.path.exists('./down_clouds.txt'):
                with open('./down_clouds.txt','r') as f:
                    saved_mc=f.read().strip()
                if saved_mc == 'Box':
                    # sould repair box here // should erase box from here 
                    pass

            return

    @classmethod
    def reset_log_session_folder_id(cls):   
        cls.box_log_session_folder=None
        if cls.my_logger is not None: # will be none for the (my_sessions) of the log merger ...
            cls.my_logger.info('b_uploader.box_log_session_folder has been reset ...')
        return