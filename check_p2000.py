#!/usr/bin/env python
#_*_ coding:utf-8 _*_
'''
Created on 2017年6月21日

@author: Alex
@version: 1.1
@copyright: 青鸟技术联盟
@license: GPLv3
'''
try: 
    import xml.etree.cElementTree as ET 
except ImportError: 
    import xml.etree.ElementTree as ET 
  
try:
    import urllib2,sys,optparse,hashlib
except Exception,e:
    print e
    sys.exit()
#Nagios 返回code    
STATUS_OK=0
STATUS_Warning=1
STATUS_Critical=2
STATUS_Unknown=3


optp = optparse.OptionParser()
optp.add_option('-H', help=u'P200存储管理IP地址或者FQDN', dest='host',metavar='10.0.0.1')
optp.add_option('-u', help=u'连接存储用户名，建议使用只读用户', default='manager',dest='user', metavar='manager')
optp.add_option('-p', help=u'连接存储用户名密码',default='!manager', dest='passwd', metavar='!manager')
optp.add_option('-P', help=u'管理页面端口', default=80,dest='port', metavar='80')
optp.add_option('-m', help=u'页面连接模式https|http,如选择HTTPS，请确认主机python是否支持SSL', default='http',dest='mode', metavar='http')
optp.add_option('-o', help=u'监控项目:status|disk|expander|controller|named-volume|named-vdisk|vdisk|volume|sensor|events', dest='option', metavar='status')
optp.add_option('-e', help=u'扩展选项，使用-e help 查看详细的说明',default='iops',dest='extend', metavar='iops')
optp.add_option('-n', help=u'name，当使用named-volume|named-vdisk次参数有效，具体的设备名',dest='name', metavar='vd0')
optp.add_option('-c', help=u'是否启动告警，默认不启用',default=0,dest='Calculation', metavar='0')
optp.add_option('--warn', help=u'警告阈值   【:80 表示小于80告警 】   【80: 表示大于80告警，默认可以去掉:号】【:80: 表示值等于80进行告警】 ', default=50,dest='warn', metavar='50')
optp.add_option('--crit', help=u'严重阈值  设定方式参照以上说明', default=70,dest='crit', metavar='70')
optp.add_option('--ok', help=u'正常状态判定，特使情况使用，例如卷的所属控制器状态判断[:B:]',default=0,dest='ok', metavar='B')
opts, args = optp.parse_args()
if opts.extend =='help':
    print u"""
    根据存储固件版本的不同，参数可能出现不同，请参考官方API手册
Disk支持的项目,后面带-1的选项根据自己的port来变换
    iops  :查看磁盘当前的IOPS，根据阈值报警
    bytes-per-second-numeric  :磁盘每秒的传输大小，单位为字节，
    number-of-reads    :Number of Reads
    number-of-writes    :Number of Writes
    io-timeout-count-1   :I/O Timeout Count Port 1
    no-response-count-1  :No-response Count Port 1
    spinup-retry-count-1    :Spinup Retry Count Port 1
    number-of-media-errors-1    :Number of Media Errors Port 1
    number-of-nonmedia-errors-1    :Number of Non-media Errors Port 1
    mber-of-block-reassigns-1    :Number of Block Reassignments Port 1
    number-of-bad-blocks-1    :Number of Bad Blocks Port 1 
controller 选项支持的扩展参数 
    cpu-load    CPU Load
    power-on-time  Power On Time (Secs)
    write-cache-used    Write Cache Used
    bytes-per-second    Bytes per second
    bytes-per-second-numeric    Bytes per second
    iops    IOPS
    number-of-reads    Number of Reads
    read-cache-hits    Read Cache Hits
    read-cache-misses    Read Cache Misses
    number-of-writes    Number of Writes
    write-cache-hits    Write Cache Hits
    write-cache-misses   Write Cache Misses
    data-read    Data Read
    data-read-numeric    Data Read
    data-written    Data Written
    data-written-numeric    Data Written
Vdisk 支持的扩展扩展参数
    bytes-per-second   Bytes per second
    bytes-per-second-numeric    Bytes per second
    iops    IOPS
    number-of-reads    Number of Reads
    number-of-writes    Number of Writes
    data-read    Data Read    
    data-read-numeric    Data Read
    data-written    Data Written
    data-written-numeric   Data Written
    avg-read-rsp-time
    avg-write-rsp-time
volume 支持的扩展扩展参数
    bytes-per-second   Bytes per second
    bytes-per-second-numeric    Bytes per second
    iops    IOPS
    number-of-reads    Number of Reads
    number-of-writes    Number of Writes
    data-read    Data Read    
    data-read-numeric    Data Read
    data-written    Data Written
    data-written-numeric   Data Written
    write-cache-hits    Write Cache Hits
    write-cache-misses    Write Cache Misses
    read-cache-hits    Read Cache Hits
    read-cache-misses    Read Cache Misses
    small-destages    Small Destages
    full-stripe-write-destages    Full Stripe Write Destages
    read-ahead-operations   Read-Ahead Operations
    write-cache-space    Write Cache Space
    write-cache-percent    Write Cache Percentage
named-volume
    size    Size
    size-numeric    Size
    preferred-owner    Preferred Owner
    preferred-owner-numeric  Preferred Owner
    owner     Current Owner
    owner-numeric    Current Owner
    write-policy    Cache Write Policy
    write-policy-numeric    Cache Write Policy
    cache-optimization    Cache Optimization
    cache-optimization-numeric    Cache Optimization
    read-ahead-size    Read Ahead Size
    read-ahead-size-numeric  Read Ahead Size  
    progress    Progress
    progress-numeric    Progress
sensor 
    value   Value
    status   Status
    status-numeric    Status Numeric
    sensor-location    Sensor Location
    sensor-type        Sensor Type
    
"""
    sys.exit(STATUS_Unknown)

if opts.host is None:
    print "You must specify the storage management IP address or FQDN"
    optp.print_help()
    sys.exit(STATUS_Unknown)
    
def GetAuthUrl():
    concatAuth="%s_%s"%(opts.user,opts.passwd)
    md=hashlib.md5()   
    md.update(concatAuth) 
    auth=md.hexdigest()
    authstr="/api/login/%s"%auth
    return authstr

def GetTokenXML(url,authstr):
    try:    
        opener = urllib2.build_opener()
        response = opener.open(url,authstr)
        response_text = response.read()
        return response_text
    except Exception,e:
        print "An unusual error occurred: %s"%e
        sys.exit(STATUS_Unknown)
    

def GetDate(url,token): 
    headers = {
           "User-Agent": "Nagios Monitor Script V1.1",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
           "Accept-Language": "zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3",
           "Accept-Encoding": "gzip, deflate",
           "Cookie": "wbisessionkey=%s; wbiusername=%s"%(token,opts.user),
           "Connection": "keep-alive"}
    try:
        P200_Request = urllib2.Request(url,headers=headers)
        response = urllib2.urlopen(P200_Request)
        response_text = response.read()
        return response_text
    except Exception,e:
        print "An unusual error occurred: %s"%e
        sys.exit(STATUS_Unknown)
    
def FormatURL(option):
    if opts.mode == "http":
        url="http://%s:%s/api/%s"%(opts.host,opts.port,option)
    else:
        url="https://%s:%s/api/%s"%(opts.host,opts.port,option)
    return url

def FormatXML(xml,attribute=['name','response'],tag="PROPERTY"):
    try:
        tree = ET.fromstring(xml)
        lst_node = tree.getiterator(tag)  
        re=[]
        for node in lst_node:
            if node.attrib[attribute[0]] == attribute[1]:
                re.append(node.text)
        if len(re) == 0:
            print "No data was found,Please check the pendant version and other information"
            sys.exit(STATUS_Unknown)
        return re
    except Exception,e:
        print "An unusual error occurred: %s"%e
        sys.exit(STATUS_Unknown)

def MultiElementXML(xml,DictName=['name','durable-id'],tag="OBJECT"):
    try:
        tree = ET.fromstring(xml)
        all_object = tree.getiterator(tag)
        re={}
        for objectxml in all_object:
            for nodexml in objectxml:
                if nodexml.attrib[DictName[0]] == DictName[1]:
                    DName=nodexml.text
                if nodexml.attrib['name'] == opts.extend:
                    re[DName]=nodexml.text
        if len(re) == 0:
            print "No data was found,Please check the pendant version and other information"
            sys.exit(STATUS_Unknown)
        return re
    except Exception,e:
        print "An unusual error occurred: %s"%e
        sys.exit(STATUS_Unknown)
        
def events(xml,DictName=['name','erity-numeric'],tag="OBJECT"):
    try:
        tree = ET.fromstring(xml)
        all_object = tree.getiterator(tag)
        re=[]
        for objectxml in all_object:
            for nodexml in objectxml:
                if nodexml.attrib[DictName[0]] == DictName[1]:
                    if nodexml.text == 0:
                        break
                if nodexml.attrib['name'] == 'message':
                    re.append(nodexml.text)
        if len(re) == 0:
            return_str="OK-No new alarm logs are generated"
        else:
            return_str="Critical-%s" %('\r\n'.join(re))
        return return_str
    except Exception,e:
        print "An unusual error occurred: %s"%e
        sys.exit(STATUS_Unknown)
        
def GetToken():        
    tokenxml=GetTokenXML(FormatURL("/login"),GetAuthUrl())
    token=FormatXML(tokenxml)
    return token[0]


def Ok_Check(textlist,Okvalue=['OK','ok','Ok']):
    for index in range(len(Okvalue)):
        textlist = [e for e in textlist if e!=Okvalue[index]]
    if len(textlist) ==0:
        return True
    else:
        return textlist
def Compare(value,threshold,Compare='gt'):
    if Compare=='gt':
        if int(value) > int(threshold):
            return True
        else:
            return False
    elif Compare=='lt':
        if int(value) < int(threshold):
            return True
        else:
            return False
    else:
        if len(value) == len(threshold):
            if value in threshold:
                return True
            else:
                return False
        else:
            return False
    
def count(key,value):
    try:
        if str(opts.ok).count(':') ==2:
            ok=str(opts.ok).strip(':')
            if Compare(value,ok,'eq'):
                rstr="OK"
            else:
                rstr="Critical"
        elif str(opts.crit).count(':') ==2:
            crit=str(opts.crit).strip(':')
            if Compare(value,crit,'eq'):
                rstr="Critical"
            else:
                rstr="OK"
        elif str(opts.warn).count(':') ==2:
            warn=str(opts.warn).strip(':')
            if Compare(value,warn,'eq'):
                rstr="Warning"
            else:
                rstr="OK"
        elif str(opts.crit).isdigit() and str(opts.warn).isdigit():
            int(value)
            if Compare(value,opts.crit,'gt'):
                rstr="Critical"
            elif Compare(value,opts.warn,'gt'):
                rstr="Warning"
            else:
                rstr="OK"
        else:
            int(value)
            if opts.crit[:1] == ':':
                crit=opts.crit[1:]
                warn=str(opts.warn).strip(':')
                int(crit)
                if Compare(value,crit,'lt'):
                    rstr="Critical"
                elif Compare(value,warn,'lt'):
                    rstr="Warning"
                else:
                    rstr="OK"
            elif opts.crit[-1:] == ':':
                crit=opts.crit[:-1]
                warn=str(opts.warn).strip(':')
                if Compare(value,crit,'gt'):
                    rstr="Critical"
                elif Compare(value,warn,'gt'):
                    rstr="Warning"
                else:
                    rstr="OK"
            else:
                int(opts.crit)
    except:
        rstr="Unknown"
    
    return_str="%s-%s %s is %s"%(rstr,key,opts.extend,value)
    return return_str    
    
def dataproce(dicts):
    return_Str=[]
    return_perf=[]
    try:
        war=str(opts.warn).strip(':')
        crit=str(opts.crit).strip(':')
    except:
        war=opts.warn
        crit=opts.crit
        
    for key in dicts:
        if opts.Calculation == 0:
            return_Str.append("%s %s %s"%(key,opts.extend,dicts[key]))
            return_perf.append("%s=%s;;;;"%(key,dicts[key]))
        else:
            return_Str.append(count(key,dicts[key]))
            return_perf.append("%s=%s;%s;%s;;"%(key,dicts[key],war,crit))
            
    rstr="%s | %s"%('\r\n'.join(return_Str),' '.join(return_perf)) 
    return rstr

token=GetToken()
return_Str="Critical-An unusual error occurred: Token was not found"
return_Status=STATUS_Unknown
if len(token) <> 0:
    if opts.option =='disk':
        return_Str=dataproce(MultiElementXML(GetDate(FormatURL('/show/disk-statistics'),token)))
    elif opts.option =='controller':
        return_Str=dataproce(MultiElementXML(GetDate(FormatURL('/show/controller-statistics'),token)))
    elif opts.option =='named-volume':
        if opts.name is None :
            return_Str="Critical-Please use the -n parameter to specify a detailed name"
        else:
            return_Str=dataproce(MultiElementXML(GetDate(FormatURL('/show/volumes/%s'%opts.name),token),DictName=['name','virtual-disk-name']))   
    elif opts.option =='named-vdisk':
        if opts.name is None :
            return_Str="Critical-Please use the -n parameter to specify a detailed name"
        else:
            return_Str=dataproce(MultiElementXML(GetDate(FormatURL('/show/vdisks/%s'%opts.name),token),DictName=['name','name']))   
    elif opts.option =='vdisk':
        return_Str=dataproce(MultiElementXML(GetDate(FormatURL('/show/vdisk-statistics'),token),DictName=['name','name']))   
    elif opts.option =='volume':
        return_Str=dataproce(MultiElementXML(GetDate(FormatURL('/show/volume-statistics'),token),DictName=['name','volume-name']))   
    elif opts.option =='sensor':
        return_Str=dataproce(MultiElementXML(GetDate(FormatURL('/show/sensor-status'),token),DictName=['name','sensor-name']))   
    elif opts.option =='events':
        return_Str=events(GetDate(FormatURL('/show/events/error'),token))   
    elif opts.option =='expander':
        date=Ok_Check(FormatXML(GetDate(FormatURL('/show/expander-status'),token),attribute=['name','elem-status']))
        if date == True:
            return_Str="OK-All expander Status is OK"
        else:
            return_Str="Critical-Have %s expander status has Abnormal"%len(date)
    else:
        date=Ok_Check(FormatXML(GetDate(FormatURL('/show/enclosure-status'),token),attribute=['name','status']))
        if date == True:
            return_Str="OK-All Status is OK"
        else:
            return_Str="Critical-Have %s Hardware status has Abnormal"%len(date)

if 'Critical' in return_Str:
    return_Status=STATUS_Critical
elif 'Warning' in return_Str:
    return_Status=STATUS_Warning
elif 'Unknown' in return_Str:
    return_Status=STATUS_Unknown
else:
    return_Status=STATUS_OK
print return_Str
sys.exit(return_Status)