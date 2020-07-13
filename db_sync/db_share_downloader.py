
import dropbox
from db_sync.db_auth import get_DB_account

class db_share_downloader:
    def __init__(self,local_path):
        dbx=get_DB_account()
        dbx.files_download_to_file(local_path,'/ss_0') #should each download be a thread?
