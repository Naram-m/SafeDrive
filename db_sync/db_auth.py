from dropbox import DropboxOAuth2FlowNoRedirect
import dropbox
import os


def get_DB_account():
    with open ("db_sync/failure_sim","r") as f:
        content=f.read()
    if content == '1':
        return None
    else:
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, 'DBcredentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)

        credential_path = os.path.join(credential_dir,'dbc')
        if not os.path.exists(credential_path):
            os.mknod(credential_path)
            noAT=True
        else: #todo :check if empty
            noAT=False
        with open(credential_path, "r") as f:
            AT=f.read();
        if not noAT:
            dbAccount=dropbox.Dropbox(AT);
        if noAT:
            auth_flow = DropboxOAuth2FlowNoRedirect("5bn928fpx8nb3ni", "kbdl7zxdlgrvri5")
            authorize_url = auth_flow.start()
            print ("1. Go to: " + authorize_url)
            print ("2. Click \"Allow\" (you might have to log in first).")
            print ("3. Copy the authorization code.")
            auth_code = input("Enter the authorization code here: ").strip()
            try:
                oauth_result = auth_flow.finish(auth_code)
            except Exception as e:
                print('Error: %s' % (e,))
                return
            dbAccount=dropbox.Dropbox(oauth_result.access_token)
            print(oauth_result.access_token)
            credential_path = os.path.join(credential_dir,'dbc')
            with open(credential_path, "w") as f:
                f.write(oauth_result.access_token);
        return dbAccount
