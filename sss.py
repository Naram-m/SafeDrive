from SSSA import sssa

sss_obj=sssa()

key='hello'

shares=sss_obj.create(2,3,key)

# a=int('PRMiwtRq_MJIreENDEz9Ps2wq2Ag4-HPHGbJhRjlwCk=zYepi0fAQXkAaD1goMknXPqHhquuZvKmXBrRVnyr1VU=')


i=0
for share in shares:
    print ("share:  ",share)
    # try:
    #     a=open('./share_'+str(i),"w")
    #     a.write(share)
    # except Exception as e :
    #     print ("errpr",e)
    # i+=1

s=[]

for i in range (0,3):
    try:
        a=open('./share_'+str(i),"r")
        s.append(a.read())
    except Exception as e :
        print ("errpr",e)
    i+=1

print("-------------\n reconstructing using share 1,3")


re_=[s[0],s[1]]
a=sss_obj.combine(re_)

print(a)
