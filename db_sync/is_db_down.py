from dropbox import DropboxOAuth2FlowNoRedirect
import dropbox
import os


home_dir = os.path.expanduser('~')
credential_dir = os.path.join(home_dir, 'DBcredentials')
credential_path = os.path.join(credential_dir,'dbc')
with open(credential_path, "r") as f:
    AT=f.read()
    dbAccount=dropbox.Dropbox(AT)
    print(dbAccount.users_get_current_account())