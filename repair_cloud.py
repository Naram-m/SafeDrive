# def repair_cloud(cloud_name='',FSF=None):
from anytree import Node, RenderTree, AsciiStyle, findall_by_attr, Resolver,PostOrderIter
import copy
import math
import os
import sys
import time
import pickle


try:
    fsf=open ('/home/nm1300/Desktop/FSF',"rb")
except Exception as e:

    print("could not open fsf:",e)
    FSF=None
    pass
else:
    FSF=pickle.load(fsf)
    fsf.close()

def get_path_as_string(tuple):
    s=""
    for t in tuple:
        s=s+'/'+t.name
    s=s.replace('/root',"")
    return s

a=[node for node in PostOrderIter(FSF)]

for x in a:
    print(get_path_as_string(x.path))
    if x._type !='dir':
        print(x._physical_name)

