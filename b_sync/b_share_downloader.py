from b_sync.b_auth import b_auth

class b_share_downloader :
    def __init__(self,local_path):
        client,app_folder=b_auth().get_authenticated_client()
        files=app_folder.get_items(limit=200)
        for file in files:
            if file.name=='ss_2':
                f=open (local_path,'wb')
                file.download_to(f)
                return
        raise Exception('ss_2 not found')

