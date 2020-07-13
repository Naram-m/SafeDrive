from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import timeit
from SSSA import sssa
from string import ascii_uppercase
from string import ascii_lowercase
from string import digits
from random import choice

from db_sync.db_share_downloader import db_share_downloader
from gd_sync.gd_share_downloader import gd_share_downloader
from b_sync.b_share_downloader import b_share_downloader


import os


class encryption_module:

    cipher=None
    key=''

    home=os.path.expanduser('~')
    cloud_paths=[
    home+"/Desktop/Dropbox",
    home+"/Desktop/GoogleDrive",
    home+"/Desktop/Box",
    ]

    def __init__(self,available_clouds=[]):
        self.available_clouds=available_clouds
        shares=[]
        i=0
        ##first count
        for cloud in self.cloud_paths:
            try:
                a=open(cloud+'/ss_'+str(i),'r',encoding='utf8')
                shares.append(a.read())
                a.close()
            except Exception as e:
                pass

            if len(shares) >=2:
                # print("reconstructing a key ... ")
                self.set_key(shares)
                break # 2 is enough
            i+=1
        
        
        if len(shares) == 0 :
            print ('no enough shares found locally, checking the cloud ...')
            self.download_shares_from_cloud(self.available_clouds)

        ##second count
        shares=[]
        i=0
        for cloud in self.cloud_paths:
            try:
                a=open(cloud+'/ss_'+str(i),'r',encoding='utf8')
                shares.append(a.read())
                a.close()
            except Exception as e:
                pass

            if len(shares) >=2:
                # print("reconstructing a key ... ")
                self.set_key(shares)
                break # 2 is enough
            i+=1
        

        if len(shares) == 0 :
            print ('no enough shares found on clouds, initiating and uploading ...')
            self.init_key_and_shares()
            print("shares written and key set ")
            #from shares_uplo
            self.upload_shares_to_cloud(self.available_clouds)

    def init_key_and_shares(self):
        sss_obj=sssa()
        # specific to 2,3 arch
        encryption_module.key=self.get_16B_rand_str()
        #print(">>>\n\n key :: \n\n",encryption_module.key)
        shares=sss_obj.create(2,3,encryption_module.key)

        i=0
        for share in shares:
            #print ("share:  ",share)
            try:
                a=open(self.cloud_paths[i]+'/ss_'+str(i),"w")
                a.write(share)
            except Exception as e :
                print ("could not write a share :",e)
            i+=1

    def set_key(self,shares):
        encryption_module.key=bytes(sssa().combine(shares),'utf8')
        
    def encrypt_meta(self,path):
        with open (path,'rb') as f:
            data=f.read()
        cipher = AES.new(encryption_module.key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        file_out = open(path+'.enc', "wb")
        [ file_out.write(x) for x in (cipher.nonce, tag, ciphertext) ]

    def encrypt_(self,data):

        #print('called')
        # with open (path,'rb') as f:
        #     data=f.read()

        #print('after opening a file')

        cipher = AES.new(encryption_module.key, AES.MODE_EAX)

        ciphertext, tag = cipher.encrypt_and_digest(data)
        #file_out = open(path+'.enc', "wb")
        e_data=cipher.nonce + tag + ciphertext
        return e_data
        #[ file_out.write(x) for x in (cipher.nonce, tag, ciphertext) ]

    def decrypt_(self,data):
        ##print('decrypt is called with ',path)
        nonce=data[0:16]
        tag=data[16:32]
        ciphertext=data[32:]

        # nonce, tag, ciphertext = [ file_in.read(x) for x in (16, 16, -1) ]

        cipher = AES.new(encryption_module.key, AES.MODE_EAX, nonce)
        data = cipher.decrypt_and_verify(ciphertext, tag)


        return data
        
    def get_16B_rand_str(self):
        all_case=[]
        for L,l,d in zip(ascii_uppercase,ascii_lowercase,digits):
            all_case.append(L)
            all_case.append(l)
            all_case.append(d)
        a=''.join(choice(all_case) for i in range(16))

        return (bytes(a,'utf8'))

    def download_shares_from_cloud(self,available_clouds):
        for ac in available_clouds:
            if 'Dropbox' in ac:
                try:
                    a=db_share_downloader (local_path=ac+'/ss_0')
                except Exception as e:
                    print(e)
            elif 'GoogleDrive' in ac:
                try:
                    b=gd_share_downloader(local_path=ac+'/ss_1')
                except Exception as e:
                    print(e)                   
            elif 'Box' in ac:
                try:
                    c=b_share_downloader(local_path=ac+'/ss_2')
                except Exception as e:
                    print (e)

    def upload_shares_to_cloud(self,available_clouds):

        from db_sync.db_uploader import db_uploader
        from gd_sync.gd_uploader import gd_uploader
        from b_sync.b_uploader import b_uploader

        for ac in  available_clouds:
            if 'Dropbox' in ac:
                a=db_uploader (path=ac+'/ss_0',dest='/ss_0')
                a.start()
            elif 'GoogleDrive' in ac:
                b=gd_uploader(path=ac+'/ss_1')
                b.start()
            elif 'Box' in ac:
                c=b_uploader(path=ac+'/ss_2')
                c.start()

        a.join()
        b.join()
        c.join()