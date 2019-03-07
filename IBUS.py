import urllib
import json

class IFS_SERVER:
    def __init__(self, name, isStartup, type, help, server):
        self.name = name
        self.isStartup = isStartup
        self.type = type
        self.help = help
        self.server = server

class IF_ENENT:
    def __init__(self, onEvent):
        self.onEvent = onEvent

class IFS_IBUS:
    SERVERS = []
    EVENTS = []

def addEvent(event):
    IFS_IBUS.EVENTS.append(event)

def addServer(moduleName, server):
    for s in server:
        s.name = moduleName + "/" + s.name
    IFS_IBUS.SERVERS.append(server)

def addServerFun(moduleName, server):
    for s in server:
        s.name = moduleName + "/" + s.name
    IFS_IBUS.SERVERS.append(server)


import base64
def RPC(sid, host, cmd, headers, datas):
    if host == "local":
        for servers in IFS_IBUS.SERVERS:
            for s in servers:
                if s.name == cmd:
                    if datas['apikey'] == "":
                        datas["request"]["nodeId"] = "admin"
                    else:
                        apikey = base64.b64decode(datas['apikey']).decode("utf8")
                        datas["request"]["nodeId"] = apikey.split("&")[1]

                    return s.server(sid, cmd, datas['request'])
        else:
            # todo 修改状态码 date:20180420 by:zuxiaojun desc:修改错误状态码
            return {
                # "errorCode": -1004,
                "errorCode": -1888,
                "errorMsg": '当前请求路径不存在'
            }
    else:
        try:
            reqString = json.dumps(datas)
            headers = {'Content-Type': 'application/json'}
            req = urllib.request.Request(host+cmd, headers = headers, data = reqString.encode(encoding='UTF8'))
            response = urllib.request.urlopen(req)
            return response.read().decode('utf8')
        except Exception as e:
            # todo 修改状态码 date:20180420 by:zuxiaojun desc:修改错误状态码
            return json.dumps({
                # "errorCode": -1004,
                "errorCode": -1999,
                "errorMsg": "请求异常"
            })


def event(sid, mode, event, datas):
     """ 事件
     功能说明：
     当模块产生了相应的事件时应当调用该回调函数，这个函数会把该事件广播到系统所用模块，也可以推送到其它Node节点上去。
     sid:   模块名称
     mode:  事件通知模式（=0：系统内部广播， =1：ESB总线推送， =2：系统内部广播与ESB推送）
     event：事件标识符
     datas： 事件数据
     """
     if (mode == 0): #系统内部广播
         for servers in IFS_IBUS.EVENTS:
             for s in servers:
                 s.onEvent(sid + "#" + event, datas)

     if (mode == 1): #ESB总线推送
         pass
     if(mode == 2): #系统内部广播与ESB推送
         for servers in IFS_IBUS.SERVERS:
             for s in servers:
                 s.onEvent(sid + "#" + event, datas)

def startupModules():
    #开机运行启动程序服务
    for servers in IFS_IBUS.SERVERS:
        for s in servers:
            if s.isStartup:
                s.server("", s.name, "")


