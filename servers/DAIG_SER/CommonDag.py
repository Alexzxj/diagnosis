import base64
import re
from datetime import datetime
import json
import time
from .DAIG_SERDao import DaigSys as DS
import functools

import IBUS
from flask import g, current_app, Flask
from flask_mail import Mail, Message

def hasKeyData(key, data):
    if(isinstance(data, dict)):
        if key in data.keys() and data[key] != "":
            return True
    return False


def judgeIntType(key, data):
    if data[key] != "":
        if type(data[key]) == int:
            return True
    return False


def judgeDictType(key, data):
    if data[key] != "":
        if type(data[key]) == dict:
            return True
    return False


def judgeListType(key, data):
    if data[key] != "":
        if type(data[key]) == list:
            return True
    return False


def judgeStrIsNum(key, data):
    '''判断字符是否为数字'''
    if data[key] != "":
        if data[key].isdigit():
            return True
        return False


def getTimerId():
    '''生成时间戳'''
    res = str(int(time.time()*10**4))
    result = int(res[:1]+res[5:])
    return result


def judgeExist(data, *args):
    if data not in [*args]:
        return False
    return True


def isVaildDate(date):
    try:
        s = time.strptime(date, "%Y-%m-%d %H:%M:%S")
        t = time.mktime(s) - time.time()
        # 已经过期
        if t <= 0:
            return -1
        # 即将过期
        elif (datetime.strptime(date, "%Y-%m-%d %H:%M:%S") - datetime.now()).days < 15:
            return -2
        # 正常
        elif (datetime.strptime(date, "%Y-%m-%d %H:%M:%S") - datetime.now()).days == 365:
            return -3
        else:
            return -4
    except:
        return False


def send_mail(subject, recipients, html_body):
    '''发邮件'''
    mail = Mail(current_app)
    msg = Message(subject=subject, recipients=[recipients])
    msg.body = "body"
    msg.html = html_body
    mail.send(msg)



def httpRequestUser(ip, path):
    '''请求用户信息'''
    args = {
        "apikey": "",
        "request": {

        }
    }
    resp = IBUS.RPC("RESTful", ip, path, "", args)
    resp = json.loads(resp)
    return resp


def httpRequestModifyUser(datas, ip, path):
    '''请求用户信息'''
    args = {
        "apikey": "",
        "request": {
            "attribute": datas['attrName'],
            "nodeid": datas['nodeid'],
            "value": datas['attrValue']
        }
    }
    resp = IBUS.RPC("RESTful", ip, path, "", args)
    resp = json.loads(resp)
    return resp


def httpRequestModifyLoginKey(datas, ip, path):
    '''修改密码'''
    args = {
        "apikey": "",
        "request": {
            "nodeid": datas['nodeid'],
            "newKey": datas['loginKey'],
            "oldKey": datas['oldLoginKey']
        }
    }
    resp = IBUS.RPC("RESTful", ip, path, "", args)
    resp = json.loads(resp)
    return resp


def httpRequestEmail(tomail, cc, subject, content, attachments, ip, path):
    '''请求发送邮件'''
    args = {
        "apikey": "",
        "request": {
            "to": tomail,
            "cc": cc,
            "subject": subject,
            "content": content,
            "attachments": attachments
        }
    }
    resp = IBUS.RPC("RESTful", ip, path, "", args)
    resp = json.loads(resp)
    return resp


def login_required(view_func):
    """登录验证装饰器"""
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        # 判断用户的登录状态
        data = dict()
        # 获取session_id
        session_id = args[2]['session_id']
        if not session_id:
            return {
                "errorCode": -5,
                "errorMsg": '请登录后再操作'
            }
        # print("-----",session_id)
        m = base64.b64decode(session_id.encode()).decode()
        if re.compile(r'^admin_').match(m):
            data['id'] = int(m.split("_")[1])
            res = DS.checkAdminLoginStatus(data)
        else:
            data['id'] = int(m)
            res = DS.checkUserLoginStatus(data)

        if not res:
            return {
                "errorCode": -1,
                "errorMsg": '请重新登录'
            }
        elif not res['online']:
            return {
                "errorCode": -3,
                "errorMsg": '用户不在线，请重新登录'
            }
        elif not res['sessionTime']:
            return {
                "errorCode": -2,
                "errorMsg": '用户没有登陆记录'
            }
        else:
            startTime = datetime.strptime(str(res['sessionTime']), "%Y-%m-%d %H:%M:%S")
            endTime = datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "%Y-%m-%d %H:%M:%S")
            if (endTime - startTime).days > 3:
                return {
                    "errorCode": -4,
                    "errorMsg": '登录失效，请重新登录'
                }
            else:
                # email = res['email']
                # 如果用户已登录，执行视图函数
                return view_func(*args, **kwargs)

    return wrapper


def admin_login_required(view_func):
    """登录验证装饰器"""
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        # 判断用户的登录状态
        data = dict()
        # 获取session_id
        session_id = args[2]['session_id']
        if not session_id:
            return {
                "errorCode": -5,
                "errorMsg": '请登录后再操作'
            }
        data['id'] = int(base64.b64decode(session_id.encode()).decode().split("_")[1])
        res = DS.checkAdminLoginStatus(data)
        if not res:
            return {
                "errorCode": -1,
                "errorMsg": '请重新登录'
            }
        elif not res['online']:
            return {
                "errorCode": -3,
                "errorMsg": '用户不在线，请重新登录'
            }
        elif not res['sessionTime']:
            return {
                "errorCode": -2,
                "errorMsg": '用户没有登陆记录'
            }
        else:
            startTime = datetime.strptime(str(res['sessionTime']), "%Y-%m-%d %H:%M:%S")
            endTime = datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "%Y-%m-%d %H:%M:%S")
            if (endTime - startTime).days > 3:
                return {
                    "errorCode": -4,
                    "errorMsg": '登录失效，请重新登录'
                }
            else:
                # email = res['email']
                # 如果用户已登录，执行视图函数
                return view_func(*args, **kwargs)

    return wrapper