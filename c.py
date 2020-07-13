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
import errno
import copy
import shutil
from collections import Counter
import gc, sys
import math

class coding:

    ## receive a byte array
    def get_simple_xor_parity(fp_ba,sp_ba):
        # fp_ba=bytearray(fp)
        # sp_ba=bytearray(sp)

        if len(fp_ba) < len(sp_ba):
            augment_byte=b'\x00'
            while len(fp_ba) < len(sp_ba):
                fp_ba.extend(augment_byte)
        elif len(sp_ba) < len(fp_ba):
            augment_byte=b'\x00'
            while len(sp_ba) < len(fp_ba):
                sp_ba.extend(augment_byte)

        #print("been called")
        int_fp = int.from_bytes(fp_ba, sys.byteorder)
        int_sp = int.from_bytes(sp_ba, sys.byteorder)
        #print("xoring ",len(fp),"with ", len(sp))
        int_pp = int_fp ^ int_sp
        int_pp_bytes_array=bytearray(int_pp.to_bytes(min(len(fp_ba),len(sp_ba)),sys.byteorder))
        #print ("::::",int_pp_bytes_array)
        # if int_pp_bytes_array[-1] == 0: # xoring an element with itself is zero .... thus, this is necessary for cases when the lesser(am) is missing, and "Nar" is present
        #     return int_pp_bytes_array[0:-1]
        return int_pp_bytes_array
    
    def repair (fp_ba,sp_ba):
        if len(fp_ba) != len(sp_ba):
            ml=min([len(fp_ba),len(sp_ba)])
            int_fp = int.from_bytes(fp_ba[0:ml], sys.byteorder)
            int_sp = int.from_bytes(sp_ba[0:ml], sys.byteorder)
            int_pp = int_fp ^ int_sp
            int_pp_bytes_array=bytearray(int_pp.to_bytes(min(len(fp_ba),len(sp_ba)),sys.byteorder))
            if len(fp_ba) > len(sp_ba):
                int_pp_bytes_array.extend(fp_ba[ml:])
            elif len(sp_ba) > len(fp_ba):
                int_pp_bytes_array.extend(sp_ba[ml:])
            
            return int_pp_bytes_array
        else:
            int_fp = int.from_bytes(fp_ba, sys.byteorder)
            int_sp = int.from_bytes(sp_ba, sys.byteorder)
            int_pp = int_fp ^ int_sp
            int_pp_bytes_array=bytearray(int_pp.to_bytes(min(len(fp_ba),len(sp_ba)),sys.byteorder))
            return(int_pp_bytes_array)