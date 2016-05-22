#!/usr/bin/env python
#coding:UTF8
try:
    import os
    import requests
    import random
    import re
    import json
    import time
    import StringIO
    import sys 
    from random import choice
    from bs4 import BeautifulSoup
    from PIL import Image
except Exception as error:
    print "MISSING SOME MODULE(s)"
    print (error)
    os.system("pip install bs4 requests Image")
    print "TRY TO INSTALL SOME MODs"
    print "PLEASE UPGRADE PIP IF IT DOESN'T WORK "
    print "Restart this Program!"
    exit(-2)
# origin = sys.stdout 
# _STDOUT = open('./bot.log', 'w') 
# sys.stdout = _STDOUT
print """
        Taobao Search Image Bot
"""
#initialization
global url_pool
global curf
global offset
global cur_offset
offset = 0
cur_offset = 0;
curf = 0
url_pool = []
if not os.path.exists("./images/"):
    os.mkdir("./images/")
offset = raw_input("Please input the number of pictures of each type(Default 500)\n")
offset = int(offset if offset.isdigit() and offset > 0 else 500)
print "Enter multiple sets of URL"
_ccount = 0
while True:
    _ccount+=1
    try:
        text = raw_input("URL%d:"%_ccount)
    except:
        print "\nEOF? "
        exit(0)
    if len(text) <= 2:
        break
    else:
        url_pool.append(text)
    
    
#print offset
init_sleep = ''#raw_input("Please input sleep time:(Default : 5)\n")
init_sleep = init_sleep if init_sleep.isdigit() else 5
#解决反爬虫机制
header = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
          'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
          'accept-encoding':'gzip, deflate, sdch'}
ua_list = [];
#获取页面TEXT
def getPage(url,param = None):
    global header
    try:
         print "\nGET >>> "+url;
         html = None
         if param is None:
             html = requests.get(url,headers=header)
         else:
             html = requests.get(url,headers=header,params=param)
        
         if html.status_code > 400:
            print "\nREMOTE ERROR CODE" + html.status_code;
            return None
    except:
         print "\nLOCAL CONNECTION ERROR"
         return None
    
    return html.text
## 获取网页中的Json数据，只限主页搜索页
def getMainPageJson(text):
    json_raw = re.findall(re.compile(r'g_page_config\s=\s(.*);',re.M),text)
    return json.loads(json_raw[0])

#获取文件
def getResource(url):
    global cur_offset
    global offset
    global curf
    print("\nGET >>> "+url)
    try:
        req = requests.get(url,timeout=10)
        binary_file = req.content
        f= StringIO.StringIO(binary_file)
        ####
        ### 图片大小筛选，明显与商品主体不同的图片将不会存储
        ### 1.宽或高比例太大（装饰用图）
        ### 2.宽/高的像素小于450(过小的是其他商品的缩略图，或质量不符合要求的图)
        ####
        im = Image.open(f)
        if im.size[0] < 450 or im.size[1] < 450 or im.size[0]/im.size[1]>8 or im.size[0]/im.size[1] < 0.125:
            print "\nGET <<< USELESS IMG"
            im.close()
            return;
        a= dir(req.raw)
        file_name ='./images/%d/%d.jpg' % (curf,int(round(time.time() * 1000)))
        f= open(file_name,'wb')
        f.write(binary_file)
        f.close()
        if req.status_code >= 400:
            print "\nREV XXX %d" % req.status_code
        else:
            print "\nREV OK (%d:%d/%d)" % (curf,cur_offset,offset) 
    except Exception as error:
        #traceback.print_exc()
        print(str(error))
        print("\nGET IMG ERROR")
    cur_offset += 1

#分析搜索页
def getSearchPg(url,items=0):
    global cur_offset
    global offset
    global curf
    mytext = None
    if items > 0:
        mytext = getPage(url,{'s':items})
    else:
        mytext = getPage(url, None)
    _count = 0
    if mytext is not None:
        itemList   = None #商品ID
        itemspos   = items#当前item浮标
        detailList = None #商品详情
        totalItems = None #商品总数
        _json = getMainPageJson(mytext)
        if _json is None:
            print "Nothing"
        else:
            itemList = _json['mainInfo']['traceInfo']['traceData']['i2iItemNids']
            detailList = _json['mods']['recitem']['data']['items']
            itemspos += _json['mods']['pager']['data']['pageSize']
            totalItems = _json['mods']['pager']['data']['totalCount'];
            ##############################################################
            print "GET ITEMS %d" % _json['mods']['pager']['data']['totalCount']
            print "ITM PER PAGE: %d" % _json['mods']['pager']['data']['pageSize']
            print "CUR PAGE: %d" % _json['mods']['pager']['data']['currentPage']
            #######################################################################
            for i in detailList:
                _count += 1
                if cur_offset > offset:
                    return;
                print  "Item Name:" +i['title']
                getResource("http:" +i['pic_url']) # 获取缩略图
                if re.match(r".*tmall\.com.*", i['detail_url']):
                    tmallImageGet("http:"+i['detail_url'])
                elif re.match(r".*item\.taobao\.com.*", i['detail_url']):
                    taobaoImageGet("http:"+i['detail_url'])
                elif re.match(r".*detail\.ju\.taobao.com.*", i['detail_url']):
                    jhsImageGet("http:"+i['detail_url'])
                else:
                    print "\n"+i['detail_url'];
                    print "GET UNKNOWN SOURCE"
            
            ##分页处理    
            if itemspos < totalItems:
                getSearchPg(url, itemspos)  
    else:
        print "None"
        return 0;

#分析天猫页
def tmallImageGet(url):
    global cur_offset
    global offset
    global curf
    _text = getPage(url)
    json_raw = re.findall(re.compile(r'descUrl":"(.*)","(?=fetchDcUrl|httpsDescUrl )',re.M),_text)
    if len(json_raw) <= 0:
        print "\nGET NO IMG"
        return
    _bs = BeautifulSoup(getPage("http:"+json_raw[0]),"html.parser")
    ppi = _bs.findAll("img")
    for i in ppi:
        if cur_offset > offset:
            return;
        try:
            if i['src'].rfind(".jpg") != -1:
                getResource(i['src'])
            else:
                continue
        except Exception as error:
            return;  
#分析淘宝页
def taobaoImageGet(url):
    global cur_offset
    global offset
    global curf
    _text = getPage(url)
    #print _text
    json_raw = re.findall(re.compile(r"location\.protocol==='http:'\s\?\s'(.*)'\s:",re.M),_text)
    if len(json_raw) <= 0:
        print "\nGET NO IMG"
        return
    _bs = BeautifulSoup(getPage("http:"+json_raw[0]),"html.parser")
    ppi = _bs.findAll("img")
    for i in ppi:
        if cur_offset > offset:
            return;
        try:
            if i['src'].rfind(".jpg") != -1:
                getResource(i['src'])
            else:
                continue
        except Exception as error:
            print(error)
            return;  
#分析聚划算    
def jhsImageGet(url):
    global cur_offset
    global offset
    global curf
    _text = getPage(url)
    #print _text
    json_raw = re.findall(re.compile(r'<div\sclass="infodetail\sks-editor-post\sJ_JuDetailBox"\sdata-url="(.*)">',re.M),_text)
    if len(json_raw) <= 0:
        print "\nGET NO IMG"
        return
    _bs = BeautifulSoup(getPage("http:"+json_raw[0]),"html.parser")
    ppi = _bs.findAll("img")
    for i in ppi:
        if cur_offset > offset:
            return;
        try:
            if i['src'].rfind(".jpg") != -1:
                getResource("http:"+i['src'])
            else:
                continue
        except Exception as error:
            print(error)
            return; 


while len(url_pool) > 0:
    curf += 1
    cur_offset = 0
    if not os.path.exists("./images/%d/" % curf):
        os.mkdir("./images/%d/" % curf)
    
    getSearchPg(url_pool.pop())

print u"\nHi~Finished~~~"
# _STDOUT.close();
        