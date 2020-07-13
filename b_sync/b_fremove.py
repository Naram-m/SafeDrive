import threading
from b_sync.b_auth import b_auth
import time
from boxsdk.exception import BoxAPIException
import os
from enc import encryption_module
import math
import os
import logging

class b_fremove():
    my_logger=None
    def __init__(self,p):
        
        self.client,self.app_folder=b_auth().get_authenticated_client()
        self.debugging_identifier='Box Remover :'
        self._run(p)
        pass
        if b_fremove.my_logger is None:
            b_fremove.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/b_sync.log'))
            fh.setLevel(logging.DEBUG)
            b_fremove.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            fh.setFormatter(formatter)
            b_fremove.my_logger.addHandler(fh)
    def _run(self,path_in_b): # path in b will be in the form of App folder/aa_11
        
        file_name=os.path.basename(path_in_b)
        ## get the id of the file and its md and then remove
        search_results=self.client.search(file_name, limit=100, offset=0)
        # search results will be a Box object of two files.
        for file in search_results:
            file.delete()
            self.my_logger.info('deleted thi '+str(file))
        
