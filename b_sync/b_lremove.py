from b_sync.b_auth import b_auth
from b_sync.b_uploader import b_uploader
import threading
import logging
import os


class b_lremove(threading.Thread):
    my_logger=None
    sesseion_folder_box_obj= None
    def __init__(self,p,isLogFolder):

        threading.Thread.__init__(self)
        self.isLogFolder=isLogFolder
        if not isLogFolder:
            self.path_in_b=p+'.enc'
        else:
            self.path_in_b=p
        self.client,self.app_folder=b_auth().get_authenticated_client()
        self.debugging_identifier='Box LRemover :'
        pass

        if b_lremove.my_logger is None:
            b_lremove.my_logger=logging.getLogger(self.debugging_identifier)
            fh = logging.FileHandler(os.path.expanduser('~/b_sync.log'))
            fh.setLevel(logging.DEBUG)
            b_lremove.my_logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(threadName)s : %(message)s ')
            fh.setFormatter(formatter)
            b_lremove.my_logger.addHandler(fh)

        #b_lremove.my_logger.info('Initiated one with these parameters '+p+','+str(isLogFolder))

    def run (self):
        
        if self.isLogFolder:
            sesseion_folder=self.path_in_b[self.path_in_b.find('log'):]
        else:
            sesseion_folder=self.path_in_b[self.path_in_b.find('log'):self.path_in_b.rfind('/')]
        
        log_name=self.path_in_b[self.path_in_b.rfind('/')+1:]

        sesseion_folder_box_obj=self.set_sesseion_folder_box_obj(sesseion_folder)
       
        if self.isLogFolder:
            # b_lremove.my_logger.info('DeB: deleting a log foler   '+sesseion_folder)
            sesseion_folder_box_obj.delete()
            b_uploader.reset_log_session_folder_id()
            b_lremove.my_logger.info('deleted this folder :'+sesseion_folder_box_obj.name)
            
        else:
            # b_lremove.my_logger.info('DeB: inside else h  ')
            files_inside_session_folder= sesseion_folder_box_obj.get_items(limit=200)
            for f in files_inside_session_folder:
                if f.name==log_name:
                    f.delete()
                    b_lremove.my_logger.info('deleted this '+sesseion_folder_box_obj.name+'/'+f.name)
                    break
        return

    def set_sesseion_folder_box_obj(self,sesseion_folder):
        # b_lremove.my_logger.info('set method called with'+sesseion_folder)

        items=self.app_folder.get_items(limit=200)     
        for item in items:
            if item.name=='FSFolder':
                sis=item.get_items(limit=200)
                for si in sis:
                    if si.name==sesseion_folder:
                        sesseion_folder_box_obj=si
                        return sesseion_folder_box_obj
                        b_lremove.my_logger.info('returned object of '+sesseion_folder)
        b_lremove.my_logger.info('returned NULL of '+sesseion_folder)