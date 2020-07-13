from lf import log_fixer
import pickle
import copy
from anytree import Node, RenderTree, AsciiStyle, findall_by_attr, Resolver

from anytree import Node, RenderTree, AsciiStyle, findall_by_attr, Resolver
import copy
import math
import os
import sys
import time

home=os.path.expanduser('~')
cloud_paths=[
home+"/Desktop/Dropbox",
home+"/Desktop/GoogleDrive",
home+"/Desktop/Box",
]

old_fs = Node("root")
unlink_testing_node_old_fs = Node("unlink_testing_node", parent=old_fs,_physical_name='abc')
bb = Node("bbb", parent=old_fs)
aa = Node("aa", parent=bb,_sadf='qqqqq') ## attribute that starts with _ is hidden from render tree function ?!
dd = Node("dd", parent=bb)


########################################################################################
new_fs = Node("root")
b = Node("b", parent=new_fs)
a = Node("a", parent=b,_sadf='qqqqq') ## attribute that starts with _ is hidden from render tree function ?!
d = Node("d", parent=b)
# c = Node("c", parent=d)
# e = Node("e", parent=d)
g = Node("g", parent=new_fs)
i = Node("i", parent=g)
h = Node("h", parent=i)
unlink_testing_node_new_fs = Node("unlink_testing_node", parent=new_fs,_physical_name='abc')

########################################################################################

r=Resolver("_someat")
log_f=log_fixer('log60',new_fs,old_fs)

print (' new  fs  : ')
print(RenderTree(new_fs))

'''
before testing , make the setupe : each cloud bath create FSFolder/log60
'''

## First Group: 
def mkdir_testing(success):

    ## testing mkdir, try failure and success separately.
    print ('testing fixing a mkdir log')
    # create a text log file in cc/logxx (take cc from lf) that says mkdir /b/q/s ( q does not exist)
    # A- failure: 
    if not success:
        with open (cloud_paths[0]+'/FSFolder/log60/3','w') as l:
            l.write('mkdir,/b/q/s')

        log_f.fix_logs()

        # go observe what happend to the log 3 , and also log 0 is added on all clouds 
    else:
        # B - Sucess :, erase the old logs 
        with open (cloud_paths[0]+'/FSFolder/log60/5','w') as l:
            l.write('mkdir,/b/q')

        log_f.fix_logs()
        print(RenderTree(new_fs))

    # observe the tree, you will find q, and the log is untouched

def create_testing(success):

    ## testing mkdir, try failure and success separately.
    print ('testing fixing a mkdir log')
    # create a text log file in cc/logxx (take cc from lf) that says mkdir /b/q/s ( q does not exist)
    
    if not success:
        # A- failure: 
        with open (cloud_paths[0]+'/FSFolder/log60/2','w') as l:
            l.write('create,/b/q/s.txt')

        log_f.fix_logs()

        # go observe what happend to the log 3 , and also log 0 is added on all clouds 
    else:

    # B - Sucess :, erase the old logs 
        with open (cloud_paths[0]+'/FSFolder/log60/4','w') as l:
            l.write('create,/b/q.txt')
        log_f.fix_logs()
        print(RenderTree(new_fs))

    # observe the tree, you will find q, and the log is untouched

def rmdir_testing(success):

    ## testing mkdir, try failure and success separately.
    print ('testing fixing a rmdir log')
    # create a text log file in cc/logxx (take cc from lf) that says mkdir /b/q/s ( q does not exist)
    
    if not success:
        # A- failure: 
        with open (cloud_paths[0]+'/FSFolder/log60/2','w') as l:
            l.write('rmdir,/b/q/s')

        log_f.fix_logs()

        # go observe what happend to the log 3 , and also log 0 is added on all clouds 
    else:

    # B - Sucess :, erase the old logs 
        with open (cloud_paths[0]+'/FSFolder/log60/4','w') as l:
            l.write('rmdir,/b/d')

        log_f.fix_logs()
        print(RenderTree(new_fs))

    # observe the tree, you will find q, and the log is untouched

## Second Group :
def rename_testing(success):
    print ('testing fixing a rename log')
    # create a text log file in cc/logxx (take cc from lf) that says mkdir /b/q/s ( q does not exist)

    if not success:
        # A- failure: 
        with open (cloud_paths[0]+'/FSFolder/log60/2','w') as l:
            l.write('rename,/b/q/s,b/q/hh')

        log_f.fix_logs()
        print(RenderTree(new_fs))

        # go observe what happend to the log 3 , and also log 0 is added on all clouds 
    else:

    # B - Sucess :, erase the old logs 
        with open (cloud_paths[0]+'/FSFolder/log60/4','w') as l:
            l.write('rename,/b/d,/b/new_d')

        log_f.fix_logs()
        #print(RenderTree(new_fs))

    # observe the tree, you will find q, and the log is untouched

def move_rename_testing(success):
    print ('testing fixing a rename log')
    # create a text log file in cc/logxx (take cc from lf) that says mkdir /b/q/s ( q does not exist)

    if not success:
        # A- failure: 
        with open (cloud_paths[0]+'/FSFolder/log60/10','w') as l:
            l.write('move_rename,/b/q,uu/ww/q')

        log_f.fix_logs()
        print(RenderTree(new_fs))

        # go observe what happend to the log 3 , and also log 0 is added on all clouds 
    else:

    # B - Sucess :, erase the old logs 
        with open (cloud_paths[0]+'/FSFolder/log60/13','w') as l:
            l.write('move_rename,/b/a,/g/i/a')

        log_f.fix_logs()
        print(RenderTree(new_fs))

    # observe the tree, you will find q, and the log is untouched

## Third Group :
 
def unlink_testing (success,file_exists=True):
    if file_exists:
        if not success: # failure : want to test unlinking different versions  
            unlink_testing_node_new_fs._version='v5' # i received v3
            unlink_testing_node_old_fs._version='v2' # i previously deleted v2

        else: # success : want to test unlinking the same verison 
            unlink_testing_node_new_fs._version='v5' # i received v3
            unlink_testing_node_old_fs._version='v5' # i previously deleted v2

        with open (cloud_paths[0]+'/FSFolder/log60/22','w') as l:
            l.write('unlink,/unlink_testing_node,abc')
    else:
        with open (cloud_paths[0]+'/FSFolder/log60/22','w') as l:
            l.write('unlink,/zzz,abc')
    log_f.fix_logs()

    print(RenderTree(new_fs))

def update_testing (success):
    if success: # put the node, and write the log 
        update_testing_node_new_fs = Node("update_testing_node", parent=new_fs,_physical_name='xyz',_version='v4')
        with open (cloud_paths[0]+'/FSFolder/log60/22','w') as l:
            l.write('update,/update_testing_node,xyz')

        print ("new version : ",update_testing_node_new_fs._version)

    else: # write the node without putting the code
        with open (cloud_paths[0]+'/FSFolder/log60/22','w') as l:
            l.write('update,/update_testing_node,xyz')

    log_f.fix_logs()

    print(RenderTree(new_fs))

######################################
# for testing .. call the methds here 

mkdir_testing(success=False)
