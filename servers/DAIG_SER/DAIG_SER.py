import base64
import random
import uuid
from datetime import datetime
import json
import re
from threading import Thread
import time
import os, math

from urllib import parse
import IBUS
from util.SMS import sms
import xlrd
from util import CommonHelp, SessionHelper
from .DAIG_SERDao import DaigSys as DS
from . import CommonDag


def adminLogin(sid, cmd, datas):
    """管理员登录
    user
    password
    """
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData("user", datas):
        errorCode = -2
        errorMsg = '用户为空'
    elif DS.uniqueAdmin(datas):
        errorCode = -3
        errorMsg = '用户不存在'
    elif not CommonDag.hasKeyData("password", datas):
        errorCode = -4
        errorMsg = '密码为空'

    if not errorMsg:
        # 密码加密 sha256
        import hashlib
        datas['password'] = hashlib.sha256(datas['password'].encode()).hexdigest()
        res = DS.checkAdminLogin(datas)
        if not res:
            errorCode = -5
            errorMsg = '查询用户失败'
        else:
            session_id = "admin_" + str(res['idx'])
            mobile = res['mobile']
            rid = res['rid']
            email = res['email']
            remark = res['remark']
            if datas['password'] != res['adminPwd']:
                errorCode = -1
                errorMsg = '密码错误'
            else:
                # 更新用户的登录状态
                datas['online'] = 1
                con = DS.updateAdminOnlineStatus(datas)
                if not con:
                    errorCode = -6
                    errorMsg = '更新状态失败'
                else:
                    errorCode = 0
                    errorMsg = '登录成功'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg,
                        "return": {
                            "session_id": base64.b64encode(str(session_id).encode()).decode(),
                            "mobile": mobile,
                            "rid": rid,
                            "email": email,
                            "remark": remark
                        }
                    }
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


def check_admin_login(sid, cmd, datas):
    """检查管理员是否登陆
    id: session_id
    """
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('id', datas):
        errorCode = -2
        errorMsg = '状态id为空'

    if not errorMsg:
        datas['id'] = int(base64.b64decode(datas['id'].encode()).decode().split("_")[1])
        res = DS.checkAdminLoginStatus(datas)
        if not res:
            errorCode = -1
            errorMsg = '请重新登录'
        elif not res['online']:
            errorCode = -3
            errorMsg = '用户不在线，请重新登录'
        elif not res['sessionTime']:
            errorCode = -5
            errorMsg = '用户没有登陆记录'
        else:
            startTime = datetime.strptime(str(res['sessionTime']), "%Y-%m-%d %H:%M:%S")
            endTime = datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "%Y-%m-%d %H:%M:%S")
            if (endTime - startTime).days > 30:
                errorCode = -4
                errorMsg = '登录失效，请重新登录'
            else:
                email = res['email']
                name = res['adminName']
                rid = res['rid']
                mobile = res['mobile']
                errorCode = 0
                errorMsg = '用户登录状态正常'
                return {
                    "errorCode": errorCode,
                    "errorMsg": errorMsg,
                    "return": {
                        "email": email,
                        "name": name,
                        "rid": rid,
                        "mobile": mobile
                    }
                }

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def statisticEnterprise(sid, cmd, datas):
    """统计企业信息
    user
    session_id
    """
    errorCode = -1
    errorMsg = ''
    # 注册企业
    ent_count = 0
    # 行业
    industry_count = 0
    # 评测企业
    test_ent = 0
    if not CommonDag.hasKeyData("user", datas):
        errorCode = -2
        errorMsg = '用户为空'
    elif DS.uniqueAdmin(datas):
        errorCode = -3
        errorMsg = '用户不存在'
    elif not CommonDag.hasKeyData("session_id", datas):
        errorCode = -4
        errorMsg = 'session_id为空'
    else:
        datas['idx'] = int(base64.b64decode(datas['session_id'].encode()).decode().split("_")[1])

    if not errorMsg:
        res = DS.checkAdminLogin(datas)
        if not res:
            errorCode = -5
            errorMsg = '查询用户信息为空'
        elif res['idx'] != datas['idx']:
            errorCode = -6
            errorMsg = '用户信息不匹配'
        else:
            # 超管的权限
            # todo:以后根据权限判断
            try:
                info = DS.getAllEnterprise(datas)
            except:
                errorCode = -1
                errorMsg = '获取企业信息异常'
            else:
                ent_count += len(info)
                lt = []
                for temp in info:
                    con = temp['industryL1']+temp['industryL2']+temp['industryL3']+temp['industryL4']+temp['industryL5']
                    if con not in lt:
                        industry_count += 1
                        lt.append(con)

                    datas['id'] = temp['idx']
                    num = DS.statisticTestingCount(datas)
                    if num:
                        test_ent += 1

                errorCode = 0
                errorMsg = '获取ok'
                return {
                    "errorCode": errorCode,
                    "errorMsg": errorMsg,
                    "return": {
                        "ent_count": ent_count,
                        "industry_count": industry_count,
                        "test_ent": test_ent
                    }
                }
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def get_all_enterprise(sid, cmd, datas):
    """获取全部企业信息
    session_id
    key：
    province
    city
    area：
    industryL1：
    industryL2：
    industryL3：
    industryL4：
    industryL5：
    income
    scale：
    test_st_time：
    test_en_time：
    res_st_time
    res_en_time
    flag
    """
    errorCode = -1
    errorMsg = ''
    ent_count = 0
    rlt = list()
    if not CommonDag.hasKeyData("session_id", datas):
        errorCode = -2
        errorMsg = 'session_id为空'
    elif not CommonHelp.hasKey("key", datas):
        errorCode = -3
        errorMsg = '关键字为空'
    elif not CommonHelp.hasKey("province", datas):
        errorCode = -4
        errorMsg = '省为空'
    elif not CommonHelp.hasKey("city", datas):
        errorCode = -11
        errorMsg = '市为空'
    elif not CommonHelp.hasKey("area", datas):
        errorCode = -12
        errorMsg = '区域为空'
    elif not CommonHelp.hasKey("industryL1", datas):
        errorCode = -5
        errorMsg = '行业一级为空'
    elif not CommonHelp.hasKey("industryL2", datas):
        errorCode = -13
        errorMsg = '行业二级为空'
    elif not CommonHelp.hasKey("industryL3", datas):
        errorCode = -14
        errorMsg = '行业三级为空'
    elif not CommonHelp.hasKey("industryL4", datas):
        errorCode = -15
        errorMsg = '行业四级为空'
    elif not CommonHelp.hasKey("industryL5", datas):
        errorCode = -16
        errorMsg = '行业五级为空'
    elif not CommonHelp.hasKey("income", datas):
        errorCode = -6
        errorMsg = '销售额为空'
    elif not CommonHelp.hasKey("scale", datas):
        errorCode = -7
        errorMsg = '企业规模为空'
    elif not CommonHelp.hasKey("test_st_time", datas):
        errorCode = -8
        errorMsg = '最近测评时间为空'
    elif not CommonHelp.hasKey("test_en_time", datas):
        errorCode = -17
        errorMsg = '最近测评时间为空'
    elif not CommonHelp.hasKey("res_st_time", datas):
        errorCode = -9
        errorMsg = '注册起始为空'
    elif not CommonHelp.hasKey("res_en_time", datas):
        errorCode = -10
        errorMsg = '注册结束为空'
    elif not CommonDag.judgeListType('flag', datas):
        errorCode = -11
        errorMsg = '传入不为列表，应该为[1,2]'
    else:
        datas['idx'] = int(base64.b64decode(datas['session_id'].encode()).decode().split("_")[1])
        if datas['res_st_time'] and datas['res_en_time']:
            if datas['res_en_time'] < datas['res_st_time']:
                errorCode = -12
                errorMsg = '起始时间大于结束时间'
        elif datas['test_st_time'] and datas['test_en_time']:
            if datas['test_en_time'] < datas['test_st_time']:
                errorCode = -16
                errorMsg = '起始时间大于结束时间'

    if not errorMsg:
        datas['type'] = 3
        try:
            info = DS.getAllEnterpriseInfo(datas)
        except:
            errorCode = -13
            errorMsg = '获取企业信息失败'
        else:
            for ct in info:
                if ct['flag']:
                    datas['id'] = ct['flag']
                    res = DS.get_enterprise_flag(datas)
                    if not res:
                        errorCode = -15
                        errorMsg = '获取标签为空'
                        return {
                            "errorCode": errorCode,
                            "errorMsg": errorMsg
                        }
                    else:
                        ct['flag'] = res

                if datas['flag']:
                    for t in datas['flag']:
                        if type(t) != int:
                            errorCode = -14
                            errorMsg = '标签里表中类型错误，应该都为整数'
                            return {
                                "errorCode": errorCode,
                                "errorMsg": errorMsg
                            }
                        # 添加搜索中标签没有的企业信息
                        elif len(ct['flag']) > 1:
                            if t not in [temp['idx'] for temp in ct['flag']]:
                                if ct not in rlt:
                                    rlt.append(ct)
                        elif len(ct['flag']) == 1:
                            if t != ct['flag'][0]['idx']:
                                if ct not in rlt:
                                    rlt.append(ct)
                        elif len(ct['flag']) == 0:
                            if ct not in rlt:
                                rlt.append(ct)
                # 获取最近评测时间
                st_time = DS.get_recently_test_time(ct)
                if not st_time:
                    ct['recently_testTime'] = ""
                else:
                    ct['recently_testTime'] = st_time
                ent_count += len(info)
                errorCode = 0
                errorMsg = '获取ok'
            # 删除搜查企业中不包含标签信息的企业
            for rt in rlt:
                info.remove(rt)

        return {
            "errorCode": errorCode,
            "errorMsg": errorMsg,
            "ent_count": ent_count,
            "return": info
        }

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


def get_flag_info(sid, cmd, datas):
    """获取标签信息
    type：1：问题 2：问卷 3：企业'
    """
    errorMsg = ''
    errorCode = -1
    if not CommonDag.hasKeyData('type', datas):
        errorCode = -2
        errorMsg = '关键字为空'
    elif datas['type'] not in [1, 2, 3]:
        errorCode = -3
        errorMsg = '传参错误，应为1-3'

    if not errorMsg:
        datas['id'] = ''
        try:
            res = DS.get_enterprise_flag(datas)
        except:
            errorCode = -1
            errorMsg = '获取标签信息异常'
        else:
            if not res:
                count = 0
            else:
                count = len(res)
            errorCode = 0
            errorMsg = 'ok'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg,
                "return": {
                    "count": count,
                    "info": res
                }
            }
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def add_flag_for_enterprise(sid, cmd, datas):
    """添加企业标签
        session_id：
        flag: 标签
        idx 企业id
    """
    errorMsg = ""
    errorCode = -1
    flag_id = ''
    if not CommonDag.hasKeyData("session_id", datas):
        errorCode = -2
        errorMsg = 'session_id为空'
    elif not CommonDag.hasKeyData('flag', datas):
        errorCode = -3
        errorMsg = '标签为空'
    elif not CommonDag.hasKeyData('idx', datas):
        errorCode = -4
        errorMsg = '企业id为空'
    elif not CommonDag.judgeIntType('idx', datas):
        errorCode = -5
        errorMsg = '企业id类型不为整数'

    if not errorMsg:
        flag_info = DS.check_flag_exist(datas)
        if not flag_info:
            con = DS.add_enterprise_flag(datas)
            if not con:
                errorCode = -6
                errorMsg = '添加企业标签失败'
            else:
                flag_id = con
        else:
            flag_id = flag_info['idx']

    if not errorMsg:
        flag_str = DS.get_my_enterprise_flag(datas)
        if not flag_str:
            errorCode = -7
            errorMsg = '获取企业标签失败'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }
        flag_list = json.loads(flag_str['flag'])
        if flag_id not in flag_list:
            flag_list.append(flag_id)
            datas['flag_id'] = flag_list
            rt = DS.modify_my_enterprise_flag(datas)
            if not rt:
                errorCode = -1
                errorMsg = '更新企业标签失败'

        errorCode = 0
        errorMsg = 'ok'
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def delete_flag_for_enterprise(sid, cmd, datas):
    """添加企业标签
        session_id：
        flag: 标签
        idx 企业id
    """
    errorMsg = ""
    errorCode = -1
    flag_id = 0
    if not CommonDag.hasKeyData("session_id", datas):
        errorCode = -2
        errorMsg = 'session_id为空'
    elif not CommonDag.hasKeyData('flag', datas):
        errorCode = -3
        errorMsg = '标签为空'
    elif not CommonDag.hasKeyData('idx', datas):
        errorCode = -4
        errorMsg = '企业id为空'
    elif not CommonDag.judgeIntType('idx', datas):
        errorCode = -5
        errorMsg = '企业id类型不为整数'

    if not errorMsg:
        flag_info = DS.check_flag_exist(datas)
        if not flag_info:
            pass
        else:
            flag_id = flag_info['idx']

    if not errorMsg:
        flag_str = DS.get_my_enterprise_flag(datas)
        if not flag_str:
            errorCode = -6
            errorMsg = '获取企业标签失败'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }
        flag_list = json.loads(flag_str['flag'])
        if flag_id in flag_list:
            flag_list.remove(flag_id)
            datas['flag_id'] = flag_list
            rt = DS.modify_my_enterprise_flag(datas)
            if not rt:
                errorCode = -1
                errorMsg = '更新企业标签失败'

        errorCode = 0
        errorMsg = 'ok'
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def modify_enterprise_mark(sid, cmd, datas):
    """修改企业备注描述
    session_id:
    remark: 备注信息
    idx:企业id
    """
    errorMsg = ""
    errorCode = -1
    if not CommonDag.hasKeyData("session_id",datas):
        errorCode = -2
        errorMsg = 'session_id为空'
    elif not CommonHelp.hasKey('remark', datas):
        errorCode = -3
        errorMsg = '备注信息为空'
    elif not CommonDag.hasKeyData('idx', datas):
        errorCode = -4
        errorMsg = '企业id为空'
    elif not CommonDag.judgeIntType('idx', datas):
        errorCode = -5
        errorMsg = '企业id类型不为整数'

    if not errorMsg:
        res = DS.modify_enterprise_remark_info(datas)
        if not res:
            errorCode = -1
            errorMsg = '更新失败'
        else:
            errorCode = 0
            errorMsg = '更新ok'
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def get_enterprise_user(sid, cmd, datas):
    """获取企业的用户
    session_id:
    idx:
    """
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData("session_id",datas):
        errorCode = -2
        errorMsg = 'session_id为空'
    elif not CommonDag.hasKeyData('idx', datas):
        errorCode = -3
        errorMsg = '企业id为空'
    elif not CommonDag.judgeIntType('idx', datas):
        errorCode = -4
        errorMsg = '企业id类型不为整数'

    if not errorMsg:
        # todo:暂时没有子用户先不获取，子用户在
        try:
            res = DS.get_enterprise_user_info(datas)
        except:
            errorCode = -1
            errorMsg = '获取企业相关信息异常'
        else:
            count = len(res)
            errorCode = 0
            errorMsg = '获取成功'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg,
                "return": {
                    "count": count,
                    "user_info": res
                }
            }
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def getEnterpriseTestAllInfo(sid, cmd, datas):
    '''获取企业评测的问卷
        session_id :
        enterprise_id:企业id
        key：关键字搜索
        status：1已完成,  2未完成 ,3全部
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('session_id', datas):
        errorCode = -2
        errorMsg = '传入session_id为空'
    elif not CommonHelp.hasKey('key', datas):
        errorCode = -3
        errorMsg = '搜索key为空'
    elif not CommonHelp.hasKey('status', datas):
        errorCode = -4
        errorMsg = '状态为空'
    elif not CommonDag.hasKeyData('enterprise_id', datas):
        errorCode = -5
        errorMsg = '传入企业id为空'
    elif not CommonDag.judgeIntType('enterprise_id', datas):
        errorCode = -6
        errorMsg = '企业id应该为整数'
    elif datas['status']:
        if not CommonDag.judgeIntType('status', datas):
            errorCode = -8
            errorMsg = '状态不为整数'
        elif datas['status'] not in [1, 2, 3]:
            errorCode = -7
            errorMsg = '状态参数不正确，应为1-3'

    if not errorMsg:
        datas['idx'] = datas['enterprise_id']
        user_list = list()
        user_info = DS.get_enterprise_user_info(datas)
        if not user_info:
            errorCode = -9
            errorMsg = '获取用户信息失败'
        else:
            for user in user_info:
                user_list.append(user['idx'])
            datas['user_id'] = user_list

        try:
            enterprise_test_all_info = DS.get_enterprise_all_info(datas)
        except Exception as e:
            errorCode = -1
            errorMsg = '获取企业评测信息失败'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }
        else:
            doing = list()
            done = list()
            # # 获取用户中心的相关用户和企业信息
            # user_enter = DS.getUserCenterInfo(datas)
            # if not user_enter:
            #     errorCode = -8
            #     errorMsg = '获取工作台相关信息失败'
            #     return {
            #         "errorCode": errorCode,
            #         "errorMsg": errorMsg
            #     }
            for ct in enterprise_test_all_info:
                if not ct['completeStatus']:
                    try:
                        result = DS.get_questions_info(ct)
                        # 转换字符串
                        result = json.loads(result)
                        q_length = len(result)
                    except:
                        errorCode = -10
                        errorMsg = '获取问题数目异常'
                        return {
                            "errorCode": errorCode,
                            "errorMsg": errorMsg
                        }
                    else:
                        questioned_count = DS.getQuestionedCount(ct)
                        ct['answered_count'] = questioned_count
                        # if not questioned_count:
                        #     ct['complete_degree'] = 0
                        # else:
                        # ct['complete_degree'] = math.ceil(questioned_count/q_length*100)
                        ct['complete_degree'] = round(questioned_count*100/q_length, 1)
                        errorCode = 0
                        errorMsg = '成功'
                        doing.append(ct)
                else:
                    done.append(ct)
            errorCode = 0
            errorMsg = '成功'

            if not datas['key'] and not datas['status']:
                return {
                    "errorCode": errorCode,
                    "errorMsg": errorMsg,
                    "return": {
                        "doing": doing,
                        "done": done
                    }
                }
            else:
                return {
                    "errorCode": errorCode,
                    "errorMsg": errorMsg,
                    "return": {
                        "info": enterprise_test_all_info
                    }
                }
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def get_test_all_info(sid, cmd, datas):
    """获取问卷信息
        session_id:
        id:问卷id
        user_id:用户id
        completeStatus： 0未完成 1 完成
        """
    errorCode = -1
    errorMsg = ''
    info = ''
    answered_count = 0
    if not CommonDag.hasKeyData('id', datas):
        errorCode = -2
        errorMsg = '传入问卷id为空'
    elif not CommonDag.judgeIntType('id', datas):
        errorCode = -3
        errorMsg = '问卷id不为整数'
    elif not DS.searchTestId(datas):
        errorCode = -4
        errorMsg = '问卷id不存在'
    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -5
        errorMsg = 'session_id为空'
    elif not CommonDag.hasKeyData('user_id', datas):
        errorCode = -6
        errorMsg = '用户为空'
    elif not CommonDag.judgeIntType('user_id', datas):
        errorCode = -7
        errorMsg = '用户id不为整数'
    elif not CommonDag.hasKeyData('completeStatus', datas):
        errorCode = -10
        errorMsg = '完成状态为空'
    elif datas['completeStatus'] not in [0, 1]:
        errorCode = -11
        errorMsg = '完成状态错误，应为0-1'

    if not errorMsg:
        # 判断是否是正在答题的问卷
        # t = DS.searchTestStatus(datas)
        # if not t:
        #     # todo：sprint3计划, 添加答卷数量 modify：20180716
        #     # 判断是否超过三个答卷， 若超过则提示不允许作答
        #     answer_count = DS.getAnswerCount(datas)
        #     if answer_count >= 3:
        #         errorCode = -8
        #         errorMsg = '正在答卷数量不能超过三个'
        #         return {
        #             "errorCode": errorCode,
        #             "errorMsg": errorMsg
        #         }
        result = DS.getQuestionsInfo(datas)
        # 转换字符串
        result = json.loads(result)
        if not result:
            errorCode = 0
            errorMsg = '目前无问题作答'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }
        else:
            # todo: 添加评分主表信息
            con = DS.searchTestStatus(datas)
            if not con:
                errorCode = -8
                errorMsg = '获取评测主表id失败'
                return {
                    "errorCode": errorCode,
                    "errorMsg": errorMsg
                }
            elif con['idx']:
                data = dict()
                data['id'] = con['idx']
                try:
                    info = DS.getAnswerInfo(data)
                except:
                    errorCode = -9
                    errorMsg = '获取答案信息失败'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }
                else:
                    answered_count = DS.getQuestionedCount(con)
                    # questioned_count = DS.getQuestionedCount(con)
                    # answered_count = questioned_count + 1
            # 获取状态
            count = len(result)
            qList = list()
            for temp in result:
                # todo：获取过程中，确保添加的题目在数据库中存在
                datas['qId'] = temp
                res = DS.getQuestionInfo(datas)
                if not res:
                    errorCode = -1
                    errorMsg = '问题不存在'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }
                if info:
                    for rt in info:
                        if rt['questionId'] == res['id']:
                            res['answered'] = rt['answer']
                            # todo:sprint2迭代  date:20180706
                            res['expected'] = rt['expectData']
                # 添加评分主表id
                res['idx'] = con['idx']
                qList.append(res)
            errorCode = 0
            errorMsg = '获取完成'
        return {
            "errorCode": errorCode,
            "errorMsg": errorMsg,
            "answered_count": answered_count,
            "count": count,
            "return": qList
        }

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


def get_tree_struct_data(sid, cmd, datas):
    """获取树状结构的数据
        id:问卷id
    """
    errorCode = -1
    errorMsg = ''
    lt = list()
    tree_list = list()
    if not CommonDag.hasKeyData('id', datas):
        errorCode = -2
        errorMsg = '传入问卷id为空'
    elif not CommonDag.judgeIntType('id', datas):
        errorCode = -3
        errorMsg = '问卷id不为整数'
    elif not DS.searchTestId(datas):
        errorCode = -4
        errorMsg = '问卷id不存在'

    if not errorMsg:
        info1 = ''
        info2 = ''
        info3 = ''
        info4 = ''
        info5 = ''
        for i in range(1, 6):
            datas['lv'] = i
            if i == 1:
                try:
                    info1 = DS.get_tree_struct_info(datas)
                except:
                    errorCode = -1
                    errorMsg = '获取结构数据不存在'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }
            elif i == 2:
                try:
                    info2 = DS.get_tree_struct_info(datas)
                except:
                    errorCode = -1
                    errorMsg = '获取结构数据不存在'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }
            elif i == 3:
                try:
                    info3 = DS.get_tree_struct_info(datas)
                except:
                    errorCode = -1
                    errorMsg = '获取结构数据不存在'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }
            elif i == 4:
                try:
                    info4 = DS.get_tree_struct_info(datas)
                except:
                    errorCode = -1
                    errorMsg = '获取结构数据不存在'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }
            elif i == 5:
                try:
                    info5 = DS.get_tree_struct_info(datas)
                except:
                    errorCode = -1
                    errorMsg = '获取结构数据不存在'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }

        for r1 in info1:
            r1['children'] = list()
            r1['label'] = r1['level1']
            r1['level'] = 1
            del r1['level1']
            lt.append(r1)
            for r2 in info2:
                dic1 = dict()
                if r2['level2'] and r2['level1'] == r1['label']:
                    dic1['level'] = 2
                    dic1['label'] = r2['level2']
                    dic1['children'] = list()
                    r1['children'].append(dic1)
                    for r3 in info3:
                        dic2 = dict()
                        if r3['level3'] and r3['level2'] == dic1['label'] and r3['level1'] == r1['label']:
                            dic2['level'] = 3
                            dic2['label'] = r3['level3']
                            dic2['children'] = list()
                            dic1['children'].append(dic2)
                            for r4 in info4:
                                dic3 = dict()
                                if r4['level4'] and r4['levle3'] == dic2['label'] and r4['level2'] == dic1['label'] \
                                        and r4['level1'] == r1['label']:
                                    dic3['level'] = 4
                                    dic3['label'] = r4['level4']
                                    dic3['children'] = list()
                                    dic2['children'].append(dic3)
                                    for r5 in info5:
                                        dic4 = dict()
                                        if r5['level5'] and r5['level4'] == dic3['label'] and r5['levle3'] == \
                                                dic2['label'] and r5['level2'] == dic1['label'] and r4['level1'] == \
                                                r1['label']:
                                            dic4['level'] = 5
                                            dic4['label'] = r4['level4']
                                            dic3['children'].append(dic4)

        errorMsg = 'ok'
        errorCode = 0
        return {
            "errorCode": errorCode,
            "errorMsg": errorMsg,
            "tree_struct": lt
        }

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def get_test_report_info(sid, cmd, datas):
    """获取报告数据
        session_id
        enterprise_id:企业id
        evaluationId ：问卷id
        id:测评主表id
    """
    errorCode = -1
    errorMsg = ''
    ric1 = dict()
    ric2 = dict()
    ric3 = dict()
    ric4 = dict()
    if not CommonDag.hasKeyData('session_id', datas):
        errorCode = -2
        errorMsg = 'session_id为空'
    elif not CommonDag.hasKeyData('evaluationId', datas):
        errorCode = -3
        errorMsg = '问卷id为空'
    elif not CommonDag.judgeIntType('evaluationId', datas):
        errorCode = -4
        errorMsg = '问卷id类型错误，为整数'
    elif not CommonDag.hasKeyData('id', datas):
        errorCode = -5
        errorMsg = '测评主表id为空'
    elif not CommonDag.judgeIntType('id', datas):
        errorCode = -6
        errorMsg = '测评主表id类型错误，为整数'
    elif not CommonDag.hasKeyData('enterprise_id', datas):
        errorCode = -7
        errorMsg = '企业id为空'
    elif not CommonDag.judgeIntType('enterprise_id', datas):
        errorCode = -8
        errorMsg = '企业id类型错误，为整数'
    elif not DS.check_enterprise_id(datas):
        errorCode = -9
        errorMsg = '企业id不存在'
    elif not DS.check_review_main_id(datas):
        errorCode = -10
        errorMsg = '主表id不存在'

    if not errorMsg:
        info = DS.get_report_all_info(datas)
        if not info:
            errorCode = -1
            errorMsg = '获取报告信息失败'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }
        datas['idx'] = info['idx']
        try:
            else_info = DS.get_report_else_info(datas)
        except:
            errorCode = -11
            errorMsg = '获取其他的信息异常'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }
        else:
            # 若获取其他企业信息为空，则添加维度
            if not else_info[0]:
                for v in info['actL1'].keys():
                    else_info[0].append(v)

        datas['industry'] = info['industry']
        datas['province'] = info['province']
        datas['city'] = info['city']
        datas['area'] = info['area']
        for i in range(1, 5):
            datas['val'] = i
            try:
                compare_info = DS.get_report_compare_data(datas)
            except:
                errorCode = -12
                errorMsg = '获取对比的信息异常'
                return {
                    "errorCode": errorCode,
                    "errorMsg": errorMsg
                }
            else:
                if i == 1:
                    ric1['industry'] = compare_info
                elif i == 2:
                    ric2['province'] = compare_info
                elif i == 3:
                    ric3['city'] = compare_info
                elif i == 4:
                    ric4['area'] = compare_info

        errorCode = 0
        errorMsg = 'ok'
        return {
            "errorCode": errorCode,
            "errorMsg": errorMsg,
            "return": {
                "report_info": info,
                "table_data": else_info,
                "industry": ric1,
                "province": ric2,
                "city": ric3,
                "area": ric4
            }
        }

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


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
servers = list()
servers.append(IBUS.IFS_SERVER("run", False, "private", "系统启动", main))
# servers.append(IBUS.IFS_SERVER("readExcelInfo", False, "public", "读表格数据", readExcelInfo))
servers.append(IBUS.IFS_SERVER("adminLogin", False, "public", "管理员登录", adminLogin))
servers.append(IBUS.IFS_SERVER("check_admin_login", False, "public", "检查管理员登录", check_admin_login))
servers.append(IBUS.IFS_SERVER("statisticEnterprise", False, "public", "统计企业信息", statisticEnterprise))
servers.append(IBUS.IFS_SERVER("get_all_enterprise", False, "public", "搜索获取企业信息", get_all_enterprise))
servers.append(IBUS.IFS_SERVER("get_flag_info", False, "public", "搜索获取标签信息", get_flag_info))
servers.append(IBUS.IFS_SERVER("add_flag_for_enterprise", False, "public", "添加标签信息", add_flag_for_enterprise))
servers.append(IBUS.IFS_SERVER("delete_flag_for_enterprise", False, "public", "删除标签信息", delete_flag_for_enterprise))
servers.append(IBUS.IFS_SERVER("modify_enterprise_mark", False, "public", "修改企业备注信息", modify_enterprise_mark))
servers.append(IBUS.IFS_SERVER("get_enterprise_user", False, "public", "获取企业用户信息", get_enterprise_user))
servers.append(IBUS.IFS_SERVER("getEnterpriseTestAllInfo", False, "public", "获取企业评测信息", getEnterpriseTestAllInfo))
servers.append(IBUS.IFS_SERVER("get_test_all_info", False, "public", "获取评测问题信息", get_test_all_info))
servers.append(IBUS.IFS_SERVER("get_tree_struct_data", False, "public", "获取评测问题结构", get_tree_struct_data))
servers.append(IBUS.IFS_SERVER("get_test_report_info", False, "public", "获取报告", get_test_report_info))
IBUS.addServer("DAIG_SER", servers)

# 事件
events = list()
events.append(IBUS.IF_ENENT(onEvent))
IBUS.addEvent(events)