import json
import IBUS


def main(sid, cmd, datas):
    """程序入口"""
    print("module PLAT_MSG is started!")
    return {
        "errorCode": 0,
        "return": "module PLAT_MSG is started!"
    }

def onEvent(event, datas):
    """处理事件/事件响应"""
    # if(event == ""): #任务管理
    #     pass

"""消息管理"""
servers = []
servers.append(IBUS.IFS_SERVER("run", False, "private", "系统启动", main))

IBUS.addServer("PLAT_MSG", servers)

#事件
events = []
events.append(IBUS.IF_ENENT(onEvent))
IBUS.addEvent(events)