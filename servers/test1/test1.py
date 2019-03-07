# import sys
# sys.path.append("..")
import IBUS
import json
from util import SysHelp

def fun1(sid, cmd, datas):
    req = {
        "apikey": "",
        "request": {
            "projectid": ["1234567"]
        }
    }
    host = ""
    length = len(SysHelp.HOST)
    for index in range(length):
        if SysHelp.HOST[index]["dns"] == "masterExtend001":
            host = SysHelp.HOST[index]["host"]
            break

    r = IBUS.RPC("RESTful", host, "/ibus/PLAT_Enterprise/getProjectData", "", req)
    return r
    # req = {}
    # r = IBUS.RPC("test1", "http://172.168.1.210:3000", "/RESTful/users/checkSession", "", req)
    # # r = IBUS.RPC("test1", "/ESBREST/EXTEND002/IBUS/users/checkSession", "", req)
    #
    # return "{'errorCode':0,'return':{'a':'test1:fun1','b':1000}}"


def fun2(sid, cmd, datas):
    return "{'errorCode':0,'return':{'a':'test1:fun2','b':1000}}"


def fun3(sid, cmd, datas):
    return "{'errorCode':0,'return':{'a':'test1:fun3','b':1000}}"


def onEvent(event, datas):
    """处理事件"""
    # if(event == ""): #任务管理
    #     pass


servers = []
servers.append(IBUS.IFS_SERVER("fun1", False, "private", "help", fun1))
servers.append(IBUS.IFS_SERVER("fun2", False, "private", "help", fun2))
servers.append(IBUS.IFS_SERVER("fun3", False, "private", "help", fun3))
IBUS.addServer("test1", servers)

events = []
events.append(IBUS.IF_ENENT(onEvent))
IBUS.addEvent(events)





