from fuse_python import Passthrough
import os
import sys
import errno
from collections import defaultdict
from time import time
from fuse import FUSE, FuseOSError, Operations
from stat import S_IFDIR, S_IFLNK, S_IFREG
from time import time
import fileinput
import pickle
from anytree import Node, RenderTree, AsciiStyle, findall_by_attr, Resolver
import random
import collections
import copy
import shutil
from db_sync.db_uploader import db_uploader
from gd_sync.gd_uploader import gd_uploader
from b_sync.b_uploader import b_uploader
from enc import encryption_module

class log_fixer:

## for lftesting:
    # cloud_paths=[
    # "/home/parallels/Desktop/DropboxT",
    # "/home/parallels/Desktop/GoogleDriveT",
    # "/home/parallels/Desktop/BoxT",
    # ]

    home=os.path.expanduser('~')
    cloud_paths=[
    home+"/Desktop/Dropbox",
    home+"/Desktop/GoogleDrive",
    home+"/Desktop/Box",
    ]

    session=''

    def __init__(self,session,new_FSF,old_FSF,db_cm=None,gd_cm=None,b_cm=None):
        self.session=session
        self.new_FSF=new_FSF
        self.old_FSF=old_FSF
        self.log_session=session
        self.em=encryption_module()

        self.logs=[]
        self.logs_numbers=[]

        self.r = Resolver('name')

        ## those are necessary for the uploads only
        self.db_cm=db_cm
        self.gd_cm=gd_cm
        self.b_cm=b_cm

        self.log_no={}

    def create_special_dir(self):
        try:
            a_node=self.r.get(self.new_FSF,"Special_Directory")
        except:
            print("creating sd for the first time")

            a_node=Node("Special_Directory", parent = self.new_FSF, _type="dir")

            ## TODO needs fixing, loop over all cloud, this is also true for log registrations below 
            self.register_log('mkdir',path_1="/Special_Directory",log_id=0,log_folder=self.session)

        return a_node

    def read_logs (self):
        _dir=0
        cc=self.cloud_paths[_dir] ## chosen cloud
        
        self.aug_cloud=cc+'/FSFolder/'+self.session
        if not os.path.exists(self.aug_cloud):
            # the running cm accepted the deletion, no dangling log 
            return
        for _log in sorted(self.listdir_nohidden(self.aug_cloud),key=lambda _log: int(_log)):
            with open (self.aug_cloud+'/'+_log,"r") as f:
                #print ('opened this ',self.aug_cloud+'/'+_log)
                read_line=f.readline().strip()
                self.logs.append(read_line)
                self.logs_numbers.append(_log)

                #self.log_no[read_line]=_log # from log content to log number

    def fix_logs(self):
        self.read_logs()
        print (len(self.logs))
        for _log,_log_no in zip(self.logs,self.logs_numbers):
            log_tokens=_log.split(',')
            operand_1=log_tokens[1]
            try:
                operand_2=log_tokens[2]
            except:
                operand_2=''

            if log_tokens[0]=='update':
                try:
                    updated_pn=operand_2
                    upadted_node=findall_by_attr(self.new_FSF,updated_pn,"_physical_name")[0]
                    print ('this is the node ..',upadted_node)
                    upadted_node._version='v'+str(int(upadted_node._version.split('v')[1])+1)

                except: # the node is deleted from the new view 
                   
                    ## reset md first
                    print ('Recovering a file ...')
                    for part_ in self.get_parts_paths(operand_2):
                        fdm= open(part_+".md", 'w+')
                        fdm.write("v0")

                    ## then re upload parts
                    self.encrypt(operand_2)
                    self.upload_to_clouds(operand_2)

                    log_no=_log_no                    
                    ## create the representing node : 
                    sd=self.create_special_dir()
                    _n=operand_1[operand_1.rfind('/')+1:]
                    a_node=Node(_n, parent = sd, _type="file",_physical_name=operand_2)
                   
                    ## log the creation of representing node, (overwrite the update )
                    self.register_log('create',path_1="/Special_Directory/"+_n,path_2=updated_pn,log_id=log_no,log_folder=self.session)

                           
        return self.new_FSF

    def get_path_as_string(self,tuple):
        s=""
        for t in tuple:
            s=s+'/'+t.name
        s=s.replace('/root',"")
        return s

    def listdir_nohidden(self,path):
        for f in os.listdir(path):
            if not f.startswith('.'):
                yield f

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

    # if a log is edited within this program, the following method should be called to update that log,
    # if a log is left untouched, then no need to encrypt and upload since these logs would have already been
    # uploaded when the were created.
    

    def upload_to_clouds(self,pn):
        ###############################################
        ########################################### Dropbox ##############################################
        p1_path_relative_to_os=self.get_parts_paths(pn)[0]+'.enc'
        p1_md_path_relative_to_os=self.get_parts_paths(pn)[0]+'.md.enc'
        
        fname1=p1_path_relative_to_os[p1_path_relative_to_os.rfind('/'):]
        fname1_md=p1_md_path_relative_to_os[p1_path_relative_to_os.rfind('/'):]
        
        p1=db_uploader(p1_path_relative_to_os,fname1,self.db_cm,upload_md=True)
        p1.start()
        
        # p1_md=db_uploader(p1_md_path_relative_to_os,fname1_md,self.db_cm)
        # p1_md.start()
        #################################################################################################

        ########################################### Google Drive ########################################
        p2_path_relative_to_os=self.get_parts_paths(pn)[1]+'.enc'
        p2_md_path_relative_to_os=self.get_parts_paths(pn)[1]+'.md.enc'

        fname2=p2_path_relative_to_os[p2_path_relative_to_os.rfind('/'):]
        fname2_md=p2_md_path_relative_to_os[p2_path_relative_to_os.rfind('/'):]

        p2=gd_uploader(p2_path_relative_to_os,gd_cm=self.gd_cm,upload_md=True)
        p2.start()

        # p2_md=gd_uploader(p2_md_path_relative_to_os,gd_cm=self.gd_cm)
        # p2_md.start()

        ################################################## Box ###############################################
        p3_path_relative_to_os=self.get_parts_paths(pn)[2]+'.enc'
        p3_md_path_relative_to_os=self.get_parts_paths(pn)[2]+'.md.enc'

        p3=b_uploader(p3_path_relative_to_os,self.b_cm,upload_md=True)
        p3.start()
        # p3_md=b_uploader(p3_md_path_relative_to_os,self.b_cm)
        # p3_md.start()

        return

    def register_log(self,operation,path_1='',path_2='',_physical_name='',log_id=-1,log_folder=''):
        if log_id ==-1 or not log_folder:
            raise Exception (' error form du ')
                   
        log_content=operation+','+path_1
        if path_2!='': # path 2 is present
            log_content=log_content+','+path_2
        if _physical_name!='':
            log_content=log_content+','+_physical_name

        for cloud in self.cloud_paths:
            if not os.path.exists(cloud+'/FSFolder/'+log_folder):
                os.mkdir(cloud+'/FSFolder/'+log_folder)
                print('recreated a deleted session folder to continue this session')
            
            with open (cloud+'/FSFolder/'+log_folder+'/'+str(log_id),'w') as f:
                f.write(log_content)
            with open (cloud+'/FSFolder/'+log_folder+'/'+str(log_id)+'.enc','wb') as f:
                f.write(self.em.encrypt_(bytes(log_content,'utf-8')))


        _src=self.cloud_paths[0]+'/FSFolder/'+log_folder+'/'+str(log_id)+'.enc'
        _src2=self.cloud_paths[1]+'/FSFolder/'+log_folder+'/'+str(log_id)+'.enc'
        _src3=self.cloud_paths[2]+'/FSFolder/'+log_folder+'/'+str(log_id)+'.enc'

        _dst='/FSFolder/'+log_folder+'/'+str(log_id)+'.enc'

        a=db_uploader(_src,_dst,self.db_cm,is_log=True)
        a.start()

        b=gd_uploader(_src2,self.gd_cm,is_log=True)
        b.start()

        c=b_uploader(_src3,self.b_cm,is_log=True)
        c.start()

    def encrypt (self,pn):
        trans_size=500 *1024 *104
        for f in self.get_parts_paths(pn):
            with open(f,"rb") as fileobjectFrom:
                with open(f+'.enc',"wb") as encFileobjectTo:
                    _by_s=fileobjectFrom.read(trans_size)
                    encFileobjectTo.write(self.em.encrypt_(_by_s))
                    while len(_by_s) == trans_size:
                        _by_s=fileobjectFrom.read(trans_size)
                        encFileobjectTo.write(self.em.encrypt_(_by_s))

        for f in self.get_parts_paths(pn):
            af=f+'.md'
            with open(af,"rb") as fileobjectFrom:
                with open(af+'.enc',"wb") as encFileobjectTo:
                    encFileobjectTo.write(self.em.encrypt_(fileobjectFrom.read()))


