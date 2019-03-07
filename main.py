import importlib
import json
import sys
import threading
import time
import uuid

import IBUS

file = open("serverConfig.json")
serverConfigStr = file.read()
file.close()
serverConfig = json.loads(serverConfigStr)

for s in serverConfig['servers']:
   if s['isEnable'] == True:
       try:
           sys.path.append("servers")

           importlib.import_module(s['server']+"."+s['server'])
           print (s['server'] + ":is starting!")
       except ImportError:
           print("file data/%s.py is not existed. " % s['server'])

from flask import Flask, request, send_file, g, current_app, jsonify
from gevent import wsgi, monkey
from util.Captcher import captch
# import sys
# if 'threading' in sys.modules:
#
#     del sys.modules['threading']
# monkey.patch_all()
# monkey.patch_socket()
app = Flask(__name__, static_url_path='')
# app = Flask(__name__)
app.config['SECRET_KEY'] = 'you never guess' # 使用 session 必须要配置这个，不然会报500错误的！
# 获取图片验证码
@app.route('/Captch')
def Captcher():
    code, pic_name = captch.create_code()
    # code = "".join(code)
    # 设置验证码和时间信息
    SessionHelper.Session().set("captcher", code)
    # g.code = code
    file = "./" + pic_name
    return send_file(file)

# 获取企业logo
@app.route('/IMAGE/<path:args>')
def LOGO(args):
    return send_file(args)

# 发邮件配置文件
# 密码
app.config['MAIL_PASSWORD'] = 'Ehz12345'
# 端口
app.config['MAIL_PORT'] = 465
# 邮箱服务
app.config['MAIL_SERVER'] = 'smtp.mxhichina.com'
# 安全服务
app.config['MAIL_USE_SSL'] = True
# 用户名
app.config['MAIL_USERNAME'] = 'product@ehz.cn'
# 默认发送者
app.config['MAIL_DEFAULT_SENDER'] = '华制诊断云<product@ehz.cn>'

# 用户session信息
SESSION_TYPE = "mysql"  # 指明session数据保存在redis中
SESSION_USE_SIGNER = True  # 指明对cookie中保存的session_id进行加密保护
PERMANENT_SESSION_LIFETIME = 3 * 24 * 60 * 60  # session的有效(三天)，单位秒


@app.route('/web/<path:args>')
def RESOURCE(args):
    if args == 'index':
        args = 'index.html'
    return send_file('web/'+ args)


from util import ConfigHelp, SessionHelper, JsonExtendEncoder
from util import SysHelp
# #向EBS平台注册
apikey = ""
data = ConfigHelp.getSysConfig()
args = {
        "apikey": "",
        "method": "ESBSystem#systemLogin",
        "request": {
            "dns": data['ibus']['DNS'],
            "objectid": data['ibus']['objectId'],
            "type": data['ibus']['type'],
            "name": data['ibus']['name'],
            "host": "http://%s:%s" % (data['ibus']['host'], data['ibus']['port']),
            "password": data['ibus']['password'],
            "cpuUsage": SysHelp.getVirtualMemoryPercent(),
            "memoryUsage": SysHelp.getCpuPercent(),
            "systemInfo": "主机名:  %s OS名称: %s 专业版OS版本: %s" %(SysHelp.getNode(), SysHelp.getVersion(), SysHelp.getPlatform()) ,
            "explain": "null"
        }
    }
requestHttp = "http://%s:%s" % (data['esb']['host'], data['esb']['port'])
sendLogin = 10
if not (data["ibus"]["sendLogin"] == None or data["ibus"]["sendLogin"] == 0):
    sendLogin = data["ibus"]["sendLogin"]

from util import CommonHelp
def systemLogin():
    """定时注册15秒"""
    ebsData = IBUS.RPC("RESTful", requestHttp, "/ESBREST/master/IBUS", "", args)
    ebsData = json.loads(ebsData)
    if (ebsData["errorCode"] == 0 or ebsData["errorCode"] == -4):
        if ebsData["errorCode"] == 0:
            apikey = ebsData["return"]["apikey"]
            print("=====向网关注册成功,当前时间:%s"%(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
    else:
        errorMsg = ""
        if CommonHelp.hasKey("errorMsg", ebsData):
            errorMsg = ebsData["errorMsg"]
        else:
            errorMsg = ebsData["return"]
        print("向网关注册失败:"+errorMsg)
    t = threading.Timer(sendLogin,systemLogin)
    t.start()

def getSystemHostByDNS():
    """定时获取所有登录的DNS"""
    hostArgs = {
        "apikey": "",
        "method": "ESBSystem#getSystemHostByDNS",
        "request": {
            "dns": data['esb']['DNS']
        }
    }
    ebsData = IBUS.RPC("RESTful", requestHttp, "/ESBREST/master/IBUS", "", hostArgs)
    ebsData = json.loads(ebsData)
    if (ebsData["errorCode"] == 0 or ebsData["errorCode"] == -4):
        SysHelp.HOST = ebsData["return"]
    else:
        errorMsg = ""
        print(ebsData)
        if CommonHelp.hasKey("errorMsg", ebsData):
            errorMsg = ebsData["errorMsg"]
        else:
            errorMsg = ebsData["return"]
        print("所有登录的DNS失败:"+errorMsg)
    t = threading.Timer(sendLogin, getSystemHostByDNS)
    t.start()

@app.route('/IBUS/<path:args>',methods=['POST'])
def RESTIBUS(args):
    res = json.loads(request.data)
    r = IBUS.RPC("RESTful", "local", args, "", res)
    """获取错误码"""
    if(r["errorCode"] != 0):
        errorMsg = r["errorMsg"]
        errorReq = {
          "apikey": "",
          "request": {
              "url": "/ESBREST/masterExtend002" + request.path,
              "errorCode": r["errorCode"]
          }
        }
        try:
            errorRes = IBUS.RPC("RESTful", "local", "PLAT_System/getErrorMsg", "", errorReq)
            if errorRes["errorCode"] == 0 or errorRes["errorCode"] == -6:
                if (CommonHelp.hasKey("retrun", errorRes["return"]) == False):
                    errorMsg = errorRes["return"]["msg"]

            r["errorMsg"] = errorMsg
        except Exception as e:
            r = r

    """处理错误码结束"""
    result = json.dumps(r, ensure_ascii=False, cls=JsonExtendEncoder.JsonExtendEncoder)
    return result

# 上传文件的最大尺寸1M
# app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024


@app.route('/upload', methods=['POST'])
def UPLOAD():
    '''上传图片
    file :图片对象
    '''
    image_file_obj = request.files.get('file')
    header = request.headers.get('Content-Length')
    if not image_file_obj:
        return jsonify(errorCode=-1, errorMsg="parameters error")
    type = ['png', 'jpg', 'jpeg', 'gif', 'bmp']
    pic_name = image_file_obj.filename
    pic_type = pic_name.split(".")[1]
    pre_name = pic_name.split(".")[0]
    if pic_type not in type:
        return jsonify(errorCode=-2, errorMsg="type error")

    # 图片名称唯一
    name = str(uuid.uuid1()).replace("-", "")
    pic = pic_name.replace(pre_name, name)
    pt = './image/' + pic

    if int(header)/1024 > 1024:
        return jsonify(errorCode=-3, errorMsg='image size is too long, please upload size < 1M')

    # 保存图片c
    image_file_obj.save(pt)
    return jsonify(errorCode=0, errorMsg='upload success', data={"image_url": pt})


if __name__ == '__main__':
    # 向网关注册
    # systemLogin()
    # 获取登录过的DSN
    # getSystemHostByDNS()
    # 初始化session
    SessionHelper.Session().init()
    # 开机运行启动程序服务
    IBUS.startupModules()
    host = "127.0.0.1"
    port = 3020
    if data != None:
        host = data['ibus']["host"]
        port = data['ibus']["port"]

    tserver = wsgi.WSGIServer((host, port), app)
    tserver.serve_forever()
