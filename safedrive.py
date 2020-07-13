import reliability_startup
#####################################################################################################################


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
import errno
import copy


import shutil
from lm import log_merger

from collections import Counter
import gc, sys
import math
from c import coding
import collections
import argparse
from enc import encryption_module
from SSSA import sssa


# DB SYNC
from db_sync.db_uploader import db_uploader
from db_sync.db_cm import db_cm
from db_sync.db_start import db_start

## GD SYNC

from gd_sync.gd_uploader import gd_uploader
from gd_sync.gd_cm import gd_cm
from gd_sync.gd_start import gd_start

## Box SYNC
from b_sync.b_uploader import b_uploader
from b_sync.b_cm import b_cm
from b_sync.b_start import b_start


from string import ascii_uppercase
from string import ascii_lowercase
from random import choice
from du import log_fixer
import threading

from data_locking_2 import get_write_permission
from data_locking_2 import remove_locks

#######################################################################################################################################


class RSCFS (Passthrough):
    files=[]
    mfiles=[]
    dirs=[]
    parent={}
    flush_after_write=False
    tree=None
    reinitialization_lock=threading.Lock()

    home=os.path.expanduser('~')
    cloud_paths=[
    home+"/Desktop/Dropbox",
    home+"/Desktop/GoogleDrive",
    home+"/Desktop/Box",
    ]

    data = defaultdict(bytearray)
    fd = 0
    log_folder=''

    def __init__ (self):
        ## timer variable for experiments 
        self.start_time=0

        ## first thing we should check cloud availability to determine which ones are working.
        self.available_clouds=reliability_startup.available_clouds
     
        ### end reliability start part ....

        self.em=encryption_module(self.available_clouds)
        self.swp_hidd_pn={}
        self.sem = threading.Semaphore()
        self.uploaded_from_client=[]
        
        self.release_after_flush=False
        self.release_after_read=False
        self.release_after_overwrite=False

        ## 1- Initialize variables
        #print("\n\n in init rit now")
        now = time.time()
        self.conflicted_copies_dict={}
        self._adjust=0
        self.parts_info={}
        self.sc_to_host_temp=''
        self.parts_info_available=collections.OrderedDict()
        self.orig_dir_name={}
        self.files = {}
        self.read_version={}
        self.files['/'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now,
                               st_mtime=now, st_atime=now, st_nlink=2,st_size=100000)
        self.file_rename=False
        self.fd=0
        self.data = defaultdict(bytearray)
        self.tree = Node("root",_type="dir")
        self.r = Resolver('name')
        self.log_id=0;
        s_n=random.randrange(100)
        self.log_folder='log'+str(s_n);
        self.cc='session_'+str(s_n);

        ##2- load FSF into memory
        self.initialize_tree()

        ## 2- create a log session
        for cloud in self.cloud_paths:
            directory=cloud+'/FSFolder/'+self.log_folder
            if not os.path.exists(directory):
                os.makedirs(directory)


        ## $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

        available_clouds_names=[os.path.basename(x) for x in self.available_clouds]

        # self.db_cm=None
        # self.gd_cm=None
        # self.b_cm=None
        self.db_cm=db_cm(self)
        self.gd_cm=gd_cm(self)
        self.b_cm=b_cm(self)
        if 'Dropbox' in available_clouds_names:
            print("Starting DB Cloud Monitor ")
            
            self.db_cm.start()
            print("Starting DB Start")
            dbs=db_start(db_cm=self.db_cm)
            dbs.start()
            dbs.join()

        if 'GoogleDrive' in available_clouds_names:

            print("Starting GD Cloud Monitor ")
            
            self.gd_cm.start()

            print("Starting GD Start")
            gds=gd_start(gd_cm=self.gd_cm)
            gds.start()
            gds.join()

        if 'Box' in available_clouds_names:

            print("Starting Box Cloud Monitor ")
            
            self.b_cm.start()

            print("Starting Box Start ")
            bs=self.b_start=b_start(b_cm=self.b_cm)
            bs.start()
            bs.join()
        

        #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
        super().__init__()

        open ('./db_sync.log','w').close()
        open ('./gd_sync.log','w').close()
        open ('./b_sync.log','w').close()
        print ('\nSafeDrive Ready ....')



    def initialize_tree(self):
        '''
        method to load FSF into memory for manipulation

        -if there is no FSF file, creates one on each cloud.
        -call the log merger to manipulate the existing FSF
        -load the FSF
        '''
        found = False
        for cloud in self.cloud_paths:
            fs_cloud=cloud+'/FSFolder/FSF'
            try:
                fsf=open (fs_cloud,"rb")
            except:
                pass
            else:
                found=True
                break

        if not found:
            #print(" FSF not found on any of the clouds, initializing ...")
            self.tree=Node("root",_type="dir")
            for cloud in self.cloud_paths:
                fs_cloud=cloud+'/FSFolder/FSF'
                fsf= open(fs_cloud,"wb+")
                pickle.dump(self.tree, fsf)
                fsf.close()

        print("Calling merger------------------------------------------------------------------------------------")
        ## ensure only on elog merger 


        ## when simulating data conflicts for experiment, make a directly true ( comment the get permission file)
        a=get_write_permission(name='log_merger_'+self.cc,version_to_be_written=1)
        #a=True
        if not a:
            remove_locks(name='log_merger_'+self.cc,cloud='all')
            print ('Another log merger is currently operating, please try to start the system again')
            sys.exit()
        
        print('ensured the only merger')
        a=log_merger(self.log_folder,self.available_clouds)
        a.read_logs()
        a.process_logs()


        remove_locks(name='log_merger_'+self.cc,cloud='all')
        open('./down_clouds.txt','w').close()
        print("Finshed  merger------------------------------------------------------------------------------------\n\n\n")
        self.delete_local_data()
        ###
        fsf= open(self.cloud_paths[0]+'/FSFolder/FSF',"rb")
        self.tree=pickle.load(fsf)

    def get_current_version (self,path):
        '''
        gets the vresion of the part specified by
        'path' from its associated md file
        '''
        #path_with_physical_name=self.r.get(self.tree,path[1:])._physical_name
        # path already passed as physical name
        try:
            #print ('trying to get the verison of this ',path)
            with open(path+'.md') as f:
                version=f.readline().strip()
                versionint=int(version.split('v')[1])
                f.close()######################################?????????????? ea will it work 
            #print ('returning ',versionint)
            return versionint
        except:
            #print("failed to get a part's version")
            return -1
            
    def readdir(self, path, fh):
        '''
        get the children names of a node in the tree,
        -if path is root, the node in the tree is 'root'
        -otherwise, use the tree's resolver 'r' to retrive
            the node
        '''

        #print ("!!!!!acquiring from readdir")
        self.sem.acquire()

        dirents = ['.','..']
        #print("\nreaddir on this :",path)
        if path=='/':
            nd=findall_by_attr(self.tree, 'root')[0]
        else:
            nd=self.r.get(self.tree,path[1:])

        for child in nd.children:
            dirents.append(child.name)
            #self.check_rebuild_32(path+'/'+child.name,self.get_parts_paths(self.r.get(path[1:]+'/'+child.name)._physical_name))
        
        for r in dirents:
            yield r

        self.sem.release()

    def getattr(self,path,fh=None):
        '''
        gets information about a file or a directory
        '''
        obtain_attr=False
        swpf=False
        hiddf=False

        #print("getattr on ",path)
        ## root directory, put the suitable attributes
        if path == '/' :
            tdict={}
            tdict['st_atime']=time.time() # same as mounting time
            tdict['st_ctime']=time.time() # same as mounting time
            tdict['st_gid']=os.getgid()
            tdict['st_mode']=(S_IFDIR | 0o755) # set mode bits with permissions
            tdict['st_mtime']=time.time()
            tdict['st_nlink']=2 #should be 2
            tdict['st_size']=0
            tdict['st_uid']=os.getuid() #

            return tdict ; # return the information directory about the root

        try: # not a root, try to retreive the file/dir from the tree
            self.r.get(self.tree,path[1:])

        except: # not on tree, either not existing or swp or hidden
            #print ("INSIDE EXCPTIOPN")
            if path.find("swp")>0: # swp
                obtain_attr=True;
                swpf=True
            elif path[path.rfind('/')+1:][0]=='.': # hidden
                obtain_attr=True;
                hiddf=True

            else:  # non existing
                obtain_attr=False

                # this method will return appropiriate value for the caller to realize that a dir do not exist
                st = os.lstat(path)
        else: # no exceptio, the file is present
            obtain_attr=True

        if obtain_attr: # opbtaining the attributes of a file or a directory 
            total_size=0
            if swpf or hiddf or self.r.get(self.tree,path[1:])._type == "file" : # it can be found and it is a file
                if swpf or hiddf:
                    p_f=self.swp_hidd_pn.get(path)
                    if p_f == None:
                        st=os.lstat(path)
                    else:
                        parts_paths=self.get_parts_paths(p_f)

                elif self.r.get(self.tree,path[1:])._type == "file" :
                    #print ("this is the node now :",self.r.get(self.tree,path[1:]))
                    parts_paths=self.get_parts_paths(self.r.get(self.tree,path[1:])._physical_name)
                
                    # print ("before check rebuild")
                    # self.check_rebuild_32(path,parts_paths)
                    # print('after check rebuild')
                
                    rv=self.check_rebuild_32(path,parts_paths)

                i=1
                if len(self.cloud_paths) == 3: # special for 32 , getting the size and the other attr
                    ## getting the size from only two parts
                    i=0
                    st=None
                    for part_file in parts_paths:
                            try:
                                st=os.lstat(part_file)
                            except:
                                pass
                            else:
                                i+=1
                                total_size+=getattr(st, 'st_size')
                            if i==2:
                                break

                    ## take an st "picture" for other attrs

                for part_file in parts_paths:
                    try:
                        st=os.lstat(part_file)
                    except:
                        pass
                    else:
                        break

                if st == None: ## st is still none, should use lstat t oraise the exception to indicate teh file does not exists
                    #print ("ST IS STILL NONE")
                    st=os.lstat(part_file)
                dictf={}
                for key in ('st_atime', 'st_ctime','st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'):
                    if key == "st_size":
                        dictf[key]=total_size
                    else:
                        try:
                            dictf[key]=getattr(st, key)
                        except:
                            pass
                return dictf # attributes of a file are all same as any part file, except the size which is the sum

            else: # directory, insert the values

                tdict={}
                if (self.r.get(self.tree,path[1:])!=None):
                    tdict['st_atime']=time.time()
                    tdict['st_ctime']=time.time()
                    tdict['st_gid']=0
                    tdict['st_mode']=(S_IFDIR | 0o755)
                    tdict['st_mtime']=time.time()
                    tdict['st_nlink']=2
                    tdict['st_size']=0
                    tdict['st_uid']=0
                    return tdict ;

                else:
                    # this call will return appropiriate value for the caller to realize that a file/dir do not exist
                    st = os.lstat(path)

    def open(self, path, flags):
        '''
        return an integer t orepresent a file descriptor
        -should be unique, per session
        '''
        self.fd=self.fd+1
        return self.fd;

    def release(self, path, fh):
        '''
        release should free a file descriptor so that it can be used again,
        since the file descriptors (returned by open methods) are always increaseing by 1,
        then directly return 0. Note: no resources to be freed
        '''

        print(">>Release",path, fh)
        if self.release_after_flush:
            #print("Release after flush")
            cc_path=self.conflicted_copies_dict.get(path)
            if cc_path:
                print ('adjusting release path')
                self.upload_to_clouds(self.r.get(self.tree,cc_path[1:])._physical_name)
                self.conflicted_copies_dict.pop(path)
            else:
                self.upload_to_clouds(self.r.get(self.tree,path[1:])._physical_name)
            self.release_after_flush=False

        if self.release_after_read:
            print("Release after read")
            self.release_after_read=False

        if self.release_after_overwrite:
            print("Release after overwrite")

            self.release_after_overwrite=False
    
            self.upload_to_clouds(self.r.get(self.tree,path[1:])._physical_name)


        return (0)

    def read(self, path, length, offset, fh):
        '''
        this method shoud return bytes  [offset, offset+length] from
        the distributed parts through the indicated steps
        '''

        if path.find('swp') >= 0 or path[path.rfind('/')+1:][0]=='.':
            is_swp_hidd=True
        else:
            is_swp_hidd=False


        print(">>Read",path,length,offset,"\n")
        if is_swp_hidd:
            parts_paths=self.get_parts_paths(self.swp_hidd_pn[path])
        else:
            parts_paths=self.get_parts_paths(self.r.get(self.tree,path[1:])._physical_name)
        # rv=self.check_rebuild_32(path,parts_paths)

        ## 1- get parts info if not present. parts info is dictionary from: part number to: included bytes
        ## getting parts infor is dependent on the coding method
        if self.parts_info_available.get(path) == None or True :
            part = 1
            ll=0
            self.parts_info_available[path]={}

            parts_info = self.parts_info_available.get(path) # by reference
            adjusted_part_paths=parts_paths # not necessary

            if len(self.cloud_paths) == 3: # specifict to 32 coding
                adjusted_part_paths=[parts_paths[0],parts_paths[1]]
                # if not rv:
                #     print("should raise an error here")
                #     #raise OSError()

            for part_path in adjusted_part_paths:
                part_size=os.stat(part_path).st_size
                # print("             this is part :",part_path)
                # print ("            this is size: ",part_size)
                parts_info[part]=[ll,ll+part_size] # to be both limits inclusive
                #print("assiging this part ",part)
                part+=1
                ll+=part_size
            # print("\n-----------------Parts Info------------------------\n")
            # print(parts_info)
            # print("\n--------------------------------------------------\n")

        else:
            parts_info = self.parts_info_available.get(path)

            # print("\n-----------------Parts Info------------------------\n")
            # print(parts_info)
            # print("\n--------------------------------------------------\n")
            #

        ##$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##

        ##$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##
        ## 2- get involved parts. involved parts is a dictionary between the part number that includes (part of) requested data
        ## and the range [x,y] that this part includes
        inital_part=1
        involved_parts={}
        ll= offset
        upper_limit_of_last_part=(parts_info[list(parts_info.keys())[-1]][1])

        if (offset+length) <= upper_limit_of_last_part: # required piece less than (upper limit of last part in parts_info)
            #print("offset+length ",offset+length ,"smaller than size ", upper_limit_of_last_part,"ok")
            ul=offset+length
        else:
            #print("offset+length ",offset+length ,"bigger than size ", upper_limit_of_last_part,"trimmed")
            ul=upper_limit_of_last_part


        involved_in_multiple_parts= False

        for part, limits in parts_info.items():
            #print("THIS IS PARTS ",part)
            #print("THIS IS LIMITS ",limits)
            if ll >= limits[0] and ll <= limits[1]: # lower limit
                involved_parts[part]=[ll]

                if ul <= limits[1] :
                    involved_parts[part].append(ul)
                    break; #involved in one part
                else:
                    involved_in_multiple_parts=True
                    involved_parts[part].append(limits[1])
                    involved_parts[part+1]=[limits[1]]
                    inital_part=part+1
                    break;

        if involved_in_multiple_parts:
            curr_part=inital_part
            part_ll=parts_info[curr_part][0]
            part_ul=parts_info[curr_part][1]

            involved_parts[curr_part].append(min(ul,part_ul))
            while part_ul < ul :
                curr_part+=1
                part_ll=parts_info[curr_part][0]
                part_ul=parts_info[curr_part][1]
                involved_parts[curr_part]=[part_ll]
                involved_parts[curr_part].append(min(ul,part_ul))



        print(" Reading from parts Info : ")
        print(involved_parts)
        # print("----------------^^^^^^^^^^^-------------------\n")

        # 3- reading data from involved parts

        #print(" Started reading from files ")

        to_be_returned=bytearray()
        if not is_swp_hidd:
            parts_tobe_read=self.get_parts_paths(self.r.get(self.tree,path[1:])._physical_name)

        else:
            parts_tobe_read=self.get_parts_paths(self.swp_hidd_pn[path])

        for k_part in involved_parts:
            adjusted_offset=involved_parts[k_part][0]-parts_info[k_part][0]
            _length=involved_parts[k_part][1]-involved_parts[k_part][0]
            try:

                f = open(parts_tobe_read[k_part-1],'rb')
                f.seek(adjusted_offset, 0)
                to_be_returned.extend(f.read(_length))
                f.close()

            except Exception as ex:
                print(ex)

        # if to_be_returned[-1] == 0: # xoring an element with itself is zero .... thus, this is necessary for cases when the lesser(am) is missing, and "Nar" is present
        #     to_be_returned= to_be_returned[0:-1]
        
        self.release_after_read=True

        return bytes(to_be_returned)

    def write(self, path, buf, offset, fh):
        '''
        -accumelate the data in buf, at a file hosted on one of the cloud.
        and set the flush_after_write flag
        -
        '''
        #print ("!!!!!acquiring from write")
        self.sem.acquire()

        is_swp_hidd= False
        if path.find('swp') >= 0 or path[path.rfind('/')+1:][0]=='.':
            is_swp_hidd=True

        if not is_swp_hidd:
            name='/'+self.r.get(self.tree,path[1:])._physical_name#path[path.rfind('/'):] #/name

        else:
            name='/'+self.swp_hidd_pn[path]


        #name=path[path.rfind('/'):]

        ## choosing a dir randomly
        if not self.flush_after_write :
            _dir=random.randrange(len(self.cloud_paths))
            self.sc_to_host_temp=self.cloud_paths[_dir]

        try:
            if not os.path.exists(self.sc_to_host_temp+name):
                open (self.sc_to_host_temp+name,'wb+').close()
        except Exception as e :
                print(e)
        try:
            with open (self.sc_to_host_temp+name,'r+b') as f:
                try:
                    f.seek(offset, os.SEEK_SET)
                except Exception as e:
                    pass
                try:
                    #print("### CALLING write !!!!<<<")
                    #rv=f.write(self.em.encrypt_(buf))
                    #print("this is rv ",rv)
                    rv=f.write(buf)
                except Exception as e2 :
                    print("ERR: ",e2)
                    pass

                self.flush_after_write=True;
                f.close()
                #return rv
        except Exception as e3:

            print(e3)

        #print ("!!!!!releasing from write")

        self.sem.release()
        return rv

    def mkdir(self, path, mode):

        print("mkdir")
        name=path[path.rfind('/')+1:]
        path_without_name=path[0:path.find(name)-1]


        #print("name:",name,"\npath_without_name:",path_without_name,"\nparent:",path_without_name)
        if path_without_name=="" :# parent is the root
            a_parent=findall_by_attr(self.tree, 'root')[0]
        else:
            a_parent=self.r.get(self.tree,path_without_name[1:])

        a_dir= Node(name, parent = a_parent, _type="dir")

        # before logging, empty the dict
        self.register_log('mkdir',path_1=path)

        return 0;

    def create_part_files_with_md(self,path,a_node,is_swp_hidd):

        if not is_swp_hidd:
            parts_paths=self.get_parts_paths(a_node._physical_name)

        else:
            parts_paths=self.get_parts_paths(self.swp_hidd_pn[path])

        for part_path in parts_paths:
            fd= open(part_path, 'a+')

            if not is_swp_hidd:
                fdm= open(part_path+".md", 'w+')
                fdm.write("v0")
                fdm.write('\n')
                fdm.write(str(0))
                fdm.close()

                fdm= open(part_path+".md", 'rb')

                enc_fdm= open(part_path+".md.enc", 'wb+')
                enc_fdm.write(self.em.encrypt_(fdm.read()))
                #enc_fdm.write(self.em.encrypt_(b"v0")) ea commented
                enc_fdm.close()

    def create_and_log_node(self,path):

        name=path[path.rfind('/')+1:]
        path_without_name=path[0:path.find(name)-1]

        if path_without_name == "": #root
            a_parent=findall_by_attr(self.tree, 'root')[0]
        else:
            a_parent=self.r.get(self.tree,path_without_name[1:])


        if name.find(".swp") < 0 and name[0] != '.': # dont add swp files to the tree or hidden files !!
            try:
                return(self.r.get(self.tree,path[1:])) # early april added return ...
            except:
                a_file=Node(name, parent = a_parent, _type="file",_version='v0',_physical_name = self.get_a_physical_name())
                #print("creating main file , his parent is ", a_parent, "his name is ",'/root'+path)

                self.register_log('create',path_1=path,_physical_name=a_file._physical_name)
                
                print('physical name: '+a_file._physical_name)

                return(a_file)
                
    def create(self, path, mode, fi=None):
        print("create," , os.path.basename(path))
        a_file=None
        is_swp_hidd=False

        if path.find('swp') >= 0 or path[path.rfind('/')+1:][0]=='.':
            is_swp_hidd=True
            self.swp_hidd_pn[path]=self.get_a_physical_name()

        else:
            a_file=self.create_and_log_node(path)

        self.create_part_files_with_md(path,a_file,is_swp_hidd)

        self.fd = self.fd+1
        #print("\n\n DONE CREATING \n\n ")

        return self.fd

    # def detect_solve_data_conflict(self,path):
    #     versions=[]
    #     try:
    #         current_v=self.r.get(self.tree,path[1:])._version
    #     except:
    #         print("not found")
    #     else:
    #         #
    #         for a in self.get_parts_paths(self.r.get(self.tree,path[1:])._physical_name):
    #             #print("calling get current version with" ,a)
    #             versions.append(self.get_current_version(a))
    #         #
    #         #print("\n\nafter flush's loop\n\n")
    #         #print("CURRENT V: ",current_v)
    #         #print("PART VERIOSNS : ",versions)
    #         pass

    #         for version in versions:
    #             if version != int(current_v.split('v')[1]):
    #                 print("Data Conflict ! ")
    #                 path_without_ext=path[0:path.rfind(".")]
    #                 ext=path[path.rfind("."):]

    #                 path_for_conflicted_copy=path_without_ext+'_'+self.cc+'_ConflictedCopy'+ext

    #                 a_file=self.create_and_log_node(path_for_conflicted_copy)
    #                 ## increase the version manually
    #                 self.r.get(self.tree,path_for_conflicted_copy[1:])._version='v0'
    #                 self.create_part_files_with_md(path_for_conflicted_copy,a_file,False)
    #                 return path_for_conflicted_copy;
    #         return None



    def detect_solve_data_conflict_v2 (self,physical_name,path):
        
        # version to be writen should be the max of the available parts ..
        pf_versions=[]
        for pf in self.get_parts_paths(physical_name):
            pf_versions.append(self.get_current_version(pf))
        
        version_to_be_written=max(pf_versions)+1

        # node=self.r.get(self.tree,path[1:])
        # old_v=int(node._version.split('v')[1]);
        # version_to_be_written=old_v+1

        print('\n\n*********************************** Time To Response Start **************************************\n\n')
        ttr_s=time.time()
        perm=get_write_permission(name=physical_name+'_'+self.cc,version_to_be_written=version_to_be_written) ##
        print('\n\n*********************************** Time To Response Finish : {} **************************************\n\n'.format(time.time()-ttr_s))
        
        if perm:
            print ('Obtained write permission ... ')
            return None
        else:
            ## the new conflicted copy has problem for file names with extension ('.') i.e. nq -> n_sessionxy_conflictedcopy_q instead of nq_sesion_conf....etc
            print("Data Conflict !")
            print('\n\n\n')
            path_without_ext=path[0:path.rfind(".")]
            ext=path[path.rfind("."):]

            path_for_conflicted_copy=path_without_ext+'_'+self.cc+'_ConflictedCopy'+ext
            a_file=self.create_and_log_node(path_for_conflicted_copy)
            self.r.get(self.tree,path_for_conflicted_copy[1:])._version='v0'
            self.create_part_files_with_md(path_for_conflicted_copy,a_file,False)
            
            remove_locks(name=physical_name+'_'+self.cc,cloud='all')
            print ('locks placed by {} were removed'.format(self.cc))
            return path_for_conflicted_copy
            


    def flush(self, path, fh):
        '''
        if after write, then this method is responsible for partioning the accumelated
        file, getting parity, and calling prepare_writing method.
        '''
        name=path[path.rfind('/'):] #/name

        swpf=False
        hiddf=False
        versions=[]

        if path.find("swp") > 0:
            swpf=True
        if path[path.rfind('/')+1:][0] =='.':
            hiddf=True


        if self.flush_after_write :

            print("Flush After Write : ", path,)

            is_swp_hidd=False
            if path.find('swp') >= 0 or path[path.rfind('/')+1:][0]=='.':
                is_swp_hidd=True


            self.parts_info_available[path]= None
            #path_relativ_to_host_os=self.sc_to_host_temp+name
            rv =None

            if  swpf or hiddf:
                #print("hidden or swap file.")
                path_relativ_to_host_os=self.sc_to_host_temp+'/'+self.swp_hidd_pn[path]

                self.prepare_writing(path,path_relativ_to_host_os,is_swp_hidd)
            else:
                #print("normal file.")
                path_relativ_to_host_os=self.sc_to_host_temp+'/'+self.r.get(self.tree,path[1:])._physical_name

                pn__=os.path.basename(path_relativ_to_host_os) # physical name.

                ## timer starts here, for experiment, comment and uncomment the rv= self.detect_solve_data_conflict_v2(pn__,path) line below
                print('\n\n Timer Started for experiment... \n')
                self.start_time=time.time()

                #rv=None ##to simulate no conflict
                
                rv= self.detect_solve_data_conflict_v2(pn__,path)
                
                if  rv == None: # no conflict
                    node=self.r.get(self.tree,path[1:])
                    old_v=int(node._version.split('v')[1]);
                    new_v=old_v+1
                    node._version='v'+str(new_v)
                    self.register_log('update',path_1=path,_physical_name=node._physical_name)

                    self.update_meta(path,os.stat(path_relativ_to_host_os).st_size)


                    self.prepare_writing(path,path_relativ_to_host_os,is_swp_hidd)

                else: # there is a conflict
                    self.conflicted_copies_dict[path]=rv
                    #self.coding.encode(rv,path_relativ_to_host_os,self.cloud_paths)
                    written=self.prepare_writing(rv,path_relativ_to_host_os,is_swp_hidd)
                    #print("\n\nprepare_writing called and returned ", written)

                self.release_after_flush =True

            self.flush_after_write=False;
            #print("removing the accumelated file now")
            os.remove(path_relativ_to_host_os)

        else:
            pass
            print("Normal Flush")

        return 0;

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)

    def rename(self, old, new):
        reterr=False
        print("\n\nENTER RENAIMING\n\n")
        print("this is old ",old)
        print("this is new ",new)

        if old[0:old.rfind('/')] == new[0:new.rfind('/')]: # renaming a file/direcotry  in the same location

            if old.find(".goutputstream") >= 0 : #overwriting
                print("OVERWRITE RENAMING\n")

                old_pn=self.swp_hidd_pn[old]
                new_pn=(self.r.get(self.tree,new[1:]))._physical_name

                new_names=self.get_parts_paths(new_pn);
                old_names=self.get_parts_paths(old_pn);
                
                accumelated_size=0
                for i,old_name in enumerate(old_names):
                    if i ==2:
                        break
                    accumelated_size+=os.stat(old_name).st_size

                print("\nTHIS IS NEW NAMES : ", new_names)

                rv=None
                rv = self.detect_solve_data_conflict_v2(new_pn,new)
                
                #update meta for the size below (conflict) needs work
                if rv != None : # conflict
                    print("OVERWRITE Data Conflict ! ")
                    n_n=self.r.get(self.tree,rv[1:])
                    new_names=self.get_parts_paths(n_n._physical_name)
                    print("\nNEW NAMES CHANGED !!!", new_names)
                    self.update_meta(rv,accumelated_size) ##rename overwrite migh not work here -<

                    reterr=True

                i=0
                
                for old_name in old_names:
                    print("RENAMING ",old_name, "with", new_names[i])
                    os.rename(old_name,new_names[i])
                    ## also th enc
                    os.rename(old_name+'.enc',new_names[i]+'.enc')

                    i+=1

                if rv == None:
                    node=self.r.get(self.tree,new[1:])
                    old_v=int(node._version.split('v')[1]);
                    new_v=old_v+1
                    print("this is the old version: ",old_v," and this is the new one: ",new_v)
                    node._version='v'+str(new_v)
                    self.update_meta(new,accumelated_size) ##rename overwrite migh not work here -<
                    self.register_log('update',path_1=new,_physical_name=node._physical_name)


                # just like flush after write, but this is for overwrite. this is in order for read to know that it has to
                # culate again
                self.parts_info_available[new]=None

                self.release_after_overwrite=True


            else:                       #normal renaming

                if self.r.get(self.tree,old[1:])._type =='dir':
                    self.file_rename=False;
                    print("\n RENAMING A DIRECTORY IN THE SAME LOCATIONqqq")


                else:
                    self.file_rename=True;
                    #rename all parts and their md
                    i=0
                    # for cloud in self.cloud_paths:
                    #     print("\n\n NORMAL RENAIMING")
                    #
                    #     old_part_name=old[old.rfind("/")+1:old.rfind(".")]+'_'+str(i+1)+old[old.rfind("."):]
                    #     new_part_name=new[new.rfind("/")+1:new.rfind(".")]+'_'+str(i+1)+new[new.rfind("."):]
                    #     shutil.copy2(cloud+'/'+old_part_name, cloud+'/'+new_part_name)
                    #
                    #     shutil.copy2(cloud+'/'+old_part_name+'.md', cloud+'/'+new_part_name+'.md')
                    #     i+=1

                old_node=self.r.get(self.tree,old[1:])
                a_parent=old_node.parent
                old_name=old_node.name
                old_node.name=new[new.rfind('/')+1:]
                self.register_log('rename',path_1=old,path_2=new)

                if reterr:
                    pass
                    #raise OSError(errno.EEXIST,"Conflicted Copy Created")
                return 0;

        else: # moving renaming
            print("\n MOVING FROM", old, "TO: ", new)
            self.register_log('move_rename',path_1=old,path_2=new)

            cnode=self.r.get(self.tree,old[1:])
            parent_of_cnode=cnode.parent
            new_parent=self.r.get(self.tree,new[1:new.rfind('/')])

            ##now moving##
            cnode.parent=new_parent


    def rmdir(self, path):
        print("rmdir(",path,")")

        node_to_remove=self.r.get(self.tree,path[1:])

        a_parent=node_to_remove.parent

        if node_to_remove.children:
            print("this dir is not empty")
            raise OSError(errno.ENOTEMPTY, '')
            return -1 ; # failure
        else:
            print("this dir IS empty")
            previously_created=False

            self.register_log('rmdir',path)

            node_to_remove.parent=None
            return 0;

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
            #print("PPP:",part_files)
            return part_files

    def unlink(self, path):
        print("UNLONK METHOD ON :",path)
        if path.find("swp") >= 0 or  path[path.rfind('/')+1:][0]=='.':
            for a in self.get_parts_paths(self.swp_hidd_pn[path]):
                os.unlink(a)
                os.unlink(a+'.enc')
                #print("unlinked this swp/hidd ",a)

        else:
            print("inside else")
            pass

            node_to_remove=self.r.get(self.tree,path[1:])
            a_parent=node_to_remove.parent
            node_to_remove.parent=None # enough to remove
            self.register_log('unlink',path_1=path,_physical_name=node_to_remove._physical_name)

        print('done')
        return None

    def truncate(self, path, length, fh=None):
        #print("truncate (",path,length,")")
        self.data[path] = self.data[path][:length]
        #self.files[path]['st_size'] = length

    def statfs(self, path):
        #print(">>STATFS")
        #full_path = self._full_path(path)
        stv = os.statvfs(path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def chmod(self, path, mode):
        #full_path = self._full_path(path)
        return os.chmod(path, mode)

    def access(self, path, mode):
        _dir=False
        _file=False

        try:
            the_node=self.r.get(self.tree,path[1:])
        except:
            return 0;
        else:

            if the_node._type=='file':
                _file=True
            elif the_node._type=='dir':
                _dir=True

            if _file:
                ps=[]
                #print(">>access",path,mode)

                for a in self.get_parts_paths(path):
                    if os.path.isfile(a):
                        part_access=os.access(a, mode)
                        #print("this is part access ",part_access)
                        ps.append (part_access)

                #print("this is ps ",ps)
                acc=True
                for p in ps:
                    acc=acc and p
                # print("ACCESESS Permessions (file) :")
                # #print(ps)
                # print(acc)
                # print("-----------------")
                if acc == True:
                    return 0; # access success
                else:
                    #print("!No access permission for this file ")
                    return -1;
            elif dir:
                ps=[]
                for a in self.cloud_paths:
                    ps.append (os.access(a, mode))
                acc=True
                for p in ps:
                    acc=acc and p
                #print("ACCESESS Permessions (dir) :")
                #print(ps)
                #print(acc)
                #print("-----------------")
                if acc == True:
                    return 0; # access success
                else:
                    #print("!No access permission for this dir")
                    return -1;

    def update_meta(self,path,new_size):
        for part_file in self.get_parts_paths(self.r.get(self.tree,path[1:])._physical_name):
            with open (part_file+".md", "r") as fmd:
                read_version=fmd.readline()
                old_v=int(read_version.split('v')[1])
            with open (part_file+".md", "w") as fmd:
                new_v=old_v+1
                fmd.write('v'+str(new_v))

                #ea
                fmd.write('\n')
                fmd.write(str(new_size))
                fmd.close()
                # end ea

            ## write .md.enc files.
            with open (part_file+".md", "rb") as fmd:
                with open (part_file+".md.enc", "wb") as enc_fmd:
                    enc_fmd.write(self.em.encrypt_(fmd.read()))

            #print("updated this meta: ",part_file+".md")

    def prepare_writing(self,path,pathOrg,is_swp_hidd):
        '''
        this method is responsible for reading the accumelated file,
        and partionig it to multiple part files and/or parity files
        then
        '''
        #print("prepare_writing",path,pathOrg)
        file_size=os.stat(pathOrg).st_size

        file_name_without_extension=path[path.rfind("/")+1:path.rfind(".")]
        extension=path[path.rfind("."):]

        ##1- calculate teh part size
        part_size=math.ceil(file_size/(len(self.cloud_paths)-1))

        _lmt= 500 * 1024 * 1024 #K, M, G

        ## 2- get the trans_size, which represents how much of part_size can
        ## be loaded into memory
        div=1
        if (part_size <= _lmt ):
            _multiple=False
            trans_size= part_size
        else:
            _multiple=True

            mod_part_size=part_size
            while (mod_part_size >  _lmt ):
                div+=1
                mod_part_size=part_size/div

            trans_size=math.ceil(mod_part_size)

        offset=0;
        iteration=0;

        #3- write parts

        if len(self.cloud_paths) == 3: ##[3,2] coding ## this should be different method
            #print("print calling write 32 now ")
            self.write32(trans_size,_multiple,div,file_size,pathOrg,path,is_swp_hidd)

        #print("finished prepare ")
        return True
            ## writing the parity shoul be here when adding the coding

    def write32(self,trans_size,_multiple,div,file_size,pathOrg,path,is_swp_hidd):
        #print("## PARAMETERS",trans_size,_multiple,div,file_size,pathOrg,path)
        part_size=math.ceil(file_size/(len(self.cloud_paths)-1)) # a part is saved for parity

        if not is_swp_hidd:
            part_files= self.get_parts_paths(self.r.get(self.tree,path[1:])._physical_name)
        else:
            part_files= self.get_parts_paths(self.swp_hidd_pn[path])

        adjusted_part_files=[part_files[0],part_files[1]]
        parity_file=part_files[2]

        ## calculate the parity
        with open(pathOrg,"rb") as fileobjectFrom:
            if not _multiple: # two whole parts can be loaded into memory
                #print("## NOT MULTIPLE")

                ## part 1:
                fp=bytearray(fileobjectFrom.read(trans_size))
                with open(part_files[0],"wb") as fileobjectTo:
                    fileobjectTo.write(fp)

                    print('Part 1 written .. :')#,fp,len(fp))
                #if not is_swp_hidd:
                with open(part_files[0]+'.enc',"wb") as fileobjectTo:
                    fileobjectTo.write(self.em.encrypt_(bytes(fp)))

                ## part 2:
                sp=bytearray(fileobjectFrom.read(trans_size))
                with open(part_files[1],"wb") as fileobjectTo:
                    fileobjectTo.write(sp)
                    print('Part 2 written .. :')#,sp,len(sp))

                # if not is_swp_hidd:
                with open(part_files[1]+'.enc',"wb") as fileobjectTo:
                    fileobjectTo.write(self.em.encrypt_(bytes(sp)))

                ## part 3 (parity):
                pp=coding.get_simple_xor_parity(fp,sp)
                with open(parity_file,"wb") as fileobjectTo:
                    fileobjectTo.write(pp)
                    print('Parity written ..: ')#,pp,len(pp))

                # if not is_swp_hidd:
                with open(parity_file+'.enc',"wb") as fileobjectTo:
                    fileobjectTo.write(self.em.encrypt_(bytes(pp)))

            else: # the size of a part is more that _lmt
                #print("  ## MULTIPLE")
                ## 1- finish the first two parts completly
                for part_file in adjusted_part_files:
                    with open(part_file,"wb") as fileobjectTo:
                        with open(part_file+'.enc',"wb") as encFileobjectTo:
                            for i in range (0,div):
                                _by_s=fileobjectFrom.read(trans_size)
                                fileobjectTo.write(_by_s)
                                encFileobjectTo.write(self.em.encrypt_(_by_s))

                ##2- finish the parity part
                with open(part_files[0],"rb") as fileobjectFrom_1:
                    with open(part_files[1],"rb") as fileobjectFrom_2:
                        with open(part_files[2],"wb") as fileobjectTo:
                            with open(part_files[2]+'.enc',"wb") as encFileobjectTo:
                                for i in range (0,div):
                                    fp=bytearray(fileobjectFrom_1.read(trans_size))
                                    sp=bytearray(fileobjectFrom_2.read(trans_size))
                                    fp=coding.get_simple_xor_parity(fp,sp) # reuse same fp variable for memory
                                    fileobjectTo.write(fp)
                                    encFileobjectTo.write(self.em.encrypt_(fp))

    def check_rebuild_32(self,path,parts_paths):
        
        pf_versions={}
        
        for part_path in parts_paths:
            pf_versions[part_path]=self.get_current_version(part_path)
        #pf_version will always be length 3, a verison of -1 will be assigned if a part is missing...
        
  
        to_rebuild=None
        

        if list(pf_versions.values()).count(min(pf_versions.values())) == 3: # example case [2,2,2] # all same version 
            pass # no need to do anything.
            print('cr',path,'nothing ...')
        elif list(pf_versions.values()).count(min(pf_versions.values())) == 2: # example case [2,2,3] # all same version 
            raise Exception('inconsistent versions.')  
        elif list(pf_versions.values()).count(min(pf_versions.values())) == 1:
            if list(pf_versions.values()).count(max(pf_versions.values())) == 1: # example case [4,3,1] # all same version 
                raise Exception('inconsistent versions.')

            elif list(pf_versions.values()).count(max(pf_versions.values())) == 2: # example case [4,4,3] # all same version 
                # a rebuild should be done, get the path of the part whose version is the found unique min   
                for k,v in pf_versions.items():
                    if v == min(pf_versions.values()):
                        to_rebuild=k
                        print ('>>>building  a part ',k)
        
    
        use_for_rebuild=[x for x in parts_paths if x!= to_rebuild]
        

        if to_rebuild  :
            _lmt=500 * 1024  * 1024  #K, M, G
            div=1
            part_size=os.stat(use_for_rebuild[0]).st_size
            if (part_size <= _lmt ):
                _multiple=False
                trans_size= part_size
            else:
                _multiple=True
                mod_part_size=part_size
                while (mod_part_size >  _lmt ):
                    div+=1
                    mod_part_size=part_size/div
                trans_size=math.ceil(mod_part_size)
            

            ## rebuild
            # start early april edit
            strip_null_byte=False
            if 'GoogleDrive' in to_rebuild: # Second part is missing, according to the file size call xor
                with open(use_for_rebuild[0]+'.md',"r") as fmd:
                    fmd.readline()
                    size=int(fmd.readline())
                    if size % 2 != 0:
                        strip_null_byte=True
                        print('should strip a null byte')
            
            with open(use_for_rebuild[0],"rb") as fileobjectFrom_1:
                
                with open(use_for_rebuild[1],"rb") as fileobjectFrom_2: # tis will always be the pariy 
                    
                    with open(to_rebuild,"wb") as fileobjectTo:
                        
                        for i in range (0,div):
                            fp=bytearray(fileobjectFrom_1.read(trans_size))
                            if strip_null_byte:
                                fp=fp[0:-1]                            
                            sp=bytearray(fileobjectFrom_2.read(trans_size))
                            ## early april
                            if strip_null_byte:
                                sp=sp[0:-1]
                            ## end earl
                            fp=coding.get_simple_xor_parity(fp,sp) # reuse same fp variable for memory
                            #fp=coding.repair(fp,sp) # reuse same fp variable for memory
                            #fileobjectTo.write(fp)
                            fileobjectTo.write(fp)
                            #print("c")
            
            ## copy the md from first available part
            with open(use_for_rebuild[0]+'.md',"rb") as fileobjectFrom_1:
                with open(to_rebuild+'.md',"wb") as fileobjectTo:
                    fileobjectTo.write(fileobjectFrom_1.read())
            
            return True
        else:
            pass
            return True


    ## DCT
    def reinitialize_tree(self,c=''):
        '''
        '''
        if not c:
            cloud=self.cloud_paths[0]
        elif c=='b':
            cloud=self.cloud_paths[2]
        elif c=='gd':
            cloud=self.cloud_paths[1]

        print ('started reinitializaing the FS ...')
        fsf= open(cloud+'/FSFolder/FSF',"rb") ##<< here to test
        self.new_tree=pickle.load(fsf)

        print ('Checking for dangling update ..')
        lf=log_fixer(self.log_folder,self.new_tree,self.tree,self.db_cm,self.gd_cm,self.b_cm)
        self.new_tree=lf.fix_logs()
        print ('Done dealign with danngling ..')
        self.tree=self.new_tree
        print("\nReinitializing Done. . . .")
        

        #self.delete_local_data()

    def delete_local_data(self):
        ## TODO: rest of the parts 
        ## First Part :
        if os.path.exists(self.cloud_paths[0]+'/FSFolder/Deleted/names'):
            with open (self.cloud_paths[0]+'/FSFolder/Deleted/names','r') as f:
                all=f.read()
                tokens=all.split('\n')
                tokens=tokens[0:-1] # discard last empty line
                for token in tokens:
                    #print("this is token ",token)
                    try: # it will stay here if log fixer kept the file (in case of dangling 'update'), and also it will be under special directory
                        to_be_deleted=findall_by_attr(self.tree,token,"_physical_name")[0]
                    except: # not found, should be deleted, below shoul be tryied 
                        ## done: remvoe .enc extension before removing , another thing: careful for duplicated (from box)
                        token=token.replace('.enc','')
                        try:
                            os.remove(self.cloud_paths[0]+'/'+token)
                        except Exception as e:
                            print (e)
                        try:
                            os.remove(self.cloud_paths[1]+'/'+token)
                        except Exception as e:
                            print (e)
                        try:
                            os.remove(self.cloud_paths[2]+'/'+token)
                        except Exception as e:
                            print (e)
            open(self.cloud_paths[0]+'/FSFolder/Deleted/names', 'w').close()

    def get_a_physical_name(self):
        all_case=[]
        for L,l in zip(ascii_uppercase,ascii_lowercase):
            all_case.append(L)
            all_case.append(l)
        a=''.join(choice(all_case) for i in range(10))
        a=a+"_"+str(math.ceil(time.time()))

        return (a)

    def register_log(self,operation,path_1='',path_2='',_physical_name=''):
        self.log_id+=1

        log_content=operation+','+path_1
        if path_2!='': # path 2 is present
            log_content=log_content+','+path_2
        if _physical_name!='':
            log_content=log_content+','+_physical_name

        for cloud in self.cloud_paths:
            if not os.path.exists(cloud+'/FSFolder/'+self.log_folder):
                os.mkdir(cloud+'/FSFolder/'+self.log_folder)
                print('recreated a deleted session folder to continue this session')
            
            with open (cloud+'/FSFolder/'+self.log_folder+'/'+str(self.log_id),'w+') as f:
                f.write(log_content)
            with open (cloud+'/FSFolder/'+self.log_folder+'/'+str(self.log_id)+'.enc','wb+') as f:
                f.write(self.em.encrypt_(bytes(log_content,'utf-8')))


        ## upload log to db
        ## Attn: both are taken from same local db dir
        _src=self.cloud_paths[0]+'/FSFolder/'+self.log_folder+'/'+str(self.log_id)+'.enc'
        _src2=self.cloud_paths[1]+'/FSFolder/'+self.log_folder+'/'+str(self.log_id)+'.enc'
        _src3=self.cloud_paths[2]+'/FSFolder/'+self.log_folder+'/'+str(self.log_id)+'.enc'

        _dst='/FSFolder/'+self.log_folder+'/'+str(self.log_id)+'.enc'

        a=db_uploader(_src,_dst,is_log=True,db_cm=self.db_cm)
        a.start()

        b=gd_uploader(_src2,is_log=True,gd_cm=self.gd_cm)
        b.start()

        c=b_uploader(_src3,is_log=True,b_cm=self.b_cm)
        c.start()


    def upload_to_clouds(self,pn):
        

        ###############################################
        ########################################### Dropbox ##############################################
        p1_path_relative_to_os=self.get_parts_paths(pn)[0]+'.enc'
        p1_md_path_relative_to_os=self.get_parts_paths(pn)[0]+'.md.enc'
        
        fname1=p1_path_relative_to_os[p1_path_relative_to_os.rfind('/'):]
        fname1_md=p1_md_path_relative_to_os[p1_path_relative_to_os.rfind('/'):]
        
        p1=db_uploader(p1_path_relative_to_os,fname1,self.db_cm,session=self.cc,upload_md=True)
        p1.start()
        

        #################################################################################################

        ########################################### Google Drive ########################################
        p2_path_relative_to_os=self.get_parts_paths(pn)[1]+'.enc'
        p2_md_path_relative_to_os=self.get_parts_paths(pn)[1]+'.md.enc'

        fname2=p2_path_relative_to_os[p2_path_relative_to_os.rfind('/'):]
        fname2_md=p2_md_path_relative_to_os[p2_path_relative_to_os.rfind('/'):]

        p2=gd_uploader(p2_path_relative_to_os,gd_cm=self.gd_cm,session=self.cc,upload_md=True)
        p2.start()


        ################################################## Box ###############################################
        p3_path_relative_to_os=self.get_parts_paths(pn)[2]+'.enc'
        p3_md_path_relative_to_os=self.get_parts_paths(pn)[2]+'.md.enc'

        p3=b_uploader(p3_path_relative_to_os,self.b_cm,session=self.cc,upload_md=True)
        p3.start()

        p1.join()
        p2.join()
        p3.join()
        print('\n\n------------------------------Experiment------------------------------------\n\n')


        print('time consumed: ',time.time()-self.start_time)
        print('\n\n----------------------------------------------------------------------------\n\n')
        ## timer should end here
        ## joining the three threads only for expermintation, should be removed


        return

###################################################################################################################################################
if __name__ == '__main__':
    try:

        parser = argparse.ArgumentParser(description='SafeDrive Parser')
        parser.add_argument('mountp')
        args=parser.parse_known_args()
        #args = parser.parse_args()
        mountp=args[0].mountp
        #print("this is args :",args)
        #mountp=sys.argv[1]
        FUSE(RSCFS(), mountp, nothreads=True, foreground=True)
    except KeyboardInterrupt:
        pass
        #t.join()
        print('Exiting')
