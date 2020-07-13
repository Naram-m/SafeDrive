# later on, to break circular dependency, the method remove_lockshere has to be extracted for each cloud uploader (with its if condition)
# so that uploader dont need to load this module any more 
import dropbox
import queue
from boxsdk.exception import BoxAPIException

from db_sync.db_auth import get_DB_account
from gd_sync.gd_auth import gd_auth
from b_sync.b_auth import b_auth

from io import StringIO
import timeit
import os

import threading 

dbx=None
app_folder=None
drive_service=None
b_client=None
b_app_folder=None


def initiate_accounts():

    # DB
    global dbx,app_folder,drive_service,b_client,b_app_folder
    dbx=get_DB_account()

    ## GD
    service=gd_auth().get_drive_service()
    app_folder=service[1]
    drive_service=service[0]

    # B
    b_client,b_app_folder=b_auth().get_authenticated_client()

def remove_locks(name='',cloud=''):
    initiate_accounts()
    file_name=name+'.lock'
    if cloud =='db':
        a=threading.Thread(target=db_remove,args=(dbx,file_name))
        a.start()
        a.join()  
    elif cloud =='gd':
        b=threading.Thread(target=gd_remove,args=(drive_service,app_folder,file_name))
        b.start()
        b.join()
    elif cloud =='b':
        c=threading.Thread(target=b_remove,args=(b_client,b_app_folder,file_name))
        c.start()
        c.join()
    elif cloud =='all':
        a=threading.Thread(target=db_remove,args=(dbx,file_name))
        a.start()

        b=threading.Thread(target=gd_remove,args=(drive_service,app_folder,file_name))
        b.start()

        c=threading.Thread(target=b_remove,args=(b_client,b_app_folder,file_name))
        c.start()

        a.join()
        b.join()
        c.join()

## to be used by remove locks :
def db_remove(dbx,file_name):
    
    try:
        dbx.files_delete('/'+file_name)
    except Exception as e :
        print('could not delete lock from db')
def gd_remove(drive_service,app_folder,file_name):
    try:
        folder_list = drive_service.files().list(q=" name = '"+file_name+"' and trashed =false and '"+app_folder+"' in parents ").execute()
        fileId=folder_list['files'][0]['id']
        drive_service.files().delete(fileId=fileId).execute()
    except Exception as e:
        print ('could not delete lock from gd')
def b_remove (b_client,b_app_folder,file_name):
    try:
        file_list=b_app_folder.get_items(limit=200)
        for f in file_list:
            if file_name == f.name:
                f.delete()
                return
    except:
        print('could not delete lock from b')
