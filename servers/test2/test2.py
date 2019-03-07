# import sys
# sys.path.append("..")
#import os
#sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__))))
import IBUS
import json

def fun1(sid, cmd, datas):
    #事件请求
    IBUS.event("test2", 0, "fun1", "buferr is err--------------------!")
    return {'errorCode':0, 'return':{'a':'test2:fun1','b':1000}}

def fun2(sid, cmd, datas):
    req = {}
    r = IBUS.RPC("test2", "http://172.168.1.210:3000", "/RESTful/users/checkSession", "",  req)
    return "{'errorCode':0,'return':{'a':'test2:fun2','b':1000}}"

def fun3(sid, cmd, datas):
    return "{'errorCode':0,'return':{'a':'test2:fun3','b':1000}}"

def onEvent(event, datas):
    """处理事件/事件响应"""
    # if(event == ""): #任务管理
    #     pass

servers = []
servers.append(IBUS.IFS_SERVER("fun1", False, "private", "help", fun1))
servers.append(IBUS.IFS_SERVER("fun2", False, "private", "help", fun2))
servers.append(IBUS.IFS_SERVER("fun3", False, "private", "help", fun3))

IBUS.addServer("test2",servers)

#事件
events = []
events.append(IBUS.IF_ENENT(onEvent))
IBUS.addEvent(events)




