from boxsdk import OAuth2, Client
import boxsdk
import requests
import time
import webbrowser
import os

class b_auth():
    authenticated_client=None
    app_folder=None
    def __init__(self):
        pass        
    def get_authenticated_client(self):
        if b_auth.authenticated_client is None:
            if self.stored_creds_exist():
                access_token, refresh_token=self.get_stored_creds()
                self.oauth = OAuth2(
                    client_id='bttdivoigr9rcg2difzsvea5994hmxep',
                    client_secret='AkiKuIVmPzsKk2dqkfi3JIpbqvNbF8mg',
                    store_tokens=self.store_creds,
                    access_token=access_token,
                    refresh_token=refresh_token,
                )
            else:
                self.oauth = OAuth2(
                    client_id='bttdivoigr9rcg2difzsvea5994hmxep',
                    client_secret='AkiKuIVmPzsKk2dqkfi3JIpbqvNbF8mg',
                    store_tokens=self.store_creds,
                )
                auth_url, csrf_token = self.oauth.get_authorization_url('http://localhost')#csrf_token needs to be checked with assert
                auth_code=self.print_instructions_get_auth_code(auth_url)
                access_token, refresh_token=self.oauth.authenticate(auth_code)
                self.store_creds(access_token,refresh_token)

            b_auth.authenticated_client = Client(self.oauth)
            root_folder = b_auth.authenticated_client.folder('0')
            folder_content=root_folder.get_items(limit=100, offset=0)
            for i in folder_content:
                if i.name=='_SafeDrive_demo_nm':
                    b_auth.app_folder=i
            if b_auth.app_folder is None:
                b_auth.app_folder=root_folder.create_subfolder('_SafeDrive_demo_nm')
            return (b_auth.authenticated_client,b_auth.app_folder)
        else:
            #print('auth returning ready thing... ')
            return (b_auth.authenticated_client,b_auth.app_folder)
    def store_creds(self,access_token, refresh_token):
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, 'Bcredentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,'bc')
        if not os.path.exists(credential_path):
            os.mknod(credential_path)
        with open(credential_path, "w") as f:
            f.write(access_token+'\n'+refresh_token);

    def stored_creds_exist(self):
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, 'Bcredentials')
        credential_path = os.path.join(credential_dir,'bc')
        if not os.path.exists(credential_path):
            return False
        else:
            return True

        access_token, refresh_token = oauth.authenticate('YOUR_AUTH_CODE')

    def get_stored_creds(self):
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, 'Bcredentials')
        credential_path = os.path.join(credential_dir,'bc')
        with open (credential_path,'r') as f :
            access_token=f.readline().strip()
            refresh_token=f.readline().strip()
        
        return (access_token,refresh_token)

    def print_instructions_get_auth_code(self,url):
        print('\n1-Navigate to the following URL:\n')
        print(url)
        print('\n2-Authenticate SafeDrive, you will be directed to new URL (non existent page)')
        print('\n3-Copy the code that appears after \'&Code=\' in the new URL, and paste it here')
        
        auth_code=input()
        return auth_code

print('now')
a=b_auth().get_authenticated_client()
print(a)
print('----')