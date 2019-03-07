import random
import time
import uuid
import hashlib
import base64

# 需要先使用 pip install requests 命令安装依赖
import requests

# # 请从应用管理页面获取APP_Key和APP_Secret进行替换
# APP_KEY = "wCc8WMaj523br7u9494LxZBUor88"
# APP_SECRET = "fI9Z1I061865na8I24ec3sx60Kql"
#
# # 请从应用管理页面获取APP接入地址，替换url中的ip地址和端口
# url = '	https://117.78.29.66:10443/sms/batchSendSms/v1'
#
# # 填写短信签名中的通道号，请从签名管理页面获取
# sender = "csms18070402"
#
# # 填写短信接收人号码
# # receiver = "13724378644"
#
# # 状态报告接收地址，为空或者不填表示不接收状态报告
# statusCallBack = ""
#
# # 请从模板管理页面获取模板ID进行替换
# TEMPLATE_ID = "7314d6b6c41c4a5fb340b55eecf6ead9"
# 模板变量请务必根据实际情况修改，查看更多模板变量规则
# 如模板内容为“您有${NUM_2}件快递请到${TXT_32}领取”时，templateParas可填写为["3","人民公园正门"]
# 双变量示例：TEMPLATE_PARAM='["3","人民公园正门"]'
# verifyCode = str("%05d"%(random.randint(0, 99999)))

# TEMPLATE_PARAM = '['+verifyCode+']'


def buildWSSEHeader(appKey, appSecret):
    now = time.strftime('%Y-%m-%dT%H:%M:%SZ')
    nonce = str(uuid.uuid4()).replace('-', '')
    digest = hashlib.sha256((nonce + now + appSecret).encode()).hexdigest()
    digestBase64 = base64.b64encode(digest.encode()).decode()
    return 'UsernameToken Username="{}",PasswordDigest="{}",Nonce="{}",Created="{}"'.format(appKey, digestBase64, nonce, now);


def main(receiver, TEMPLATE_PARAM, APP_KEY, APP_SECRET, sender, url, TEMPLATE_ID, statusCallBack):
    wsseHeader = buildWSSEHeader(APP_KEY, APP_SECRET)
    header= {'Authorization':'WSSE realm="SDP",profile="UsernameToken",type="Appkey"', 'X-WSSE': wsseHeader}
    formData = {'from':sender, 'to':receiver, 'templateId':TEMPLATE_ID,
                'templateParas':TEMPLATE_PARAM, 'statusCallBack':statusCallBack}

    r = requests.post(url, data=formData, headers=header, verify=False)
    return r.text


if __name__ == '__main__':
    main()