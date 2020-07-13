from enc import encryption_module
import time
from SSSA import sssa
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from string import ascii_uppercase
from string import ascii_lowercase
from string import digits
from random import choice
from anytree import Node, RenderTree, AsciiStyle, findall_by_attr, Resolver
import pickle
import os
import math

en =encryption_module()

cloud_paths=[
"/home/parallels/Desktop/Dropbox",
"/home/parallels/Desktop/GoogleDrive",
"/home/parallels/Desktop/OneDrive",
]

## def get_16B_rand_str():
    #     all_case=[]
    #     for L,l,d in zip(ascii_uppercase,ascii_lowercase,digits):
    #         all_case.append(L)
    #         all_case.append(l)
    #         all_case.append(d)
    #     a=''.join(choice(all_case) for i in range(16))
    #
    #     return (a)
    #
    #
    # key=get_16B_rand_str()
    # b_key=bytes(key,'utf-8')
    # print ('this is key: ',key, '\nthis is its len,',len(key))
    # print ('this is b_key: ',b_key, '\nthis is its len,',len(b_key))
    #
    # shares=sssa().create(2,3,key)
    #
    # i=0
    # for share in shares:
    #     a=open('./share_'+str(i),'w')
    #     a.write(share)
    #     print('wrote this share:', share)
    #     i+=1
    #
    # time.sleep(3)
    # print('encrypting some file')
    # with open ('./test_en.txt','rb') as f:
    #     data=f.read()
    #
    #
    # cipher = AES.new(b_key, AES.MODE_EAX)
    #
    # ciphertext, tag = cipher.encrypt_and_digest(data)
    # file_out = open('./test_en.txt.enc', "wb")
    # [ file_out.write(x) for x in (cipher.nonce, tag, ciphertext) ]
    # file_out.close()
    #
    # time.sleep(3)


## testing to encrypt and decrypt object file 
    # print('now reconstructing key and reading file')
    # r_s=[]

    # for i in range(0,3):
    #     a=open(cloud_paths[i]+'/ss_'+str(i),'r')
    #     s=a.read()
    #     r_s.append(s)
    #     print('read')

    # print('recinstructing: ')
    # rkey=sssa().combine(r_s)
    # b_rkey=bytes(rkey,'utf-8')

    # #1- make the object file 
    # tree=Node("root",_type="dir")
    # fsf= open("/home/parallels/Documents/TestFSF","wb+")
    # pickle.dump(tree, fsf,4)
    # #2- read it, encrypt, and write to another file
    # with open ("/home/parallels/Documents/TestFSF",'rb') as fsf:
    #     a=bytes(fsf.read())
    #     print('this is FSF :' ,a)
    #     with open ('/home/parallels/Documents/TestFSF.enc','wb') as fsfe:
    #         fsfe.write(en.encrypt_(a))

    # #3- read that other file and decrypt it 
    # file_in = open('/home/parallels/Documents/TestFSF.enc', "rb")
    # d=file_in.read()
    # file_in.close()
    # nonce=d[0:16]
    # tag=d[16:32]
    # ciphertext=d[32:]
    # # nonce, tag, ciphertext = [ file_in.read(x) for x in (16, 16, -1) ]

    # cipher = AES.new(b_rkey, AES.MODE_EAX, nonce)
    # try:
    #     data = cipher.decrypt_and_verify(ciphertext, tag)
    # except Exception as e:
    #     print("     !!!!>> :",e)
    # else:
    #     recon_obje=pickle.loads(data)
    #     print(recon_obje)



# #2- read it, encrypt, and write to another file


# with open ("/home/parallels/Documents/less.txt",'rb') as f:
#     with open ('/home/parallels/Documents/less.txt.enc','wb') as fe:
#         fe.write(en.encrypt_(f.read()))
# print ('done')

## this is file encryption 
path='/home/parallels/Documents/m.txt'
_lmt= 500 * 1024 * 1024
size_=os.stat(path).st_size
trans=math.ceil(size_/_lmt)

with open(path,"rb") as fileobjectfrom:
    with open(path+'.enc',"wb") as encFileobjectTo:
        for i in range (0,trans):
            print(i)
            #print ('iteration :',i,'offsets : ',fileobjectfrom.tell(),'   ',encFileobjectTo.tell()) 
            _by_s=fileobjectfrom.read(_lmt)
            #print ("length read : ", len(_by_s))
            a=encFileobjectTo.write(en.encrypt_(_by_s))
            #print ("length written : ", a)
        #print ('iteration :',i,'offsets : ',fileobjectfrom.tell(),'   ',encFileobjectTo.tell()) 

# time.sleep(3)
# with open(path+'.enc',"rb") as f:
#     with open(path+'.deenc',"wb") as f2:
#         for i in range(0,trans):
#             f2.write(en.decrypt_(f.read(32+_lmt)))
# print ('done ....')