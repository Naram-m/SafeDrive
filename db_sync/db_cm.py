import os
import time
import dropbox
import sys
import threading
from db_sync.db_downloader import db_downloader
from db_sync.db_auth import get_DB_account
from db_sync.db_lremove import db_lremove
import re
import logging
import shutil
import traceback


class db_cm(threading.Thread):
    my_logger=None
    def __init__(self,FS):
        threading.Thread.__init__(self)
        self.FS=FS
        self.dbx=get_DB_account()
        self.uploaded_from_client=[]
        self.debugging_identifier="DB CM"
        self.local_parts=[]
        self.cloud_parts=[]

        self.p=re.compile('\d+.enc') ## untested addition
        self.data_file_re=re.compile('[a-zA-Z]{10}_\d+_1(.md){0,1}.enc')# x_1.md.enc, or x_1.enc
        self.log_folder_re=re.compile('log(\d){1,2}')
        home=os.path.expanduser('~')
        self.cloud_paths=[
        home+"/Desktop/Dropbox",
        home+"/Desktop/GoogleDrive",
        home+"/Desktop/Box",
        ]

        if db_cm.my_logger is None:
            db_cm.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/db_sync.log'))
            fh.setLevel(logging.DEBUG)
            db_cm.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            fh.setFormatter(formatter)
            db_cm.my_logger.addHandler(fh)


    def run(self):
        try:
            c=self.dbx.files_list_folder('',recursive=True).cursor;
            while True:
                res=self.dbx.files_list_folder_longpoll(c, timeout=300)
                if res.changes == True:
                    res2=self.dbx.files_list_folder_continue(c)
                    for entry in res2.entries:
                        dropbox_path=entry.path_lower;
                        if isinstance (entry,dropbox.files.DeletedMetadata) and not '.lock' in entry.name: # ignore deletions on lock files
                            db_cm.my_logger.info(' Deletion: {}'.format(entry.name))
                            #print("DeletedMetadata :"+entry.name)
                            if self.p.match(entry.name):
                                db_cm.my_logger.info("log deletion from the cloud")
                                path=entry.path_display
                                #print("this path:",path)
                                path_without_enc=path[0:path.find('.enc')] # starts from /FSFolder
                                try:
                                    os.remove(self.cloud_paths[0]+'/'+path_without_enc)
                                except OSError:
                                    pass
                                    db_cm.my_logger.info("could not delete {}, it does not exist locally".format(self.cloud_paths[0]+'/'+path_without_enc))
                                
                                log_foler_path=path[0:path.rfind('/')]
                                
                            elif self.log_folder_re.match(entry.name):
                                try:
                                    os.rmdir(self.cloud_paths[0]+entry.path_display)
                                    db_cm.my_logger.info('deleted folder : '+path)
                                except:
                                    db_cm.my_logger.info('did not remove '+entry.path_display+' because it contains a dangling log, or it does not exist ...')


                            else:
                                db_cm.my_logger.info("data deletion from the cloud")
                                if not os.path.exists(self.cloud_paths[0]+"/FSFolder/Deleted"):
                                    db_cm.my_logger.info(" created Deleted ")
                                    os.mkdir(self.cloud_paths[0]+"/FSFolder/Deleted")
                                if not os.path.exists(self.cloud_paths[0]+"/FSFolder/Deleted/names"):
                                    open (self.cloud_paths[0]+"/FSFolder/Deleted/names",'wb+').close()
                                    db_cm.my_logger.info(" created file and truncated ")

                                f=open (self.cloud_paths[0]+"/FSFolder/Deleted/names",'a')
                                f.write(entry.name+"\n")
                                f.close()
                                db_cm.my_logger.info("wrote this to the file : "+entry.name+"\n")

                        elif isinstance (entry,dropbox.files.FileMetadata) and  self.data_file_re.match(entry.name): ## don download logs #fix in GD
                            if not entry.name in self.uploaded_from_client:
                                #self.dbx.files_download_to_file(self.dir+'/'+entry.name,'/'+entry.name) #should each download be a thread?
                                a=db_downloader(local_path=self.cloud_paths[0]+'/'+entry.name,db_path='/'+entry.name)
                                a.start()
                                db_cm.my_logger.info(" started downloader thread because of this entry"+str(entry.name))
                            else:
                                db_cm.my_logger.info("ignored event on :"+entry.name)
                                self.uploaded_from_client=[x for x in self.uploaded_from_client if x != entry.name]

                        elif isinstance (entry,dropbox.files.FileMetadata) and  entry.name=='FSF.enc':
                            db_cm.my_logger.info('captured new FSF')
                            a=db_downloader(local_path=self.cloud_paths[0]+'/FSFolder/FSF.enc',db_path='/FSFolder/FSF.enc')
                            a.start()
                            a.join()

                            f= open('./reinitializing_cloud.txt','r')
                            cloud=f.read().strip()
                            f.close()
                            if cloud == 'Dropbox':
                            #if self.FS.reinitialization_lock.acquire(blocking=False):
                                try:
                                    db_cm.my_logger.info('calling reinitialize tree ..')
                                    self.FS.reinitialize_tree()
                                except Exception as e :
                                    db_cm.my_logger.info('error in re initializing the tree: '+ str(e))
                                    traceback.print_exc()
                                else:
                                    pass
                                    #time.sleep(5)
                                    #self.FS.reinitialization_lock.release()

                    c=res2.cursor

        except (KeyboardInterrupt):
            print('interrupted!')
            sys.exit(0)

    def set_uploaded_from_client(self,name):
        #db_cm.my_logger.info(" Insertion of : "+name[1:])
        self.uploaded_from_client.append(name[1:])





    def listdir_nohidden(self,path):
        for f in os.listdir(path):
            if not f.startswith('.'):
                yield f
