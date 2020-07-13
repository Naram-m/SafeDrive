from fuse_python import Passthrough
import os
import sys
import errno
from collections import defaultdict
import time
from fuse import FUSE, FuseOSError, Operations
from stat import S_IFDIR, S_IFLNK, S_IFREG
import fileinput
import pickle
from anytree import Node, RenderTree, AsciiStyle, findall_by_attr, Resolver
import random
import collections
import copy
import shutil
import threading



## DB Imports:
from db_sync.db_logs import db_logs
from db_sync.db_fremove import db_fremove
from db_sync.db_lremove import db_lremove

# GD Imports:
from gd_sync.gd_logs import gd_logs

from gd_sync.gd_fremove import gd_fremove
from gd_sync.gd_lremove import gd_lremove

# ## Box Imports:
from b_sync.b_logs import b_logs
from b_sync.b_fremove import b_fremove
from b_sync.b_lremove import b_lremove



## encryption module import
from enc import encryption_module


class log_merger:

    home=os.path.expanduser('~')
    cloud_paths=[
    home+"/Desktop/Dropbox",
    home+"/Desktop/GoogleDrive",
    home+"/Desktop/Box",
    ]

    sessions_logs=defaultdict(list)
    sessions_logs_numbers=defaultdict(list)

    renaming_dict=collections.OrderedDict()

    accepted_rename_dict={}
    rejected_rename_dict={}

    log_no={}

    FSF=None

    def __init__(self,current_session,available_clouds):
        print("Log merger started ... ")
        self.available_clouds_names=[os.path.basename(x) for x in available_clouds]
        self.previously_down_cloud=''
        with open('./down_clouds.txt','r') as f:
            self.previously_down_cloud=f.read().strip() 
        
        self.r = Resolver('name')
        self.current_session=current_session
        
        ## TDC
        ## Synchronizers : 
        
        if 'Dropbox' in self.available_clouds_names:
            self.db_logs=db_logs(current_session)
        if 'GoogleDrive' in self.available_clouds_names:
            self.gd_logs=gd_logs(current_session)
        if 'Box' in self.available_clouds_names:   
            self.b_logs=b_logs(current_session)

        ##TDC
        ## download FSF from first available cloud

        if self.available_clouds_names[0] =='Dropbox' and self.previously_down_cloud !='Dropbox':
            self.db_logs.download_FSF()
        elif self.available_clouds_names[0] =='GoogleDrive' and self.previously_down_cloud !='GoogleDrive':
            self.gd_logs.download_FSF()
        elif self.available_clouds_names[0] =='Box' and self.previously_down_cloud !='Box':
            self.b_logs.download_FSF()
        
        print("Downloaded FSF ")
        self.em=encryption_module()
        
        ##TDC
        #downloaded_FSF_cloud=self.cloud_paths[0] # used in decrypt_downloaded_FSF and fsf_path variable
        downloaded_FSF_cloud=available_clouds[0]
        self.decrypt_downloaded_FSF(downloaded_FSF_cloud)


        fsf_path=downloaded_FSF_cloud+'/FSFolder/FSF'
        try:
            fsf=open (fsf_path,"rb")
        except Exception as e:

            print("could not open fsf:",e)
            self.FSF=None
            pass
        else:
            self.FSF=pickle.load(fsf)
            fsf.close()

    ##DCT

    def download_logs (self):
        ## TODO, pick first available cloud
        #self.first_available_cloud=0 #0: for now this is an assumption

        if 'Dropbox' in self.available_clouds_names and self.previously_down_cloud !='Dropbox':
            self.first_available_cloud=0
        elif 'GoogleDrive' in self.available_clouds_names and self.previously_down_cloud !='GoogleDrive':
            self.first_available_cloud=1
        elif 'Box' in self.available_clouds_names and self.previously_down_cloud !='Box':
            self.first_available_cloud=2

        if self.first_available_cloud ==0:
            pass
            self.my_sessions=self.listdir_nohidden_logs_sessions(self.cloud_paths[0]+'/FSFolder/')
            self.db_logs.download_others_logs()

        elif self.first_available_cloud==1:
            pass
            ## before ..
            self.my_sessions=self.listdir_nohidden_logs_sessions(self.cloud_paths[1]+'/FSFolder/')
            self.gd_logs.download_others_logs()

        
        elif self.first_available_cloud==2:          
            self.my_sessions=self.listdir_nohidden_logs_sessions(self.cloud_paths[2]+'/FSFolder')
            self.b_logs.download_others_logs()


        print("downloaded encrypted logs ")

        self.decrypt_downloaded_logs() # pass current session
        #print("downloading logs from gd finished")
        #time.sleep(5)

    def decrypt_downloaded_logs(self):
        '''
        this method checks for all logs sessions folder and decrypt the content of them (log files)
        '''
        cloud=self.cloud_paths[self.first_available_cloud] #decrypt only downloaded ones
        aug_cloud=cloud+'/FSFolder/'
        for sub_folder in self.listdir_nohidden(aug_cloud):
            if 'log' in sub_folder and sub_folder!= self.current_session:
                for encrypted_log_file in self.listdir_nohidden(aug_cloud+sub_folder):
                    if '.enc' in encrypted_log_file:
                        path_to_encrypted_log_file=aug_cloud+sub_folder+'/'+encrypted_log_file
                        #print("this is path to encrypted log file",path_to_encrypted_log_file)
                        path_to_log_file=path_to_encrypted_log_file[0:path_to_encrypted_log_file.find('.enc')] 
                        #print("this is path to  log file",path_to_log_file)
                        with open (path_to_encrypted_log_file,'rb') as from_:
                            with open (path_to_log_file,'wb') as to_:
                                to_.write(self.em.decrypt_(from_.read()))
                        os.remove(path_to_encrypted_log_file)
                    else:
                        pass # already decrypted
    
    def decrypt_downloaded_FSF(self, cloud):
        pass
        try:
            # order is important
            with open (cloud+'/FSFolder/FSF.enc','rb') as f2:
                # print(' FSF.enc opened for reading')
                with open (cloud+'/FSFolder/FSF','wb') as f:
                    # print(' FSF opened for writing')
                    f.write(self.em.decrypt_(f2.read()))
        except Exception as e :
            print('no encrypted fsf found... :',e)

    def read_logs (self):
        '''this method forms self.sessions_logs which is a dictionary from a log session to all logs inside it,
        it uses the variable first available cloud to read the logs from a the local folder of this cloud, because
        the xx_logs would have downloaded the logs there .. (and they were decrypted by the decrypt_downloaded logs )
        '''

        self.download_logs()
        self.decrypt_downloaded_logs()

        cc=self.cloud_paths[self.first_available_cloud] ## chosen cloud

        aug_cloud=cc+'/FSFolder'
        for log_session in self.listdir_nohidden (aug_cloud):
            if log_session.find('log') >= 0 : # indeed is a log session folder
                #self.sessions_logs[log_session]=[]
                ## following loop iterates through sorted logs , 1 ,2 ,3 ..etc
                for _log in sorted(self.listdir_nohidden(aug_cloud+'/'+log_session),key=lambda _log: int(_log)):
                    with open (aug_cloud+'/'+log_session+'/'+_log,"r") as f:
                        read_line=f.readline().strip()
                        self.sessions_logs[log_session].append(read_line)

                        self.sessions_logs_numbers[log_session].append(_log)

    def adjust_log_entry(self,log_entry):
        le=log_entry
        for k,v in self.accepted_rename_dict.items():
            le=le.replace(k,v)

        for k,v in self.rejected_rename_dict.items():
            le=le.replace(k,v)

        return le

    def process_logs(self):

        for log_session in self.sessions_logs.keys():
            print("Incorporating Log Session: ",log_session)
            self.rejected_rename_dict={}
            #print ("sorted logs inside : ",self.sessions_logs[log_session])

            for log_entry,log_no in zip( self.sessions_logs[log_session] , self.sessions_logs_numbers[log_session]):
                print ("this is log entry ",log_entry)
                
                # print ('\n\nsleeping...\n')

                # time.sleep(30)
                
                #print("adjusting lof entry...:")
                log_entry=self.adjust_log_entry(log_entry)

                tokens=log_entry.split(',')
                # operation=self.adjust_path(tokens[0]) # adjust here or befor accessing the tree
                # operand_1=self.adjust_path(tokens[1]) #
                operation=tokens[0] # adjust here or befor accessing the tree
                operand_1=tokens[1] #

                try:
                    operand_2=tokens[2]# same as opernad 1 but for renames
                except:
                    operand_2=''
                    pass

                affected_node_path= operand_1[0:operand_1.rfind('/')]   # if log is update a/b/c/d , anp is a/b/c and

                affected_node_for_r=affected_node_path[1:]

                affected_node_object=self.r.get(self.FSF,affected_node_for_r)

                #print ("entering loop with this ",affected_node_path)

                node_1= operand_1[operand_1.rfind('/'):]                  # node is name
                node_2=operand_2[operand_1.rfind('/'):]

                path_to_node= operand_1[1:] #path to node itself

                if path_to_node[0] =='/':
                    path_to_node=path_to_node[1:]

                if operation == 'unlink':
                    # if not self.unlink_conflict_exists(log_session,operand_2): # maybe ?  v2

                    if not self.unlink_conflict_exists(log_session,operand_1): # no conflicts
                        #pn_to_remove=self.r.get(self.FSF,path_to_node)._physical_name
                        self.r.get(self.FSF,path_to_node).parent=None
                        
                        self.remove_parts(operand_2)

                        a=db_fremove('/'+operand_2+'_1.enc') # < expects path in db
                        a=db_fremove('/'+operand_2+'_1.md.enc') # < expects path in db

                        #b=gd_fremove(operand_2)

                elif operation == 'rmdir': # rmdir could not have been possible
                        self.r.get(self.FSF,path_to_node).parent=None

                elif operation == 'create':
                    _name=node_1[1:]
                    a_node=Node(_name, parent = affected_node_object, _type="file",_version='v0')
                    self.r.get(self.FSF,path_to_node)._physical_name=operand_2

                elif operation == 'update':
                    self.r.get(self.FSF,path_to_node)._version='v'+str(int(self.r.get(self.FSF,path_to_node)._version.split('v')[1])+1)

                elif operation == 'mkdir':
                    _name=node_1[1:]
                    a_node=Node(_name, parent = affected_node_object, _type="dir")

                elif operation == 'rename': ##3 possibilities , 1+2 -> no conflict TODO later
                    print("")
                    if not self.rename_conflict_exists(log_session,operand_1,operand_2):
                        print ("!!  HERE , new name should be :",operand_2[operand_2.rfind('/')+1:])
                        self.r.get(self.FSF,path_to_node).name=operand_2[operand_2.rfind('/')+1:]
                        self.accepted_rename_dict[operand_1]=operand_2

                    else:
                        print ("adding this to rejected ",operand_1,"     ",operand_2)
                        self.rejected_rename_dict[operand_2]=operand_1


                    print("")

                elif operation == 'move_rename':
                    if not self.move_loop_conflict_exists(log_session,operand_1,operand_2) and not self.move_conflict_exists(log_session,operand_1,operand_2):
                        _from=path_to_node
                        node=self.r.get(self.FSF,path_to_node)
                        new_parent=self.r.get(self.FSF,operand_2[1:operand_2.rfind('/')])
                        node.parent=new_parent

                        self.accepted_rename_dict[operand_1]=operand_2

                    else:
                        self.rejected_rename_dict[operand_2]=operand_1

                print("removing this incorporated log: ",log_session+'/'+log_no)

                self.remove_log('/FSFolder/'+log_session+'/'+log_no,False)
            self.remove_log('/FSFolder/'+log_session,True) ## to remove log folder.
        
        self.write_FSF()

    def write_FSF(self):

        
        print ("Writing the FSF again: ")
        for cloud in self.cloud_paths:
            fpath=cloud+'/FSFolder/FSF'
            fsf = open (fpath,'wb')
            pickle.dump(self.FSF, fsf)
            
            try:
                with open (fpath,'rb') as fsf:
                    with open (fpath+'.enc','wb') as fsfe:
                        fsfe.write(self.em.encrypt_(fsf.read()))
            except Exception as e:
                print ('ERR : ',e)



        ##TDC

        if 'Dropbox' in self.available_clouds_names:
            db_fsf_path=self.cloud_paths[0]+'/FSFolder/FSF.enc'
            self.db_logs.write_FSF_again(db_fsf_path)
       
        if 'GoogleDrive' in self.available_clouds_names:
            gd_fsf_path=self.cloud_paths[1]+'/FSFolder/FSF.enc'
            self.gd_logs.write_FSF_again(gd_fsf_path)
      
        if 'Box' in self.available_clouds_names:
            b_fsf_path=self.cloud_paths[2]+'/FSFolder/FSF.enc'
            self.b_logs.write_FSF_again(b_fsf_path)

    def remove_log (self,fpath,isLogFolder=False):
        for cp in self.cloud_paths:
            try:
                if isLogFolder:
                    os.rmdir(cp+fpath)
                else:
                    os.remove(cp+fpath)
            except OSError:
                pass
                print('.')
                #print("could not delete ",cp+fpath+'..might not exist locally')

        ## TDC
        a=None
        b=None
        c=None

        if 'Dropbox' in self.available_clouds_names:
            a=db_lremove(fpath,isLogFolder) 
            a.start()
        if 'GoogleDrive' in self.available_clouds_names:
            b=gd_lremove(fpath,isLogFolder)
            b.start()
        if 'Box' in self.available_clouds_names:   
            c=b_lremove(fpath,isLogFolder)
            c.start()

        if a: 
            a.join()
        if b:
            b.join()
        if c:
            c.join()
    
    def listdir_nohidden(self,path):
        for f in os.listdir(path):
            if not f.startswith('.'):
                yield f

    def unlink_conflict_exists(self,p_log_session,path):
        name=path[path.rfind('/'):]
        unlinked_node=self.r.get(self.FSF,path[1:])
        unlinked_node_pn=unlinked_node._physical_name
        for session,_logs in self.sessions_logs.items():
            if session != p_log_session: ## search for edits only in other sessions !
                for _log in _logs:
                    log_tokens=_log.split(',')
                    if log_tokens[0]=='update':
                        updated_node_pn=log_tokens[2]
                        if updated_node_pn==unlinked_node_pn:
                            print ("!! Cought an unlink/update conflict")
                            return True
        return False

    def rename_conflict_exists(self,p_log_session,old_path,new_path):
        #name=path[path.rfind('/'):]
        for session,_logs in self.sessions_logs.items():
            if session != p_log_session: ## search for edits only in other sessions !
                for _log in _logs:
                    log_tokens=_log.split(',')
                    if log_tokens[0]=='rename' and log_tokens[1] == old_path :
                        print ("!! Cought an frename/frename conflict")
                        return True
        return False

    def move_conflict_exists(self,p_log_session,old_path,new_path):
        #name=path[path.rfind('/'):]
        for session,_logs in self.sessions_logs.items():
            if session != p_log_session: ## search for edits only in other sessions !
                for _log in _logs:
                    log_tokens=_log.split(',')
                    if log_tokens[0]=='move_rename' and log_tokens[1] == old_path :
                        print ("!! Cought an move/move conflict")
                        return True
        return False

    def get_parts_paths(self,path):
        if path.find('.') >=0:
            file_name_without_extension=path[path.rfind('/')+1:path.rfind('.')]
            dot_extension=path[path.rfind('.'):]

            part_files=[]
            for i in range (0,len(self.cloud_paths)):
                part_files.append(self.cloud_paths[i]+'/'+file_name_without_extension+'_'+str(i+1)+dot_extension)

            return part_files
        else:
            file_name=path[path.rfind('/')+1:]
            part_files=[]
            for i in range (0,len(self.cloud_paths)):
                part_files.append(self.cloud_paths[i]+'/'+file_name+'_'+str(i+1))
            return part_files

    def remove_parts(self,pn):
        i=0
        for part_file in self.get_parts_paths(pn):
            try:
                #print("removing this ",part_file)
                os.unlink(part_file)
                os.unlink(part_file+".md")
            except Exception as e :
                print(part_file,"  already removed:"+ str(e))
            i+=1

    def move_loop_conflict_exists(self,p_log_session,operand_1,operand_2): # A , B
        for session,_logs in self.sessions_logs.items():
            if session != p_log_session: ## search for edits only in other sessions !
                for _log in _logs:
                    if _log.find('move_rename') >=0:
                        tokens=_log.split(',')
                        nA=tokens[1]
                        nB=tokens[2]
                        for ancestor in self.get_ancestors_list(operand_2):
                            if nA == ancestor and operand_1 in nB:
                                print("!! Cought type_2 moving conflict")
                                return True
        return False

    def get_ancestors_list(self,B):
        tokens=B.split('/')
        prev=''
        i=0
        list_of_ancestors_fullpaths=[]
        for item in tokens:
            list_of_ancestors_fullpaths.append(prev+'/'+item)
            if i==0:
                prev=prev+item
            else:
                prev=prev+'/'+item
            i+=1
        return list_of_ancestors_fullpaths

    def listdir_nohidden_logs_sessions(self,path):
        a=[]
        for f in os.listdir(path):
            if not f.startswith('.') and 'log' in f:
                a.append(f)
        return a