from db_sync.db_auth import get_DB_account
from gd_sync.gd_auth import gd_auth
from b_sync.b_auth import b_auth

from collections import OrderedDict

def get_status_snap():
    st_dict=OrderedDict()
    a=get_DB_account()

    try:
        a.users_get_current_account()
    except Exception as e: ##really dowm
        st_dict['db']=False
    else:
        if a is None :
            st_dict['db']=False # for the simulation
        else:
            st_dict['db']=True
    
##############################################################
## gd is a bit different in reliability check simulation..
    try:
        (b1,b2)=gd_auth().get_drive_service()
    except Exception as e: # really down
        st_dict['gd']=False
    else: # for simulation
        if not b1 or not b2:
            st_dict['gd']=False
        else:
            st_dict['gd']=True
    
##################################################################
    
    
    try: 
        (c1,c2)=b_auth().get_authenticated_client()
    except Exception as e: # really down
        st_dict['b']=False
        # optional, show the exception
        #print('------------- here is the exception :: ',e,'\n\n')
    else: # for simulation
        if c1 is None or c2 is None:
            st_dict['b']=False
        else:
            st_dict['b']=True
    
    return st_dict