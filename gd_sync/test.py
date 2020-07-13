
from gd_auth import get_drive_service
from gd_downloader import gd_downloader
from gd_uploader import gd_uploader
from gd_cm import gd_cm
from gd_logs import gd_logs
from gd_start import gd_start
from gd_fremove import gd_fremove
import time
from apiclient.http import MediaFileUpload



#1uCy4OXh_0NppKoE1oFsTRzoRApFxU5HK // App folder id
# 1FYG6hgb3gWwM7mcdNNLD_Cn16qlcub3a // FSFolder

# a=gd_logs()
#
# a.run_()

drive_service=get_drive_service()[0]




##### * Upload some log files in 1 , 2 ,3 in log 60

# path='/home/parallels/Desktop/fsfs/4'
# print(" uploading a log")
# media = MediaFileUpload(path)
# _name=path[path.rfind('/')+1:]
# request = drive_service.files().create(media_body=media, body={'name': _name, 'parents': ['1vrsWbp6Nl6rLTambywY2CDwgtW3MlkCM']})
# request.execute()

 ## Upload FSF to FSFolder
#path='/home/parallels/Desktop/fsfs/first/FSF'
# media = MediaFileUpload(path)
# _name=path[path.rfind('/')+1:]
# request = drive_service.files().create(media_body=media, body={'name': _name, 'parents': ['1FYG6hgb3gWwM7mcdNNLD_Cn16qlcub3a']})
# request.execute()

 ##* gd logs testing
#path='/home/parallels/Desktop/fsfs/second/FSF'
# a=gd_logs()
# # a.run_()
# a.remove_logs('/FSFolder/log55')



## gd uploader testing

# less than, first time
# a=gd_uploader('/media/psf/Dropbox/ssb.txt')
# a.start()

## gd start testing

# a=gd_start()
# a.start()

## * gd fremove testing

# a=gd_cm('/dd.txt')
# a.start()
# time.sleep(2)
#
# a=gd_uploader('/media/psf/Dropbox/ssb.txt')
# a.start()
#
#
# time.sleep(2)
#
# b=gd_uploader('/media/psf/Dropbox/mhasen.txt')
# b.start()
#
# time.sleep(2)
#

a=drive_service.files().get(fileId='1izstBvNy6CUmlRkMWKxD54Tt5gL7-gur',fields="parents").execute()['parents'][0]
b=drive_service.files().get(fileId=a,fields="name").execute()['name']

print(b)

# print ("----- removing ..")
#
# drive_service.files().delete(fileId=fileId).execute()
#
# time.sleep(2)
#
#
# drive_service.files().delete(fileId=fileId).execute()
