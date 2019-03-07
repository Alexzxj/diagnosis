# todo:添加至main.py
# 邮箱服务
# MAIL_SERVER = 'smtp.mxhichina.com',
# # 邮箱端口
# MAIL_PORT = 465,
# # 邮箱安全协议
# MAIL_USE_SSL = True,
# # 邮箱名称
# MAIL_USERNAME = 'product@ehz.cn',
# # 邮箱密码
# MAIL_PASSWORD = 'Ehz12345'
# # 邮箱
# MAIL_DEFAULT_SENDER = '华制诊断云<product@ehz.cn>'
# 主题
subject = '激活账户'

# 激活链接
link = 'http://zhenduan.ehzcloud.com/#/registerActive/?'
# 邮件内容
html_body = ''

# 请从应用管理页面获取APP_Key和APP_Secret进行替换
APP_KEY = "wCc8WMaj523br7u9494LxZBUor88"
APP_SECRET = "fI9Z1I061865na8I24ec3sx60Kql"

# 请从应用管理页面获取APP接入地址，替换url中的ip地址和端口
url = 'https://117.78.29.66:10443/sms/batchSendSms/v1'

# 填写短信签名中的通道号，请从签名管理页面获取
sender = "csms18070402"

# 填写短信接收人号码
# receiver = "13724378644"

# 状态报告接收地址，为空或者不填表示不接收状态报告
statusCallBack = ""

# 请从模板管理页面获取模板ID进行替换
TEMPLATE_ID = "7314d6b6c41c4a5fb340b55eecf6ead9"