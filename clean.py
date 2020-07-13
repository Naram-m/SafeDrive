import os
import shutil

home=os.path.expanduser('~')

shutil.rmtree(home+'/Desktop/Dropbox')
shutil.rmtree(home+'/Desktop/GoogleDrive')
shutil.rmtree(home+'/Desktop/Box')


os.mkdir(home+'/Desktop/Dropbox')
os.mkdir(home+'/Desktop/Dropbox/FSFolder')
os.mkdir(home+'/Desktop/GoogleDrive')
os.mkdir(home+'/Desktop/GoogleDrive/FSFolder')
os.mkdir(home+'/Desktop/Box')
os.mkdir(home+'/Desktop/Box/FSFolder')


