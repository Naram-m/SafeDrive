import os
home=os.path.expanduser('~')
cloud_paths=[home+"/Desktop/Dropbox",home+"/Desktop/GoogleDrive",home+"/Desktop/Box"]
## following methods returns either true or false 
def reliability_startup(available_clouds):
    available_clouds_names=[os.path.basename(x) for x in available_clouds]
    ## specific for 3,2 coding
    if len(available_clouds) == 3:
        if not os.path.exists('./down_clouds.txt'):
            return True
        else:
            with open('./down_clouds.txt','r') as f:
                saved_mc=f.read().strip()
            if not saved_mc:
                return True
            else:
                pass
                print('Should repair '+saved_mc)
                return True
    
    elif len(available_clouds) ==2: #there should be a down_clouds file..
        if not 'Dropbox' in available_clouds_names:
            mc='Dropbox'
        elif not 'GoogleDrive' in available_clouds_names:
            mc='GoogleDrive'
        elif not 'Box' in available_clouds_names:
            mc='Box'
        
        with open('./down_clouds.txt','r') as f:
            saved_mc=f.read().strip()
        if saved_mc==mc:
            #print('clouds to be repaired: '+saved_mc)
            return True # a down cloud is still down
        else:
            pass
            print('clouds to be repaired: '+saved_mc)
            with open('./down_clouds.txt','w') as f:
                f.write(mc)
            return True
    else:
        return False

from status_snap import get_status_snap
ac=get_status_snap()
available_clouds=[]
for c in ac:  
    if c =='db' and ac[c]==True:
        available_clouds.append(cloud_paths[0])
    elif c =='gd' and ac[c]==True:
        available_clouds.append(cloud_paths[1])
    elif c =='b' and ac[c]==True:
        available_clouds.append(cloud_paths[2])

print('\n this is available clouds .... : ',available_clouds,'\n\n')

with open('./reinitializing_cloud.txt','w') as f:
    f.write(os.path.basename(available_clouds[0]))  

start=reliability_startup(available_clouds)
if not start:
    print('\n\n\n Not enough cloud providers are available currently ... \n\n\n')
    exit()