import os
import time
import dropbox
from datetime import timezone
import sys
import threading
from db_sync.db_auth import get_DB_account
import logging


class db_lremove(threading.Thread):
    my_logger=None
    def __init__(self,p,isLogFolder):
        threading.Thread.__init__(self)
        self.isLogFolder=isLogFolder
        if not isLogFolder:
            self.path_in_db=p+'.enc'
        else:
            self.path_in_db=p
        self.dbx=get_DB_account()
        self.debugging_identifier='DB LRemover :'
        #self.run(p)
        pass

        if db_lremove.my_logger is None:
            db_lremove.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/db_sync.log'))
            fh.setLevel(logging.DEBUG)
            db_lremove.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            fh.setFormatter(formatter)
            db_lremove.my_logger.addHandler(fh)

    def run (self):

        try:
            self.dbx.files_delete(self.path_in_db)
            db_lremove.my_logger.info(" removed "+self.path_in_db)
        except Exception as e:
            db_lremove.my_logger.info (" could not l_remove: ")
