from gd_sync.gd_auth import gd_auth
from apiclient.http import MediaIoBaseDownload
import io

class gd_share_downloader:
    def __init__(self,local_path):
        service=gd_auth().get_drive_service()
        app_folder=service[1]
        drive_service=service[0]
        _list = drive_service.files().list(q=" name = '"+'ss_1'+"' and trashed =false and '"+ app_folder+"' in parents").execute()
        file_id=_list['files'][0].get('id')
        
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.FileIO(local_path, 'wb')#fh = io.BytesIO()

        downloader = MediaIoBaseDownload(fh, request,chunksize=100*1024*1024)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
       
        

