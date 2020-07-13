with open('./ss.txt','r+') as f:
    cloud=f.read().strip()
    if cloud == 'Box':
        f.seek(0)
        f.truncate()
        f.write('Dropbox')