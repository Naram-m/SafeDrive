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
from db_sync.db_auth import get_DB_account
import logging


class db_logs():

    my_logger=None
    def __init__(self,current_session=''):
        #threading.Thread.__init__(self)
        data=None
        self.dbx=get_DB_account()
        self.debugging_identifier='Dropbox Log Sync: '

        self.current_session=current_session
        self.other_sessions={}

        home=os.path.expanduser('~')
        self.cloud_paths=[
        home+"/Desktop/Dropbox",
        home+"/Desktop/GoogleDrive",
        home+"/Desktop/Box",
        ]

        if db_logs.my_logger is None:
            db_logs.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/db_sync.log'))
            fh.setLevel(logging.DEBUG)
            db_logs.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            fh.setFormatter(formatter)
            db_logs.my_logger.addHandler(fh)
       
    def download_others_logs(self):
        db_logs.my_logger.info("Getting the logs ...")
        _list=None
        session=None
        sessions_list=self.dbx.files_list_folder('/FSFolder')

        for entry in sessions_list.entries:
            if entry.name.find('log') >= 0:
                self.other_sessions[entry.name]=[]

        for session in self.other_sessions:
            db_logs.my_logger.info ("this is session "+session)
            initial_list=self.dbx.files_list_folder('/FSFolder/'+session)
            #db_logs.my_logger.info ("its content: "+str(initial_list.entries))
            cursor=initial_list.cursor
            _list=[x.path_display for x in initial_list.entries]
            _cont=initial_list.has_more
            while _cont:
                new_patch=self.dbx.files_list_folder_continue(cursor)
                _list.extend([x.path_display for x in new_patch.entries])
                cursor=new_patch.cursor
                _cont=new_patch.has_more

            if self.other_sessions:
                self.other_sessions[session]=_list
            
        for session,path_in_db_list in self.other_sessions.items():
            if not os.path.exists(self.cloud_paths[0]+'/FSFolder/'+session):
                os.makedirs(self.cloud_paths[0]+'/FSFolder/'+session)
                for path_in_db in path_in_db_list:
                    self.dbx.files_download_to_file(self.cloud_paths[0]+path_in_db,path_in_db) #should each download be a thread?
                    db_logs.my_logger.info (" downloaded to this "+self.cloud_paths[0]+path_in_db)

    def write_FSF_again(self,fpath):
        with open (fpath,"rb")as f:
            self.dbx.files_upload(f.read(),'/FSFolder/FSF.enc',mode= dropbox.files.WriteMode.overwrite)
            os.remove(fpath)

    def download_FSF(self):
        try:
            path_in_db='/FSFolder/FSF.enc'
            self.dbx.files_download_to_file(self.cloud_paths[0]+path_in_db,path_in_db)

        ## this will happen each time the local dirs and clouds are cleaned, lm will then just use the newly created local one
        except: 
            db_logs.my_logger.info (" FSF not found on the cloud")
