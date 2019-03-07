import json
import IBUS

from .PLAT_SYSDao import SystemDao as DAO
from util import CommonHelp


def addSystemDict(sid, cmd, datas):
    """添加数据字典"""
    errorCode = -1
    errorMsg = ""
    valueName = ""
    if CommonHelp.hasKey("dictid", datas) == False or datas["dictid"] == "":
        errorCode = -1
        errorMsg = "数据字典的标识符不能为空"

    elif CommonHelp.hasKey("value", datas) == False or datas["value"] == "":
        errorCode = -2
        errorMsg = "数据字典的数值不能为空"

    elif DAO.uniqueSystemDict(datas["dictid"], datas["value"]) == False:
        errorCode = -3
        errorMsg = "模块名称不能重复"

    elif CommonHelp.hasKey("valueName", datas) == True:
        valueName = datas["valueName"]

    if errorMsg == "":
        result = DAO.addSystemDict(datas["dictid"], datas["value"], valueName)
        if (result > 0):
            errorCode = 0
            errorMsg = "操作成功"
        else:
            errorCode = -1003
            errorMsg = "操作失败"

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


def updateSystemDict(sid, cmd, datas):
    """修改数据字典"""
    errorCode = -1
    errorMsg = ""
    if CommonHelp.hasKey("dictid", datas) == False or datas["dictid"] == "":
        errorCode = -1
        errorMsg = "数据字典的标识符不能为空"
    elif CommonHelp.hasKey("oldValue", datas) == False or datas["oldValue"] == "":
        errorCode = -2
        errorMsg = "数据字典的数值不能为空"
    elif CommonHelp.hasKey("newValue", datas) == False or datas["newValue"] == "":
        errorCode = -3
        errorMsg = "数据字典修改的值不能为空"
    elif CommonHelp.hasKey("valueName", datas) == False:
        errorCode = -4
        errorMsg = "数据字典修改值描述不能为空"

    elif DAO.uniqueSystemDict(datas["dictid"], datas["oldValue"]):
        errorCode = -5
        errorMsg = "数据字典的标识符下数值不存在"
    else:
        if datas["oldValue"] == datas["newValue"]:
            pass
        elif not DAO.uniqueSystemDict(datas["dictid"], datas["newValue"]):
            errorCode = -6
            errorMsg = "名称已存在"

    # todo: desc:增加相同值添加时的信息输出 modifyBy：zuxiaojun  date：20180504
    if errorMsg == "":
        res = DAO.selectCommonDict(datas["newValue"], datas["valueName"], datas["dictid"])
        if res:
            errorCode = 0
            errorMsg = "操作成功"
        else:
            result = DAO.updateSystemDict(datas["newValue"], datas["valueName"], datas["dictid"], datas["oldValue"])
            if (result > 0):
                errorCode = 0
                errorMsg = "操作成功"
            else:
                errorCode = -1003
                errorMsg = "操作失败"

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }

def deleteSystemDict(sid, cmd, datas):
    """删除数据字典"""
    errorCode = -1
    errorMsg = ""
    value = ""
    if CommonHelp.hasKey("dictid", datas) == False or datas["dictid"] == "":
        errorCode = -1
        errorMsg = "数据字典的标识符不能为空"

    elif not (CommonHelp.hasKey("value", datas) == False or datas["value"] == ""):
        if DAO.uniqueSystemDict(datas["dictid"], datas["value"]) == True:
            errorCode = -2
            errorMsg = "数据字典的标识符下数值不能不存在"
        else:
            value = datas["value"]

    if errorMsg == "":
        result = DAO.deleteSystemDict(datas["dictid"], value)
        if (result > 0):
            errorCode = 0;
            errorMsg = "操作成功"
        else:
            errorCode = -1003
            errorMsg = "操作失败"

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


def getSystemDict(sid, cmd, datas):
    """获取数据字典"""
    errorMsg = ""
    if CommonHelp.hasKey("dictid", datas) == False or datas["dictid"] == "":
        errorCode = -1
        errorMsg = "数据字典的标识符不能为空"

    if errorMsg == "":
        data = DAO.getSystemDict( datas["dictid"])
        jsonData = []
        for row in data:
            result = {}
            result['value'] = row['value']
            result['valueName'] = row['valueName']
            jsonData.append(result)

        return {
            "errorCode": 0,
            "errorMsg": "操作成功",
            "return": {
                "table": jsonData
            }
        }
    else:
        return {
            "errorCode": errorCode,
            "errorMsg": errorMsg
        }

def getErrorMsg(sid, cmd, datas):
    """获取服务错误码描述"""
    errorCode = -1
    errorMsg = ""
    if (datas == ""):
        errorCode = -1
        errorMsg = "参数不能为空"

    if not isinstance(datas, dict):
        errorCode = -2
        errorMsg = "参数无效"

    if CommonHelp.hasKey("url", datas) == False or datas["url"] == "":
        errorCode = -3
        errorMsg = "URL地址不能为空"

    elif CommonHelp.hasKey("errorCode", datas) == False:
        errorCode = -4
        errorMsg = "错误码不能为空"

    elif not isinstance(datas["errorCode"], int):
        errorCode = -5
        errorMsg = "错误码必须是整数类型"

    if errorMsg == "":
        result = DAO.getErrorMsg(datas["url"], datas["errorCode"])
        if (result != ""):
            return {
                "errorCode": 0,
                # "errorMsg": "操作成功",

                "return": {
                    "msg": result
                }
            }
        else:
            errorCode = -6
            errorMsg = "没有数据"

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }

def readSql(sid, cmd, datas):
    """执行读SQL命令"""
    errorCode = -1
    errorMsg = ""
    if (datas == ""):
        errorCode = -1
        errorMsg = "参数不能为空"

    if not isinstance(datas, dict):
        errorCode = -2
        errorMsg = "参数无效"

    if CommonHelp.hasKeyNotEmpty("sql", datas) == False:
        errorCode = -3  #执行读SQL命令
        errorMsg = "执行SQL语句不存在"

    if errorMsg == "":
        try:
            data = DAO.readSql(datas["sql"])
        except Exception as e:
            return {
                "errorCode": -1002,
                "errorMsg": str(e)
            }

        if data and len(data) > 0:
            data = CommonHelp.getFormatData(data)
        else:
            return {
                    "errorCode": -1001,
                    "errorMsg": "not data"
            }

        return {
            "errorCode": 0,
            "return": data
        }
    else:
        return {
            "errorCode": errorCode,
            "errorMsg": errorMsg
        }


def witerSql(sid, cmd, datas):
    """执行写SQL命令"""
    errorCode = -1
    errorMsg = ""
    if (datas == ""):
        errorCode = -1
        errorMsg = "参数不能为空"

    if not isinstance(datas, dict):
        errorCode = -2
        errorMsg = "参数无效"

    if CommonHelp.hasKeyNotEmpty("sql", datas) == False:
        errorCode = -3  #执行的sql语句不能为空
        errorMsg = "执行SQL语句不存在"

    if errorMsg == "":
        data = DAO.witerSql(datas["sql"])

        return {
            "errorCode": 0,
            "return": {
                "data": data
            }
        }
    else:
        return {
            "errorCode": errorCode,
            "errorMsg": errorMsg
        }


def main(sid, cmd, datas):
    """程序入口"""
    print("module PLAT_System is started!")
    return {
        "errorCode": 0,
        "return": "module PLAT_System is started!"
    }


def onEvent(event, datas):
    """处理事件/事件响应"""
    # if(event == ""): #任务管理
    #     pass

"""系统模块"""
servers = []
servers.append(IBUS.IFS_SERVER("run", False, "private", "系统启动", main))
servers.append(IBUS.IFS_SERVER("addSystemDict", False, "public", "添加数据字典", addSystemDict))
servers.append(IBUS.IFS_SERVER("updateSystemDict", False, "public", "修改数据字典", updateSystemDict))
servers.append(IBUS.IFS_SERVER("deleteSystemDict", False, "public", "删除数据字典", deleteSystemDict))
servers.append(IBUS.IFS_SERVER("getSystemDict", False, "public", "获取数据字典", getSystemDict))
servers.append(IBUS.IFS_SERVER("getErrorMsg", False, "public", "获取服务错误码描述", getErrorMsg))
servers.append(IBUS.IFS_SERVER("readSql", False, "public", "执行读SQL命令", readSql))
servers.append(IBUS.IFS_SERVER("witerSql", False, "public", "执行写SQL命令", witerSql))

IBUS.addServer("PLAT_System", servers)

#事件
events = []
events.append(IBUS.IF_ENENT(onEvent))
IBUS.addEvent(events)