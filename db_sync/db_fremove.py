import os
import time
import dropbox
from datetime import timezone
import sys
import threading
from db_sync.db_auth import get_DB_account
import logging 


class db_fremove():
    my_logger=None
    def __init__(self,path_in_db):
        self.dbx=get_DB_account()
        self.debugging_identifier='DB Remover :'
        
        pass

        if db_fremove.my_logger is None:
            db_fremove.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/db_sync.log'))
            fh.setLevel(logging.DEBUG)
            db_fremove.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            fh.setFormatter(formatter)
            db_fremove.my_logger.addHandler(fh)
        
        self._run(path_in_db)

    def _run(self,path_in_db):

        db_fremove.my_logger.info(" removed "+path_in_db)
        self.dbx.files_delete(path_in_db)

