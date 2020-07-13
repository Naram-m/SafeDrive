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

from enc import encryption_module

start_time = timeit.default_timer()

## Encryption module 

home=os.path.expanduser('~')
cloud_paths=[
home+"/Desktop/Dropbox",
home+"/Desktop/GoogleDrive",
home+"/Desktop/Box",
]

dbx=None
app_folder=None
drive_service=None
b_client=None
b_app_folder=None

em=encryption_module(available_clouds=[cloud_paths[0],cloud_paths[1],cloud_paths[2]])

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

def place_locks(name=''):

    file_name=name+'.lock'

    a=threading.Thread(target=db_up,args=(dbx,file_name))
    a.start()
    b=threading.Thread(target=gd_up,args=(drive_service,app_folder,file_name))
    b.start()

    c=threading.Thread(target=b_up,args=(b_client,b_app_folder,file_name))
    c.start()

    a.join()
    b.join()
    c.join()

def ensure_only_one(name=''):
    q = queue.Queue()

    a=threading.Thread(target=db_check,args=(dbx,name,q))
    a.start()
    b=threading.Thread(target=gd_check,args=(drive_service,app_folder,name,q))
    b.start()
    c=threading.Thread(target=b_check,args=(b_client,b_app_folder,name,q))
    c.start()

    a.join()
    b.join()
    c.join()

    # while testing TTR, with clouds numbers, edit the qsize condition to any small number, -1, ust to make it work. when experimenting is done, return it to 2
    if q.qsize() < 2:
    #if q.qsize() < -1:
        raise Exception (' no enough clouds ...')
    else:
        #print ('enough')
        comm=True
        while q.qsize():
            nxt=q.get()
            #print (' anding ',comm,"  ",nxt )
            comm=comm and nxt
            
            ## Experiment.. 
            ## - to simulate data conflict without the need to run multiple machines or upload lock files manually.
            ## - in order for this simulation to work, dont forget to disable (ensure only merger in the main file)
            #  comm= False
            ## end simulate data conflict 
        return comm

def ensure_newer_version(name='',version_to_be_written=''):

    q2=queue.Queue()

    vc=threading.Thread(target=b_version,args=(b_client,b_app_folder,name,q2))
    vc.start()
    vb=threading.Thread(target=gd_version,args=(drive_service,app_folder,name,q2))
    vb.start()
    va=threading.Thread(target=db_version,args=(dbx,name,q2))
    va.start()

    vc.join()
    vb.join()
    va.join()
    
    
    ## always will be 3, not like ensure only ...
    v_x =q2.get()
    v_y=q2.get() 
    #v_y='nv' # put 0 to for experimenting TTR

    v_z=q2.get()
    #v_z='nv' # put 0 to for experimenting TTR

    print ('version to be written',version_to_be_written)
    if v_x =='nv' and v_y =='nv' and v_z=='nv': # first time writing a file, or a cloud is un available
        return True

    elif v_x =='nv':

        if version_to_be_written > max([int(str_v.split('\n')[0].split('v')[1]) for str_v in [v_y,v_z]]):
            return True
        else:
            return False
    elif v_y =='nv':

        if version_to_be_written > max([int(str_v.split('\n')[0].split('v')[1]) for str_v in [v_x,v_z]]):
            return True
        else:
            return False
    elif v_z =='nv':
        
        if version_to_be_written > max([int(str_v.split('\n')[0].split('v')[1]) for str_v in [v_x,v_y]]):
            return True
        else:
            return False

    else:
        if version_to_be_written > max([int(str_v.split('\n')[0].split('v')[1]) for str_v in [v_x,v_y,v_z]]):
            return True
        else:
            return False
       
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

## this is the main interface funtion
def get_write_permission(name='',version_to_be_written=''):
    initiate_accounts()
    place_locks(name=name)
    name_without_session=name[0:name.find('_session')]
    return (ensure_only_one(name=name_without_session) and ensure_newer_version(name=name_without_session,version_to_be_written=version_to_be_written))


## Helper functions :

## to be used by place locks
def db_up(dbx,file_name):
    try:
        db_up=dbx.files_upload(b' ','/'+file_name,mode= dropbox.files.WriteMode.overwrite)
    except:
        print('Could not place a lock in db')
def gd_up(drive_service,app_folder,file_name):
    try:
        try: # does the file exist ?
            _list = drive_service.files().list(q=" name = '"+file_name+"' and trashed =false and '"+ app_folder+"' in parents").execute()
            file_id=_list['files'][0].get('id')
        except: # no 
            request = drive_service.files().create(body={'name': file_name,'parents':[app_folder]}).execute()
        else: # yes => update
            request = drive_service.files().update(fileId=file_id, body={'name': file_name}).execute()
    except:
        print('Could not place lock in gd')
def b_up(b_client,b_app_folder,file_name):
    try:
        stream = StringIO()
        stream.write(' ')
        stream.seek(0)
        try: # attempt to upload
            b_app_folder.upload_stream(stream,file_name) # box does not support chunked sdk yet
        except BoxAPIException as e : # upload failed, file exists , update content
            f_id=e.context_info['conflicts']['id']
            b_client.file(file_id=f_id).update_contents_with_stream(stream)  #without .methd , this is not a request 

    except:
        print('could not place lock in b')

## to be used by ensure only :
def db_check(dbx,file_name,q):
    try:
        results=dbx.files_list_folder('')
        counter=0
        # print (' db check cheking for ',file_name, ' and .lock in each of ::')
        for entry in results.entries:
            # print('         ',entry.name)
            if file_name in entry.name and '.lock' in entry.name:
                counter+=1
        if counter ==1 :
            q.put(True) 
        else:
            q.put (False)
    except:
        print (" could not 'ensure_onl_one' from db")
def gd_check(drive_service,app_folder,file_name,q):
    try:
        file_list = drive_service.files().list(q="name contains '"+file_name+"' and name contains '.lock' and trashed = false and '"+app_folder+"' in parents ").execute()
        if len (file_list['files']) == 1:
            q.put (True)
        else:
            q.put (False )
    except:
        print ("could not 'ensure_only_one' from gd")
def b_check (b_client,b_app_folder,file_name,q):
    try:
        file_list=b_app_folder.get_items(limit=200)
        counter=0
        for f in file_list:
            if file_name in f.name and '.lock' in f.name:
                counter+=1
        if counter == 1:
            q.put (True)
        else:
            q.put (False)
    except:
        print ("could not 'ensure_only_one' from b")

## to be used by ensure_newer_versionn
def db_version(dbx,file_name,q2):
   
    md_file_name=file_name+'_1.md.enc'
    #print('seeing this md '+md_file_name)
    try:
        encrypted_version=dbx.files_download('/'+md_file_name)[1].content
        decrypted_version=em.decrypt_(encrypted_version)
    except Exception as e:
        q2.put('nv')
        print ('could not verif version from db')
    else:
        print (' db chunk version is ',decrypted_version.decode('ascii'))
        q2.put (decrypted_version.decode('ascii'))
def gd_version (drive_service,app_folder,file_name,q2):
    
    md_file_name=file_name+'_2.md.enc'
    #print('this is what i am seeing '+md_file_name)
    try:
        files_list = drive_service.files().list(q=" name = '"+md_file_name+"' and trashed =false and '"+app_folder+"' in parents ").execute()
        encrypted_version = drive_service.files().get_media(fileId=files_list['files'][0]['id']).execute()
        decrypted_version=em.decrypt_(encrypted_version)
    except Exception as e:
        q2.put('nv')
        print('could not verify verison form gd')
    else:
        print (' gd chunk version is ',decrypted_version.decode('ascii'))
        q2.put (decrypted_version.decode('ascii'))
def b_version (b_client,b_app_folder,file_name,q2):
    try:
        md_file_name=file_name+'_3.md.enc'
        files=b_app_folder.get_items(limit=200)
        for file in files:
            if file.name==md_file_name:
                    encrypted_version=file.content()
                    decrypted_version=em.decrypt_(encrypted_version)
                    print (' B chunk version is ',decrypted_version.decode('ascii'))        
                    q2.put(decrypted_version.decode('ascii'))
                    return
        print('could not verif version from b')
        q2.put('nv')
    except:
        print('could not verif version from b')
        q2.put('nv')

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
    