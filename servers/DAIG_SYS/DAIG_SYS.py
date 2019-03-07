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
from .DAIG_SYSDao import DaigSys as DS
from . import CommonDag, config
from decimal import Decimal


def readExcelInfo(sid, cmd, datas):
    '''读取Excel写数据库
    path :excel文件路径
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('path', datas):
        errorCode = -2
        errorMsg = '路径为空'
    print(1111111111)
    if not errorMsg:
        # 打开文件，并且获取相对应表单数据
        # print(datas['path'])
        dt = xlrd.open_workbook(datas['path'])
        table = dt.sheet_by_index(0)
        # 层级信息
        datas['level1'] = ''
        datas['level2'] = ''
        datas['level3'] = ''
        datas['level4'] = ''
        datas['level5'] = ''
        # 获取表单行数
        for temp in range(3, table.nrows):
            # print(temp, table.row_values(temp))
            con = table.row_values(temp)
            if con[5]:
                # datas['question'] = con[4]
                # res = DS.searchQuestion(datas)
                # datas['qid'] = 0
                # if res:
                #     datas['qid'] = res['idx']
                # else:
                # 问题的信息获取
                datas['question'] = con[5]
                # 先单选，并且整数
                datas['answerType'] = 1
                # 选项倒叙
                datas['answer'] = con[6:]
                datas['answer'].reverse()
                datas['createBy'] = 'admin'
                datas['status'] = 1
                # 插入数据
                ue = DS.addQuestion(datas)
                if not ue:
                    errorCode = -3
                    errorMsg = '添加问题失败'
                    break
                datas['qid'] = ue
                # 获取每行数据
                # con = table.row_values(temp)
                # 先按四级设计
                if con[0]:
                    datas['level1'] = con[0]
                    datas['level2'] = con[1]
                    datas['level3'] = con[2]
                    datas['level4'] = con[3]
                    datas['level5'] = con[4]
                elif con[1]:
                    datas['level2'] = con[1]
                    datas['level3'] = con[2]
                    datas['level4'] = con[3]
                    datas['level5'] = con[4]
                elif con[2]:
                    datas['level3'] = con[2]
                    datas['level4'] = con[3]
                    datas['level5'] = con[4]
                elif con[3]:
                    datas['level4'] = con[3]
                    datas['level5'] = con[4]
                elif con[4]:
                    datas['level5'] = con[4]
                # 若果四级有一级有，则走此分支
                if datas['level1'] or datas['level2'] or datas['level3'] or datas['level4'] or datas['level5']:
                    # 查询是否存在相应的问题类型，若存在则将问题放在此类下
                    res = DS.searchType(datas)
                    if not res:
                        # 添加问题分类信息
                        datas['mark'] = ''
                        datas['createBy'] = 'admin'
                        ty = DS.addTypeQuestion(datas)
                        if not ty:
                            errorCode = -4
                            errorMsg = '添加分类失败'
                            break

                errorCode = 0
                errorMsg = '添加ok'
            else:
                errorCode = -1
                errorMsg = '无问题添加'

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg

    }


def getTestInfo(sid, cmd, datas):
    '''获取分类'''
    errorCode = -1
    errorMsg = ''

    try:
        res = DS.getTestAllInfo(datas)
    except:
        errorCode = -1
        errorMsg = '获取信息异常'
        return {
            "errorCode": errorCode,
            "errorMsg": errorMsg
        }
    else:
        con = set()
        for ct in res:
            # con = DS.getLevel1Type(ct)
            # ct['categories'] = con
            con.add(ct['categories'])
        total = len(res)
        # datas['id'] = ''
        # categories = DS.getLevel1Type(datas)
        categories = list(con)
        categories.insert(0, '全部')
        errorCode = 0
        errorMsg = '获取ok'

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg,
        "return": {
            "total": total,
            "categories": categories,
            "evaluations": res
        }
    }


@CommonDag.login_required
def getQuestion(sid, cmd, datas):
    '''获取问题
        id:问卷id
        session_id:
    '''
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
        errorCode = -7
        errorMsg = 'session_id为空'
    else:
        # 回答者的id
        datas['user_id'] = int(base64.b64decode(datas['session_id'].encode()).decode())

    if not errorMsg:
        # 判断是否是正在答题的问卷
        t = DS.searchTestStatus(datas)
        if not t:
            # todo：sprint3计划, 添加答卷数量 modify：20180716
            # 判断是否超过三个答卷， 若超过则提示不允许作答
            answer_count = DS.getAnswerCount(datas)
            if answer_count >= 3:
                errorCode = -8
                errorMsg = '正在答卷数量不能超过三个'
                return {
                    "errorCode": errorCode,
                    "errorMsg": errorMsg
                }
        # todo:添加点击数量 date:20180911
        datas['evaluationId'] = datas['id']
        hot_info = DS.get_test_hot_info(datas)
        if not hot_info:
            errorCode = -9
            errorMsg = '获取问卷点击数量错误'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }
        else:
            # 点击数量加1
            hot_info['evaluationId'] = datas['id']
            hot_info['attrV'] = hot_info['quantity'] + 1
            hot_info['attr'] = "quantity"
            DS.update_hot_info(hot_info)

        result = DS.getQuestionsInfo(datas)
        # 转换字符串
        result = json.loads(result)
        count = len(result)
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
                resp = DS.addTotalScoreInfo(datas)
                if not resp:
                    errorCode = -5
                    errorMsg = '添加信息失败'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }
                else:
                    con = dict()
                    con['idx'] = resp
                    answered_count = 1
            elif con['idx']:
                data = dict()
                data['id'] = con['idx']
                try:
                    info = DS.getAnswerInfo(data)
                except:
                    errorCode = -6
                    errorMsg = '获取答案信息失败'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }
                else:
                    questioned_count = DS.getQuestionedCount(con)
                    if count > questioned_count:
                        answered_count = questioned_count + 1
                    else:
                        answered_count = questioned_count

            # 获取状态
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


def getTestId(sid, cmd, datas):
    '''模糊查询
    :keywords
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('keywords', datas):
        errorCode = -2
        errorMsg = '搜索关键字为空'

    if not errorMsg:
        try:
            res = DS.getTestId(datas)
        except:
            errorCode = -1
            errorMsg = '模糊查询异常'
        else:
            errorCode = 0
            errorMsg = '查询ok'
        return {
            "errorCode": errorCode,
            "errorMsg": errorMsg,
            "result": res
            }
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def addAnswer(sid, cmd, datas):
    '''统计答题结果
        questionId：问题id
        answer：答案序号
        expectData:期望值序号 todo：sprint2迭代
        evaluationId 问卷id
        status:是否回答完答题 0未完成 1完成
        idx :评测主表id
        session_id:
    '''
    errorCode = -1
    errorMsg = ''
    p5 = 1
    p4 = 1
    p3 = 1
    p2 = 1
    p1 = 1
    p = 1
    total = 0
    expectScore = 0
    if not CommonDag.hasKeyData('questionId', datas):
        errorCode = -2
        errorMsg = '问题id信息为空'
    elif not CommonDag.judgeIntType('questionId', datas):
        errorCode = -3
        errorMsg = '问题id格式错误，为整数'
    elif not CommonDag.hasKeyData('answer', datas):
        errorCode = -4
        errorMsg = '答案信息为空'
    elif not CommonDag.judgeIntType('answer', datas):
        errorCode = -5
        errorMsg = '答案格式错误，为整数'
    elif not CommonDag.hasKeyData('evaluationId', datas):
        errorCode = -6
        errorMsg = '问卷id信息为空'
    elif not CommonDag.judgeIntType('evaluationId', datas):
        errorCode = -7
        errorMsg = '问卷id类型错误，应该为整数'
    elif not CommonDag.hasKeyData('status', datas):
        errorCode = -8
        errorMsg = '是否答完题的状态为空'
    elif not CommonDag.judgeIntType('status', datas):
        errorCode = -9
        errorMsg = '是否答完题的状态类型错误，应该为整数'
    elif datas['status'] not in [0, 1]:
        errorCode = -10
        errorMsg = '答题状态超范围，选 0或1'
    elif not CommonDag.hasKeyData('idx', datas):
        errorCode = -11
        errorMsg = '评测主表id为空'
    elif not CommonDag.judgeIntType('idx', datas):
        errorCode = -12
        errorMsg = '评测主表id类型错误，应该为整数'
    elif not DS.uniqueIdx(datas):
        errorCode = -13
        errorMsg = '评测主表id不存在'
    # todo:sprint2迭代  date:20180706
    elif not CommonDag.hasKeyData('expectData', datas):
        errorCode = -18
        errorMsg = '期望值为空'
    elif not CommonDag.judgeIntType('expectData', datas):
        errorCode = -19
        errorMsg = '期望值格式错误，为整数'
    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -21
        errorMsg = 'session_id为空'
    else:
        datas['user_id'] = int(base64.b64decode(datas['session_id'].encode()).decode())

    if not errorMsg:
        datas['id'] = datas['evaluationId']
        if not DS.searchTestId(datas):
            errorCode = -14
            errorMsg = '问卷id不存在'
        else:
            result = DS.getQuestionsInfo(datas)
            # 转换字符串
            result = json.loads(result)
            if datas['questionId'] not in result:
                errorCode = -15
                errorMsg = '问题id不在对应序列中'
            elif datas['answer'] not in [1, 2, 3, 4, 5, 6]:
                errorCode = -16
                errorMsg = '答案数据超范围,应该为1-6'
            # todo:sprint2迭代  date:20180706
            elif datas['expectData'] not in [1, 2, 3, 4, 5, 6]:
                errorCode = -20
                errorMsg = '期望数据超范围,应该为1-6'

    if not errorMsg:
        # datas['answerUser'] = 'admin'
        # 获取答题信息
        con = DS.searchAnswerInfo(datas)
        if con:
            # 删除答题信息
            DS.deleteAnswerInfo(datas)
        # 获取企业id
        ent_id = DS.get_enterprise_id(datas)
        if not ent_id:
            errorCode = -23
            errorMsg = '获取企业id失败'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }
        res = DS.addAnswerInfo(datas)
        if not res:
            errorCode = -17
            errorMsg = '添加信息失败'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }
        else:
            if datas['status']:
                # 更新评测状态和评测总分
                # sm = DS.totalScore(datas)
                # if sm['total']:
                #     datas['score'] = sm['total']
                # todo: sprint6加权统计分数 date:20180816
                try:
                    cr = DS.get_relation_power_and_level(datas)
                except:
                    errorCode = -18
                    errorMsg = '获取层级关系失败'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }
                else:
                    # 统计模块权重
                    for i in range(0, 5):
                        datas['level'] = i
                        try:
                            qw = DS.statistic_power_value(datas)
                        except:
                            errorCode = -19
                            errorMsg = '获取模块权重失败'
                            return {
                                "errorCode": errorCode,
                                "errorMsg": errorMsg
                            }
                        else:
                            for temp in qw:
                                temp['level'] = i+1
                                temp['id'] = datas['evaluationId']
                                cv = DS.search_model_count_power(temp)
                                # if (not cv or not cv['idx']) and temp['level']:
                                if not cv or not cv['idx']:
                                    # DS.delete_model_count_power(temp)
                                    rs = DS.add_model_count_power(temp)
                                    if not rs:
                                        errorCode = -20
                                        errorMsg = '更新模块权重失败'
                                        return {
                                            "errorCode": errorCode,
                                            "errorMsg": errorMsg
                                        }
                                    else:
                                        temp['pid'] = rs
                                        temp['eid'] = ent_id['enterpriseId']
                                        df = DS.add_model_score_info(temp)
                                        if not df:
                                            errorCode = -22
                                            errorMsg = '添加模块信息失败'
                                            return {
                                                "errorCode": errorCode,
                                                "errorMsg": errorMsg
                                            }
                                else:
                                    temp['pid'] = cv['idx']
                                    temp['eid'] = ent_id['enterpriseId']
                                    scp = DS.search_model_score_info(temp)
                                    if not scp:
                                        df = DS.add_model_score_info(temp)
                                        if not df:
                                            errorCode = -22
                                            errorMsg = '添加模块信息失败'
                                            return {
                                                "errorCode": errorCode,
                                                "errorMsg": errorMsg
                                            }
                                    else:
                                        upp = DS.update_model_score_flag(temp)
                                        pass

                    for ct in cr:
                        con = ''
                        for i in range(5, 0, -1):
                            m = 'level' + str(i)
                            if ct[m]:
                                ct["type"] = i
                                pt = DS.get_model_power_count(ct)
                                if not pt:
                                    errorCode = -20
                                    errorMsg = '获取模块权重失败'
                                    return {
                                        "errorCode": errorCode,
                                        "errorMsg": errorMsg
                                    }
                                else:
                                    if i == 5:
                                        n = 'powerL' + str(i)
                                        if not pt['flag']:
                                            ct['flag'] = 1
                                            p5 = Decimal(ct[n] / pt['power'])
                                            ct['p'] = p5
                                            con = DS.update_model_power_value(ct)
                                            if not con:
                                                errorCode = -21
                                                errorMsg = '更新模块权重值失败'
                                                return {
                                                    "errorCode": errorCode,
                                                    "errorMsg": errorMsg
                                                }
                                        else:
                                            p5 = pt['power']

                                    elif i == 4:
                                        n = 'powerL' + str(i)
                                        if not pt['flag']:
                                            ct['flag'] = 1
                                            p4 = Decimal(ct[n] / pt['power'])
                                            ct['p'] = p4
                                            con = DS.update_model_power_value(ct)
                                            if not con:
                                                errorCode = -21
                                                errorMsg = '更新模块权重值失败'
                                                return {
                                                    "errorCode": errorCode,
                                                    "errorMsg": errorMsg
                                                }
                                        else:
                                            p4 = pt['power']
                                    elif i == 3:
                                        n = 'powerL' + str(i)
                                        if not pt['flag']:
                                            ct['flag'] = 1
                                            p3 = Decimal(ct[n] / pt['power'])
                                            ct['p'] = p3
                                            con = DS.update_model_power_value(ct)
                                            if not con:
                                                errorCode = -21
                                                errorMsg = '更新模块权重值失败'
                                                return {
                                                    "errorCode": errorCode,
                                                    "errorMsg": errorMsg
                                                }
                                        else:
                                            p3 = pt['power']

                                    elif i == 2:
                                        n = 'powerL' + str(i)
                                        if not pt['flag']:
                                            ct['flag'] = 1
                                            p2 = Decimal(ct[n] / pt['power'])
                                            ct['p'] = p2
                                            con = DS.update_model_power_value(ct)
                                            if not con:
                                                errorCode = -21
                                                errorMsg = '更新模块权重值失败'
                                                return {
                                                    "errorCode": errorCode,
                                                    "errorMsg": errorMsg
                                                }
                                        else:
                                            p2 = pt['power']
                                    elif i == 1:
                                        n = 'powerL' + str(i)
                                        if not pt['flag']:
                                            ct['flag'] = 1
                                            p1 = Decimal(ct[n] / pt['power'])
                                            ct['p'] = p1
                                            con = DS.update_model_power_value(ct)
                                            if not con:
                                                errorCode = -21
                                                errorMsg = '更新模块权重值失败'
                                                return {
                                                    "errorCode": errorCode,
                                                    "errorMsg": errorMsg
                                                }
                                        else:
                                            p1 = pt['power']

                        q_count = DS.get_question_count(ct)
                        if not q_count:
                            errorCode = -22
                            errorMsg = '获取题目权重值失败'
                            return {
                                "errorCode": errorCode,
                                "errorMsg": errorMsg
                            }
                        else:
                            p = Decimal(1 / len(q_count))
                        count_score = ct['score'] * p * p1 * p2 * p3 * p4 * p5
                        expect_score = ct['expectScore'] * p * p1 * p2 * p3 * p4 * p5
                        total += count_score
                        expectScore += expect_score

                datas['score'] = total
                datas['expectScore'] = expectScore
                st = DS.updateMainTestStatus(datas)
                if not st:
                    errorCode = -1
                    errorMsg = '更新信息失败'
                else:
                    errorCode = 0
                    errorMsg = '添加ok'
        errorCode = 0
        errorMsg = '添加ok'

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def getTotalScoreInfo(sid, cmd, datas):
    '''统计总分和题目总分及其相关的内容
        evaluationId 问卷id
        idx :评测主表id
        session_id:
    '''
    errorCode = -1
    errorMsg = ''
    my_score = 0
    total_score = 0
    if not CommonDag.hasKeyData('evaluationId', datas):
        errorCode = -2
        errorMsg = '问卷id为空'
    elif not CommonDag.judgeIntType('evaluationId', datas):
        errorCode = -3
        errorMsg = '问卷id类型错误'
    elif not CommonDag.hasKeyData('idx', datas):
        errorCode = -4
        errorMsg = '评测id为空'
    elif not CommonDag.judgeIntType('idx', datas):
        errorCode = -5
        errorMsg = '评测id类型错误'
    elif not DS.uniqueTestMain(datas):
        errorCode = -6
        errorMsg = '评测主表id不存在或者问卷id不存在'
    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -8
        errorMsg = 'session_id为空'
    else:
        datas['user_id'] = int(base64.b64decode(datas['session_id'].encode()).decode())

    if not errorMsg:
        self_info = DS.getTestScore(datas)
        if self_info['score'] and self_info['endTime']:
            my_score += self_info['score']
            testTime = self_info['endTime']
            datas['id'] = datas['evaluationId']
            result = DS.getQuestionsInfo(datas)
            # 转换字符串
            result = json.loads(result)
            for temp in result:
                datas['qId'] = temp
                rt = DS.getQuestionInfo(datas)
                if not rt:
                    errorCode = -7
                    errorMsg = '问题不存在'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }
                else:
                    rt['type'] = rt['answerType']
                    # rt['length'] = len(rt['answerLists'])
                    rt['length'] = 1
                    # 如果是选择题1类，
                    # todo:目前讨论是选择题要什么样的同分策略就加什么样的策略，却分按照answerType来就ok
                    if rt['type'] == 1:
                        total = DS.GetTotalScore(rt)
                        total_score += total['score']
                        errorCode = 0
                        errorMsg = '获取ok'
                    else:
                        pass
        else:
            errorCode = -1
            errorMsg = '评测主表id不存在'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }

        return {
            "errorCode": errorCode,
            "errorMsg": errorMsg,
            "return": {
                "my_score": my_score,
                "total_score": total_score,
                "testTime": testTime
            }
        }
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def getLevelInfo(sid, cmd, datas):
    '''获取各层级的信息
        evaluationId 问卷id
        idx :评测主表id
        level: 1
        session_id:
    '''
    errorCode = -1
    errorMsg = ''
    total = 0
    if not CommonDag.hasKeyData('evaluationId', datas):
        errorCode = -2
        errorMsg = '问卷id为空'
    elif not CommonDag.judgeIntType('evaluationId', datas):
        errorCode = -3
        errorMsg = '问卷id类型错误，为整数'
    elif not CommonDag.hasKeyData('idx', datas):
        errorCode = -4
        errorMsg = '评测id为空'
    elif not CommonDag.judgeIntType('idx', datas):
        errorCode = -5
        errorMsg = '评测id类型错误，为整数'
    elif not DS.uniqueTestMain(datas):
        errorCode = -6
        errorMsg = '评测主表id不存在或者问卷id不存在'
    elif not CommonDag.hasKeyData('level', datas):
        errorCode = -7
        errorMsg = '等级为空'
    # 三个等级
    elif datas['level'] not in [1, 2, 3]:
        errorCode = -8
        errorMsg = '等级传入错误，应为1-3'
    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -10
        errorMsg = 'session_id为空'
    else:
        datas['user_id'] = int(base64.b64decode(datas['session_id'].encode()).decode())

    # name = ''    # total = 0    # score = 0    # lose = 0    # scorePercent = 0    # losePercent = 0
    # todo:sprint2迭代  date:20180706
    # expectScore = 0
    if not errorMsg:
        try:
            info = DS.getLevelinfo(datas)
        except:
            errorCode = -9
            errorMsg = '数据库异常'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }
        else:
            # todo:sprint2迭代  date:20180706
            for k in info:
                # 初始化各项值
                k['total'] = 0
                k['name'] = k['lev']
                k['score'] = k['score']
                # k['expectScore'] = k['expect']
                datas['id'] = datas['evaluationId']
                result = DS.getQuestionsInfo(datas)
                # 转换字符串
                result = json.loads(result)

                for temp in result:
                    datas['qId'] = temp
                    rt = DS.getQuestionInfo(datas)
                    if not rt:
                        errorCode = -1
                        errorMsg = '问题不存在'
                        return {
                            "errorCode": errorCode,
                            "errorMsg": errorMsg
                        }
                    else:
                        if k['name'] == rt['level1']:
                            rt['type'] = rt['answerType']
                            # todo:目前讨论是选择题要什么样的同分策略就加什么样的策略，却分按照answerType来就ok
                            # rt['length'] = len(rt['answerLists'])
                            rt['length'] = 1
                            # 如果是选择题
                            if rt['type'] == 1:
                                tal = DS.GetTotalScore(rt)
                                k['total'] += tal['score']
                                errorCode = 0
                                errorMsg = '获取ok'
                            else:
                                pass
                        elif k['name'] == rt['level2']:
                            rt['type'] = rt['answerType']
                            # todo: 目前讨论是选择题要什么样的同分策略就加什么样的策略，却分按照answerType来就ok
                            # rt['length'] = len(rt['answerLists'])
                            rt['length'] = 1
                            # 如果是选择题
                            if rt['type'] == 1:
                                tal = DS.GetTotalScore(rt)
                                k['total'] += tal['score']
                                errorCode = 0
                                errorMsg = '获取ok'
                            else:
                                pass
                        elif k['name'] == rt['level3']:
                            rt['type'] = rt['answerType']
                            # todo:目前讨论是选择题要什么样的同分策略就加什么样的策略，却分按照answerType来就ok
                            # rt['length'] = len(rt['answerLists'])
                            rt['length'] = 1
                            # 如果是选择题
                            if rt['type'] == 1:
                                tal = DS.GetTotalScore(rt)
                                k['total'] += tal['score']
                                errorCode = 0
                                errorMsg = '获取ok'
                            else:
                                pass
                # k['total'] = total
                k['lose'] = k['total'] - k['score']
                k['scorePercent'] = round(k['score'] * 100 / k['total'], 1)
                k['losePercent'] = 100 - k['scorePercent']

        return {
                "errorCode": errorCode,
                "errorMsg": errorMsg,
                "level": info
            }
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


# def smsVerifyCode(sid, cmd, datas):
#     '''获取短信验证码
#         mobile：
#     '''
#     errorCode = -1
#     errorMsg = ''
#     if not CommonDag.hasKeyData('mobile', datas):
#         errorCode = -5
#         errorMsg = '密码为空'
#     elif not re.match(r"1[3456789]\d{9}", datas['mobile']):
#         errorCode = -6
#         errorMsg = '手机号不符合规则'
#
#     if not errorMsg:
#         res = sms.main(datas['mobile'])
@CommonDag.login_required
def report_datas_statistic(sid, cmd, datas):
    '''获取各层级的信息
        evaluationId 问卷id
        idx :评测主表id
        session_id:
    '''
    errorCode = -1
    errorMsg = ''
    total_score = 0
    expect_score = 0
    activeL1 = dict()
    expectL1 = dict()
    l11 = dict()
    l12 = dict()
    l11L2 = dict()
    l12L2 = dict()
    l11L3 = dict()
    l12L3 = dict()
    allLv = dict()
    l11IndPec = 0
    l12IndPec = 0
    l11ProvincePec = 0
    l11CityPec = 0
    l11AreaPec = 0
    l12ProvincePec = 0
    l12CityPec = 0
    l12AreaPec = 0
    if not CommonDag.hasKeyData('evaluationId', datas):
        errorCode = -2
        errorMsg = '问卷id为空'
    elif not CommonDag.judgeIntType('evaluationId', datas):
        errorCode = -3
        errorMsg = '问卷id类型错误，为整数'
    elif not CommonDag.hasKeyData('idx', datas):
        errorCode = -4
        errorMsg = '评测id为空'
    elif not CommonDag.judgeIntType('idx', datas):
        errorCode = -5
        errorMsg = '评测id类型错误，为整数'
    elif not DS.uniqueTestMain(datas):
        errorCode = -6
        errorMsg = '评测主表id不存在或者问卷id不存在'
    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -7
        errorMsg = 'session_id为空'
    else:
        datas['user_id'] = int(base64.b64decode(datas['session_id'].encode()).decode())

    if not errorMsg:
        # 获取企业信息
        ent_info = DS.get_enterprise_info(datas)
        if not ent_info:
            errorCode = -8
            errorMsg = '获取报告企业基本信息失败'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }
        datas['eid'] = ent_info['idx']
        # 获取总分和期望分
        self_info = DS.getTestScore(datas)
        if not self_info:
            errorCode = -9
            errorMsg = '获取分数信息失败'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }
        else:
            total_score += self_info['score']
            expect_score += self_info['expectScore']
            datas['activeScore'] = Decimal(total_score)
            datas['expectScore'] = Decimal(expect_score)

        # 获取分级，模块，题号等信息
        try:
            cr = DS.get_relation_power_and_level(datas)
        except:
            errorCode = -10
            errorMsg = '获取层级关系失败'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }

        # 获取各个层级模块权重信息
        try:
            degree_info = DS.get_model_power(datas)
        except:
            errorCode = -11
            errorMsg = '获取权重信息失败'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }
        else:
            # 获取最小面模块的分值
            for temp in degree_info:
                act_model_score = 0
                exp_model_score = 0
                try:
                    q_list = DS.get_question_list(temp)
                except:
                    errorCode = -12
                    errorMsg = '获取题目列表信息失败'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }
                else:
                    if not q_list:
                        pass
                    else:
                        for ct in cr:
                            if ct['qId'] in q_list:
                                sc = Decimal(ct['score']/len(q_list))
                                ec = Decimal(ct['expectScore']/len(q_list))
                                act_model_score += sc
                                exp_model_score += ec
                        temp['act_model_score'] = act_model_score
                        temp['exp_model_score'] = exp_model_score
                        temp['entId'] = ent_info['idx']
                        up = DS.update_model_score(temp)
                        if not up:
                            errorCode = -13
                            errorMsg = '更新模块分数失败'
                            return {
                                "errorCode": errorCode,
                                "errorMsg": errorMsg
                            }

            # 获取层级模块权重信息
            for i in range(5, 0, -1):
                try:
                    degree_info1 = DS.get_model_power(datas)
                except:
                    errorCode = -14
                    errorMsg = '获取权重信息失败'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }
                else:
                    # 获取其他模块的分值
                    for temp in degree_info1:
                        if temp['level'] == i and not temp['scoreFlag']:
                            temp['type'] = i
                            temp['entId'] = ent_info['idx']
                            try:
                                ref = DS.get_model_score(temp)
                            except:
                                errorCode = -15
                                errorMsg = '获取下级模块总分失败'
                                return {
                                    "errorCode": errorCode,
                                    "errorMsg": errorMsg
                                }
                            else:
                                temp['act_model_score'] = ref['acs']
                                temp['exp_model_score'] = ref['exs']
                                up = DS.update_model_score(temp)
                                if not up:
                                    errorCode = -16
                                    errorMsg = '更新模块分数失败'
                                    return {
                                        "errorCode": errorCode,
                                        "errorMsg": errorMsg
                                    }

            # 分模型
            # todo: 目前只有两级维度
            # 获取各个层级更新模块后信息
            rap = list()
            try:
                degree_info2 = DS.get_model_power(datas)
            except:
                errorCode = -17
                errorMsg = '获取权重信息失败'
                return {
                    "errorCode": errorCode,
                    "errorMsg": errorMsg
                }
            else:
                for temp in degree_info2:
                    if temp['level'] == 1:
                        rap.append(temp['n1'])
                        s = temp['n1']
                        # score = Decimal(total_score / temp['power'])
                        score = float(temp['actModelScore'])
                        expect = float(temp['expModelScore'])
                        # expect = Decimal(expect_score / temp['power'])
                        activeL1[s] = score
                        expectL1[s] = expect

                # 二级分类
                rt = list()
                nt = list()
                for temp in degree_info2:
                    if temp['level'] == 2 and temp['n1'] == rap[0]:
                        ct = dict()
                        s = temp['n1']
                        r = temp['n2']
                        # score = Decimal(activeL1[s] / temp['power'])
                        # expect = Decimal(expectL1[s] / temp['power'])
                        score = float(temp['actModelScore'])
                        expect = float(temp['expModelScore'])
                        ct["active"] = score
                        ct["expect"] = expect
                        ct['label'] = r
                        rt.append(ct)
                    elif temp['level'] == 2 and temp['n1'] == rap[1]:
                        mt = dict()
                        n = temp['n1']
                        m = temp['n2']
                        # score = Decimal(activeL1[n] / temp['power'])
                        # expect = Decimal(expectL1[n] / temp['power'])
                        score = float(temp['actModelScore'])
                        expect = float(temp['expModelScore'])
                        mt["active"] = score
                        mt["expect"] = expect
                        mt['label'] = m
                        nt.append(mt)
                l11L2['key'] = rt
                l11L2['label'] = rap[0]
                l12L2['key'] = nt
                l12L2['label'] = rap[1]

                # 三级分类
                ut = list()
                vt = list()
                for temp in degree_info2:
                    if temp['level'] == 3 and temp['n1'] == rap[0]:
                        xx = dict()
                        s = temp['n1']
                        f = temp['n2']
                        r = temp['n3']
                        score = float(temp['actModelScore'])
                        expect = float(temp['expModelScore'])
                        # score = Decimal(rt[f]["active"] / temp['power'])
                        # expect = Decimal(rt[f]["expect"] / temp['power'])
                        xx["active"] = score
                        xx["expect"] = expect
                        xx['label'] = r
                        ut.append(xx)
                    elif temp['level'] == 3 and temp['n1'] == rap[1]:
                        yy = dict()
                        n = temp['n1']
                        d = temp['n2']
                        m = temp['n3']
                        score = float(temp['actModelScore'])
                        expect = float(temp['expModelScore'])
                        # score = Decimal(rt[d]["active"] / temp['power'])
                        # expect = Decimal(rt[d]["expect"] / temp['power'])
                        yy["active"] = score
                        yy["expect"] = expect
                        yy['label'] = m
                        vt.append(yy)
                l11L3['key'] = ut
                l11L3['label'] = rap[0]
                l12L3['key'] = vt
                l12L3['label'] = rap[1]

            # todo：四级分类目前没有，预留

            # 企业id
            datas['id'] = ent_info['idx']
            datas['industry'] = ent_info['industryL1']
            datas['province'] = ent_info['province']
            datas['city'] = ent_info['city']
            datas['area'] = ent_info['area']
            for i in range(1, 6):
                datas['val'] = i
                try:
                    report_info = DS.get_report_info_compare(datas)
                except:
                    errorCode = -18
                    errorMsg = '获取企业评测相关信息失败'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }
                else:
                    if i == 1:
                        if not report_info:
                            allLv['expect'] = 0
                            allLv['active'] = 0
                            l11['label'] = rap[0]
                            l11['expect'] = 0
                            l11['active'] = 0
                            l12['label'] = rap[1]
                            l12['expect'] = 0
                            l12['active'] = 0
                        else:
                            count = len(report_info) + 1
                            ex_per = 0
                            ac_per = 0
                            l11_ex = 0
                            l11_ac = 0
                            l12_ex = 0
                            l12_ac = 0
                            for temp in report_info:
                                # todo:修改整体水平比较实际和期望都和其他企业的实际比较 date：20180911
                                if temp['activeScore'] <= expect_score:
                                    ex_per += 1
                                if temp['activeScore'] <= total_score:
                                    ac_per += 1
                                if temp['actL1'][rap[0]] <= activeL1[rap[0]]:
                                    l11_ac += 1
                                if temp['actL1'][rap[1]] <= activeL1[rap[1]]:
                                    l12_ac += 1
                                if temp['actL1'][rap[0]] <= expectL1[rap[0]]:
                                    l11_ex += 1
                                if temp['actL1'][rap[1]] <= expectL1[rap[1]]:
                                    l12_ex += 1
                            allLv['expect'] = float('%.2f' %Decimal(ex_per / count * 100))
                            allLv['active'] = float('%.2f' %Decimal(ac_per / count * 100))
                            l11['label'] = rap[0]
                            l11['expect'] = float('%.2f' %Decimal(l11_ex / count * 100))
                            l11['active'] = float('%.2f' %Decimal(l11_ac / count * 100))
                            l12['label'] = rap[1]
                            l12['expect'] = float('%.2f' %Decimal(l12_ex / count * 100))
                            l12['active'] = float('%.2f' %Decimal(l12_ac / count * 100))
                    elif i == 2:
                        if not report_info:
                            l11IndPec = 0
                            l12IndPec = 0
                        else:
                            count = len(report_info) + 1
                            industry1 = 0
                            industry2 = 0
                            for temp in report_info:
                                if temp['actL1'][rap[0]] <= activeL1[rap[0]]:
                                    industry1 += 1
                                if temp['actL1'][rap[1]] <= activeL1[rap[1]]:
                                    industry2 += 1
                            l11IndPec = Decimal(industry1 / count) * 100
                            l12IndPec = Decimal(industry2 / count) * 100
                    elif i == 3:
                        if not report_info:
                            l11ProvincePec = 0
                            l12ProvincePec = 0
                        else:
                            count = len(report_info) + 1
                            province1 = 0
                            province2 = 0
                            for temp in report_info:
                                if temp['actL1'][rap[0]] <= activeL1[rap[0]]:
                                    province1 += 1
                                if temp['actL1'][rap[1]] <= activeL1[rap[1]]:
                                    province2 += 1
                            l11ProvincePec = Decimal(province1 / count) * 100
                            l12ProvincePec = Decimal(province2 / count) * 100
                    elif i == 4:
                        if not report_info:
                            l11CityPec = 0
                            l12CityPec = 0
                        else:
                            count = len(report_info) + 1
                            city1 = 0
                            city2 = 0
                            for temp in report_info:
                                if temp['actL1'][rap[0]] <= activeL1[rap[0]]:
                                    city1 += 1
                                if temp['actL1'][rap[1]] <= activeL1[rap[1]]:
                                    city2 += 1
                            l11CityPec = Decimal(city1 / count) * 100
                            l12CityPec = Decimal(city2 / count) * 100
                    elif i == 5:
                        if not report_info:
                            l11AreaPec = 0
                            l12AreaPec = 0
                        else:
                            count = len(report_info) + 1
                            area1 = 0
                            area2 = 0
                            for temp in report_info:
                                if temp['actL1'][rap[0]] <= activeL1[rap[0]]:
                                    area1 += 1
                                if temp['actL1'][rap[1]] <= activeL1[rap[1]]:
                                    area2 += 1
                            l11AreaPec = Decimal(area1 / count) * 100
                            l12AreaPec = Decimal(area2 / count) * 100

        test_name = DS.get_test_name(datas)
        if not test_name:
            errorCode = -19
            errorMsg = '获取测试问卷名称失败'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }

        datas['test_name'] = test_name['name']
        datas['entpId'] = ent_info['idx']
        datas['name'] = ent_info['enterpriseName']
        datas['industry'] = ent_info['industryL1']
        datas['province'] = ent_info['province']
        datas['city'] = ent_info['city']
        datas['area'] = ent_info['area']
        datas['scale'] = ent_info['scale']
        datas['income'] = ent_info['income']
        # datas['expectScore'] = expect_score
        # datas['activeScore'] = total_score
        datas['actL1'] = activeL1
        datas['expL1'] = expectL1
        datas['allLv'] = allLv
        datas['l11'] = l11
        datas['l12'] = l12
        datas['l11L2'] = l11L2
        datas['l12L2'] = l12L2
        datas['l11IndPec'] = l11IndPec
        datas['l12IndPec'] = l12IndPec
        datas['l11ProvincePec'] = l11ProvincePec
        datas['l12ProvincePec'] = l12ProvincePec
        datas['l11CityPec'] = l11CityPec
        datas['l12CityPec'] = l12CityPec
        datas['l11AreaPec'] = l11AreaPec
        datas['l12AreaPec'] = l12AreaPec
        datas['l11L3'] = l11L3
        datas['l12L3'] = l12L3
        # 更新报告数据标记位
        DS.update_report_flag(datas)
        # 添加报告数据
        hm = DS.add_report_datas(datas)
        if not hm:
            errorCode = -1
            errorMsg = '添加报告数据失败'
        errorCode=0
        errorMsg = 'ok'
        return {
            "errorCode": errorCode,
            "errorMsg": errorMsg,
            "return": {
                "enterprise_id": datas['entpId'],
                "idx": datas['idx'],
                "evaluationId": datas['evaluationId']
            }
        }
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def get_report_datas(sid, cmd, datas):
    """获取报告数据
        session_id
        evaluationId ：问卷id
        enterprise_id:企业id
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
        # todo:添加热度数量 date:20180911
        hot_info = DS.get_test_hot_info(datas)
        if not hot_info:
            errorCode = -13
            errorMsg = '获取问卷点击数量错误'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }
        else:
            # 点击数量加1
            hot_info['evaluationId'] = datas['evaluationId']
            hot_info['attrV'] = hot_info['hot'] + 1
            hot_info['attr'] = "hot"
            DS.update_hot_info(hot_info)
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


def registerUser(sid, cmd, datas):
    '''注册企业用户
        email
        password
        mobile
        verifyCode
        protocol
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('email', datas):
        errorCode = -2
        errorMsg = '邮箱为空'
    elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['email'], re.I):
        errorCode = -3
        errorMsg = '邮箱不符合规则'
    elif not CommonDag.hasKeyData('password', datas):
        errorCode = -4
        errorMsg = '密码为空'
    elif not CommonDag.hasKeyData('mobile', datas):
        errorCode = -5
        errorMsg = '手机为空'
    elif not re.compile(r"^1[3456789]\d{9}$").match(datas['mobile']):
        errorCode = -6
        errorMsg = '手机号不符合规则'
    elif not CommonDag.hasKeyData('verifyCode', datas):
        errorCode = -7
        errorMsg = '验证码为空'
    elif not DS.uniqueEmail(datas):
        errorCode = -9
        errorMsg = '邮箱已注册'
    elif not DS.uniqueMobile(datas):
        errorCode = -10
        errorMsg = '电话已注册'
    # todo:添加用户协议 date：20180828
    elif not CommonDag.hasKeyData('protocol', datas):
        errorCode = -14
        errorMsg = '协议为空'
    elif datas['protocol'] != 1:
        errorCode = -15
        errorMsg = '未勾选用户协议'
    else:
        # 取验证码和时间信息
        rest = SessionHelper.Session().get(datas['mobile'] + "_sms")
        if rest:
            if datas['verifyCode'] != rest['verifyCode']:
                errorCode = -8
                errorMsg = '验证码错误'
            else:
                startTime = datetime.strptime(rest['sTime'], "%Y-%m-%d %H:%M:%S")
                endTime = datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "%Y-%m-%d %H:%M:%S")
                if (endTime - startTime).seconds > 300:
                    errorCode = -12
                    errorMsg = '验证码失效，重新获取'
        else:
            errorCode = -13
            errorMsg = '验证码不存在'

    if not errorMsg:
        # 密码加密 sha256
        datas['email'] = datas['email'].lower()
        import hashlib
        datas['password'] = hashlib.sha256(datas['password'].encode()).hexdigest()
        # 管理员
        datas['roleId'] = 1
        res = DS.addUser(datas)
        if res:
            email = base64.b64encode(datas['email'].encode()).decode()
            con = parse.urlencode({"mail": email})
            addr = config.link + con

            with open('servers/DAIG_SYS/emailTpl.html', 'r', encoding='utf-8') as f:
                    config.html_body = f.read()

            # 设置邮件链接失效期
            SessionHelper.Session().set(datas['email']+'_link', time.time())
            try:
                # 开辟线程发邮件
                th = Thread(target=CommonDag.send_mail(config.subject, datas['email'], config.html_body%(addr)))
                th.start()
                # CommonDag.send_mail(config.subject, datas['email'], config.html_body%(addr))
            except:
                # datas['attr'] = 'email'
                # datas['id'] = datas['email']
                # DS.deleteUser(datas)
                # errorCode = -11
                # 目前发送邮件失败，也注册成功，后面让用户换邮箱试试
                errorCode = 0
                errorMsg = '邮件发送失败'
            else:
                errorCode = 0
                errorMsg = '注册ok'
        else:
            errorCode = -1
            errorMsg = '添加信息失败'
    return {
        'errorCode': errorCode,
        'errorMsg': errorMsg
    }


def activeAccount(sid, cmd, datas):
    '''激活账户
    email：邮箱
    '''
    errorCode = -1
    errorMsg = ''
    start_time = ''
    if not CommonDag.hasKeyData('email', datas):
        errorCode = -2
        errorMsg = '邮箱为空'
    else:
        # 解码邮箱
        mail_str = parse.unquote(datas['email']).replace("mail=", "")
        datas['id'] = base64.b64decode(mail_str.encode()).decode()
        datas['email'] = datas['id']
        datas['attr'] = 'email'

        if DS.uniqueEmail(datas):
            errorCode = -4
            errorMsg = '邮箱未注册'
        elif DS.AccountIsActive(datas):
            errorCode = 0
            errorMsg = '账户激活'
        else:
            # 获取链接的起始时间
            s_time = SessionHelper.Session().get(datas['email']+'_link')
            if not s_time:
                # 删除用户
                datas['attr'] = 'email'
                datas['id'] = datas['email']
                DS.deleteUser(datas)
                errorCode = -6
                errorMsg = '链接已失效,请重新注册'

            else:
                e_time = time.time()
                # 目前过期时间为24小时
                if (int(e_time - s_time)) > 24 * 60 * 60:
                # if (int(e_time - s_time)) > 60:
                    # 删除用户
                    DS.deleteUser(datas)
                    errorCode = -6
                    errorMsg = '链接失效，请重新注册'
                else:
                    SessionHelper.Session().set(datas['email'] + '_link', '')

    if not errorMsg:
        res = DS.updateAccountActive(datas)
        if not res:
            errorCode = -1
            errorMsg = '激活失败'
        else:
            errorCode = 0
            errorMsg = '激活成功'

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


def login(sid, cmd, datas):
    '''登录
        id(邮箱或者电话)
        password 密码
        captchCode 验证码
    '''
    errorCode = -1
    errorMsg = ''
    session_id = 0
    firstLogin = 0
    if not CommonDag.hasKeyData('id', datas):
        errorCode = -2
        errorMsg = '账户名为空'
    elif not CommonDag.hasKeyData('password', datas):
        errorCode = -3
        errorMsg = '密码为空'
    elif not CommonHelp.hasKey('captchCode', datas):
        errorCode = -4
        errorMsg = '验证码为空'
    # 有验证码
    elif datas['captchCode']:
        if datas["captchCode"].lower() != (SessionHelper.Session().get("captcher")).lower():
            errorCode = -5
            errorMsg = "验证码错误"

    if not errorMsg:
        # 密码加密 sha256
        import hashlib
        datas['password'] = hashlib.sha256(datas['password'].encode()).hexdigest()
        # 判断是否是手机号
        if CommonDag.judgeStrIsNum('id', datas):
            datas['mobile'] = datas['id']
            datas['attr'] = 'mobile'
            if not re.compile(r"^1[3456789]\d{9}$").match(datas['id']):
                errorCode = -9
                errorMsg = '手机号不符合规则'
            elif DS.uniqueMobile(datas):
                errorCode = -10
                errorMsg = '手机号未注册'
            else:
                con = DS.AccountIsActiveAndPassword(datas)
                if not con['isActive']:
                    # 前端不想做分支判断，后端错误码返回0
                    errorCode = -6
                    # errorCode = 0
                    errorMsg = '账户未激活'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg,
                        "return": {
                            "email": con['email'],
                            "mobile": con['mobile']
                        }

                    }
                elif con['password'] != datas['password']:
                    errorCode = -7
                    errorMsg = '密码错误'
                else:
                    if con['enterpriseId']:
                        firstLogin = 0
                    else:
                        firstLogin = 1
                    email = con['email']
                    image = con['image']
                    datas['online'] = 1
                    # 保存session信息
                    session_id = con['idx']
                    st = DS.updateOnlineStatus(datas)
                    if not st:
                        errorCode = -1
                        errorMsg = '登陆失败'
                    else:
                        errorCode = 0
                        errorMsg = '登录成功'
                        return {
                            "errorCode": errorCode,
                            "errorMsg": errorMsg,
                            "image": image,
                            "email": email,
                            "mobile": datas['id'],
                            "firstLogin": firstLogin,
                            "session_id": base64.b64encode(str(session_id).encode()).decode()
                        }
        else:
            # 邮箱登陆
            datas['id'] = datas['id'].lower()
            datas['email'] = datas['id']
            datas['attr'] = 'email'
            if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['id'], re.I):
                errorCode = -8
                errorMsg = '邮箱不符合规则'
            elif DS.uniqueEmail(datas):
                errorCode = -11
                errorMsg = '邮箱未注册'
            else:
                con = DS.AccountIsActiveAndPassword(datas)
                if not con['isActive']:
                    errorCode = -6
                    errorMsg = '账户未激活'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg,
                        "return": {
                            "email": con['email'],
                            "mobile": con['mobile']
                        }

                    }
                elif con['password'] != datas['password']:
                    errorCode = -7
                    errorMsg = '密码错误'
                else:
                    if con['enterpriseId']:
                        firstLogin = 0
                    else:
                        firstLogin = 1
                    datas['online'] = 1
                    mobile = con['mobile']
                    image = con['image']
                    # 保存session信息
                    session_id = con['idx']
                    st = DS.updateOnlineStatus(datas)
                    if not st:
                        errorCode = -1
                        errorMsg = '登陆失败'
                    else:
                        errorCode = 0
                        errorMsg = '登录成功'
                        return {
                            "errorCode": errorCode,
                            "errorMsg": errorMsg,
                            "mobile": mobile,
                            "image": image,
                            "email": datas['id'],
                            "firstLogin": firstLogin,
                            "session_id": base64.b64encode(str(session_id).encode()).decode()
                        }

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg,
    }


def check_login(sid, cmd, datas):
    """检查登陆状态
        id:session_id
    """
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('id', datas):
        errorCode = -2
        errorMsg = '状态id为空'

    if not errorMsg:
        datas['id'] = int(base64.b64decode(datas['id'].encode()).decode())
        res = DS.checkUserLoginStatus(datas)
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
            # if (endTime - startTime).seconds > 180:
                errorCode = -4
                errorMsg = '登录失效，请重新登录'
            else:
                email = res['email']
                errorCode = 0
                errorMsg = '用户登录状态正常'
                return {
                    "errorCode": errorCode,
                    "errorMsg": errorMsg,
                    "email": email
                }

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


def sendSms(sid, cmd, datas):
    '''发送信息
        mobile
        type: 0：注册/修改电话时发短信 1：非注册
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('mobile', datas):
        errorCode = -2
        errorMsg = '手机号为空'
    elif not CommonDag.judgeStrIsNum('mobile', datas):
        errorCode = -3
        errorMsg = '手机号不是纯数字'
    elif not re.compile(r"^1[3456789]\d{9}$").match(datas['mobile']):
        errorCode = -4
        errorMsg = '手机号不符合规则'
    elif not CommonDag.hasKeyData('type', datas):
        errorCode = -5
        errorMsg = '类型为空'
    elif not CommonDag.judgeIntType('type', datas):
        errorCode = -6
        errorMsg = '类型错误，应该为整数'
    else:
        if not datas['type']:
            if not DS.uniqueMobile(datas):
                errorCode = -8
                errorMsg = '电话已经注册'
        else:
            if DS.uniqueMobile(datas):
                errorCode = -7
                errorMsg = '电话未注册'

    if not errorMsg:
        verifyCode = "%6d" % (random.randint(100000, 999999))
        sTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        session_value = dict()
        session_value['verifyCode'] = verifyCode
        session_value['sTime'] = sTime
        # 将验证码和时间信息保存内存数据库
        SessionHelper.Session().set(datas['mobile']+"_sms", session_value)
        # print(type(SessionHelper.Session().get(datas['mobile']+"_sms")))
        # set_sms.set(key=datas['mobile']+'_sms', value=session_value)
        TEMPLATE_PARAM = '[' + verifyCode + ']'
        try:
            res = sms.main(datas['mobile'], TEMPLATE_PARAM, config.APP_KEY, config.APP_SECRET, config.sender,
                           config.url, config.TEMPLATE_ID, config.statusCallBack)

        except:
            errorCode = -9
            errorMsg = '发送验证码异常'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg,
            }
        else:
            res = json.loads(res)
            if res['description'] == 'Success' and res['code'] == '000000':
                errorCode = 0
                errorMsg = 'ok'
            else:
                errorCode = -1
                errorMsg = '发送短信验证码异常'
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg,
    }


@CommonDag.login_required
def uploadImage(sid, cmd, datas):
    '''上传图片
        email
        type: 0：个人 1：企业
        path :图片路径
        session_id:
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('email', datas):
        errorCode = -2
        errorMsg = '邮箱信息为空'
    elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['email'], re.I):
        errorCode = -3
        errorMsg = '邮箱不符合规则'
    elif DS.uniqueEmail(datas):
        errorCode = -4
        errorMsg = '邮箱未注册'
    elif not CommonDag.hasKeyData('path', datas):
        errorCode = -5
        errorMsg = '路径为空'
    # elif os.path.getsize(datas['path'])/1024 > 1024:
    # elif len(datas['path'])/1024 > 1024:
    #     errorCode = -6
    #     errorMsg = '图片尺寸过大'
    elif not CommonDag.hasKeyData('type', datas):
        errorCode = -7
        errorMsg = '类型为空'
    elif not CommonDag.judgeIntType('type', datas):
        errorCode = -8
        errorMsg = '类型不为整数'
    elif datas['type'] not in [0, 1]:
        errorCode = -9
        errorMsg = '类型超限'
    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -14
        errorMsg = 'session_id为空'

    if not errorMsg:
        datas['email'] = datas['email'].lower()
        # try:
        #     with open(datas['path'], 'rb') as f:
        #         content = f.read()
        # except:
        #     errorCode = -10
        #     errorMsg = '读取文件异常'
        # else:
        #     name = str(uuid.uuid1()).replace("-", "")
        #     pt = './image/'+name+'.png'
        #
        # try:
        #     with open(pt, 'wb') as f:
        #         f.write(content)
        # except:
        #     errorCode = -11
        #     errorMsg = '写文件异常'
        # else:
        if datas['type']:
            path = DS.getEnterpriseInfo(datas)
            if not path:
                errorCode = -12
                errorMsg = '没有相应信息'
                return {
                    "errorCode": errorCode,
                    "errorMsg": errorMsg
                }
            # 如果之前有logo，删除
            elif path['logo']:
                try:
                    os.remove(path['logo'])
                except:
                    errorCode = -13
                    errorMsg = '删除图片失败'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }
            errorCode = 0
            errorMsg = '上传ok'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg,
                "image_url": datas['path']
            }
        else:
            path = DS.getUserInfo(datas)
            if not path:
                errorCode = -12
                errorMsg = '没有相应信息'
                return {
                    "errorCode": errorCode,
                    "errorMsg": errorMsg
                }
            # 如果之前有image，删除
            elif path['image']:
                try:
                    os.remove(path['image'])
                except:
                    errorCode = -13
                    errorMsg = '删除图片失败'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }
            # todo:更新数据库信息
            datas['image'] = datas['path']
            up = DS.updateImageInfo(datas)
            if not up:
                errorCode = -1
                errorMsg = '更新图片信息失败'
                return {
                    "errorCode": errorCode,
                    "errorMsg": errorMsg
                }
            errorCode = 0
            errorMsg = '上传ok'
        return {
            "errorCode": errorCode,
            "errorMsg": errorMsg,
            "image_url": datas['path']
        }
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def uploadImageBase64(sid, cmd, datas):
    '''上传图片
        email
        type: 0：个人 1：企业
        path :图片数据
        session_id:
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('email', datas):
        errorCode = -2
        errorMsg = '邮箱信息为空'
    elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['email'], re.I):
        errorCode = -3
        errorMsg = '邮箱不符合规则'
    elif DS.uniqueEmail(datas):
        errorCode = -4
        errorMsg = '邮箱未注册'
    elif not CommonDag.hasKeyData('path', datas):
        errorCode = -5
        errorMsg = '数据为空'
    elif not CommonDag.hasKeyData('type', datas):
        errorCode = -7
        errorMsg = '类型为空'
    elif not CommonDag.judgeIntType('type', datas):
        errorCode = -8
        errorMsg = '类型不为整数'
    elif datas['type'] not in [0, 1]:
        errorCode = -9
        errorMsg = '类型超限'
    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -14
        errorMsg = 'session_id为空'

    if not errorMsg:
        datas['email'] = datas['email'].lower()
        # 获取图片类型和大小
        format = ['png', 'jpg', 'jpeg', 'gif', 'bmp']
        type = datas['path'].split(',')[0].split('/')[1].split(';')[0].lower()
        image = datas['path'].split(',')[1]
        if type not in format:
            errorCode = -10
            errorMsg = '图片格式错误'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }
        elif len(image) / 1024 > 2048:
            errorCode = -6
            errorMsg = '图片尺寸过大'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }
        image = base64.b64decode(image)
        name = str(uuid.uuid1()).replace("-", "")
        pt = './image/'+name+'.' + type

        try:
            with open(pt, 'wb') as f:
                f.write(image)
        except:
            errorCode = -11
            errorMsg = '写文件异常'
        else:
            if datas['type']:
                path = DS.getEnterpriseInfo(datas)
                if not path:
                    pass
                    # errorCode = -12
                    # errorMsg = '没有相应信息'
                    # return {
                    #     "errorCode": errorCode,
                    #     "errorMsg": errorMsg
                    # }
                # 如果之前有logo，删除
                elif path['logo']:
                    try:
                        os.remove(path['logo'])
                    except:
                        # 异常时不阻止程序运行
                        errorCode = -13
                        errorMsg = '删除图片失败'
                        pass
                        # return {
                        #     "errorCode": errorCode,
                        #     "errorMsg": errorMsg
                        # }
                # todo:企业信息UI更新，单独列出图片上传。date：20180912
                datas['logo'] = pt
                datas['id'] = path['idx']
                up = DS.update_logo_Info(datas)
                if not up:
                    errorCode = -1
                    errorMsg = '更新企业图片信息失败'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }
                errorCode = 0
                errorMsg = '上传ok'
                # errorCode = 0
                # errorMsg = '上传ok'
                # return {
                #     "errorCode": errorCode,
                #     "errorMsg": errorMsg,
                #     "image_url": pt
                # }
            else:
                path = DS.getUserInfo(datas)
                if not path:
                    errorCode = -12
                    errorMsg = '没有相应信息'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }
                # 如果之前有image，删除
                elif path['image']:
                    try:
                        os.remove(path['image'])
                    except:
                        errorCode = -13
                        errorMsg = '删除图片失败'
                        pass
                        # return {
                        #     "errorCode": errorCode,
                        #     "errorMsg": errorMsg
                        # }
                # todo:更新数据库信息
                datas['image'] = pt
                up = DS.updateImageInfo(datas)
                if not up:
                    errorCode = -1
                    errorMsg = '更新用户图片信息失败'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg
                    }
                errorCode = 0
                errorMsg = '上传ok'
        return {
            "errorCode": errorCode,
            "errorMsg": errorMsg,
            "image_url": pt
        }
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def registerEnterpriseInfo(sid, cmd, datas):
    '''注册企业信息
        email
        session_id
        enterpriseName,shortName,enterpriseCode,province,city,area,
        industryL1,industryL2,industryL3,industryL4,industryL5`scale`,income
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('email', datas):
        errorCode = -2
        errorMsg = '邮箱信息为空'
    elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['email'], re.I):
        errorCode = -3
        errorMsg = '邮箱不符合规则'
    elif DS.uniqueEmail(datas):
        errorCode = -4
        errorMsg = '邮箱未注册'
    elif not CommonDag.hasKeyData('enterpriseName', datas):
        errorCode = -5
        errorMsg = '企业名称为空'
    elif not CommonDag.hasKeyData('shortName', datas):
        errorCode = -6
        errorMsg = '企业简称为空'
    # elif not CommonHelp.hasKey('logo', datas):
    #     errorCode = -7
    #     errorMsg = 'logo为空'
    elif not CommonHelp.hasKey('enterpriseCode', datas):
        errorCode = -8
        errorMsg = '组织机构代码为空'
    elif not CommonDag.hasKeyData('province', datas):
        errorCode = -9
        errorMsg = '所在地区省为空'
    elif not CommonDag.hasKeyData('city', datas):
        errorCode = -10
        errorMsg = '所在地区市为空'
    elif not CommonDag.hasKeyData('area', datas):
        errorCode = -11
        errorMsg = '所在地区县省为空'
    elif not CommonDag.hasKeyData('industryL1', datas):
        errorCode = -12
        errorMsg = '所属行业为空'
    elif not CommonHelp.hasKey('industryL2', datas):
        errorCode = -13
        errorMsg = '行业二级为空'
    elif not CommonHelp.hasKey('industryL3', datas):
        errorCode = -14
        errorMsg = '行业三级为空'
    elif not CommonHelp.hasKey('scale', datas):
        errorCode = -15
        errorMsg = '公司规模为空'
    elif not CommonHelp.hasKey('income', datas):
        errorCode = -16
        errorMsg = '公式收入为空'
    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -18
        errorMsg = 'session_id为空'
    elif not CommonHelp.hasKey('industryL4', datas):
        errorCode = -19
        errorMsg = '行业四级为空'
    elif not CommonHelp.hasKey('industryL5', datas):
        errorCode = -20
        errorMsg = '行业五级为空'
    else:
        if datas['enterpriseCode']:
            if len(datas['enterpriseCode']) == 9 and not(re.compile(r'^[0-9A-Z]{8}[0-9X]{1}$').match(datas['enterpriseCode'])):
                errorCode = -21
                errorMsg = '组织机构代码规则不符合规范'
            elif len(datas['enterpriseCode']) == 18 and not(re.compile(r'^[159Y]{1}[1239]{1}[0-9]{6}[0-9A-Z]{10}$').match(datas['enterpriseCode'])):
                errorCode = -22
                errorMsg = '社会信用代码规则不符合规范'
            elif len(datas['enterpriseCode']) not in [9, 18]:
                errorCode = -23
                errorMsg = '组织机构代码/社会信用代码长度不符合规范（9位或18位）'

    if not errorMsg:
        datas['email'] = datas['email'].lower()
        datas['flag'] = []
        res = DS.addEnterpriseInfo(datas)
        if not res:
            errorCode = -1
            errorMsg = '添加信息失败'
        else:
            datas['id'] = res
            con = DS.updateUserEnterpriseId(datas)
            if not con:
                errorCode = -17
                errorMsg = '更新企业id失败'
            else:
                errorCode = 0
                errorMsg = '注册成功'

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def getEnterpriseInfo(sid, cmd, datas):
    '''获取企业用户信息
        email
        session_id
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('email', datas):
        errorCode = -2
        errorMsg = '邮箱信息为空'
    elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['email'], re.I):
        errorCode = -3
        errorMsg = '邮箱不符合规则'
    elif DS.uniqueEmail(datas):
        errorCode = -4
        errorMsg = '邮箱未注册'
    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -5
        errorMsg = 'session_id为空'

    if not errorMsg:
        datas['email'] = datas['email'].lower()
        res = DS.getEnterpriseInfo(datas)
        if not res:
            errorCode = -1
            errorMsg = '获取信息失败'
        else:
            errorCode = 0
            errorMsg = '获取成功'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg,
                "return": res
            }

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def modifyEnterpriseInfo(sid, cmd, datas):
    '''修改企业信息
        email
        session_id
        enterpriseName,shortName,enterpriseCode,province,city,area,
        industryL1,industryL2,industryL3,industryL4,industryL5`scale`,income
    '''
    errorMsg = ''
    errorCode = -1
    if not CommonDag.hasKeyData('email', datas):
        errorCode = -2
        errorMsg = '邮箱信息为空'
    elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['email'], re.I):
        errorCode = -3
        errorMsg = '邮箱不符合规则'
    elif DS.uniqueEmail(datas):
        errorCode = -4
        errorMsg = '邮箱未注册'
    elif not CommonDag.hasKeyData('enterpriseName', datas):
        errorCode = -5
        errorMsg = '企业名称为空'
    elif not CommonDag.hasKeyData('shortName', datas):
        errorCode = -6
        errorMsg = '企业简称为空'
    # elif not CommonHelp.hasKey('logo', datas):
    #     errorCode = -7
    #     errorMsg = 'logo为空'
    elif not CommonHelp.hasKey('enterpriseCode', datas):
        errorCode = -8
        errorMsg = '组织机构代码为空'
    elif not CommonDag.hasKeyData('province', datas):
        errorCode = -9
        errorMsg = '所在地区省为空'
    elif not CommonDag.hasKeyData('city', datas):
        errorCode = -10
        errorMsg = '所在地区市为空'
    elif not CommonDag.hasKeyData('area', datas):
        errorCode = -11
        errorMsg = '所在地区县省为空'
    elif not CommonDag.hasKeyData('industryL1', datas):
        errorCode = -12
        errorMsg = '所属行业为空'
    elif not CommonHelp.hasKey('industryL2', datas):
        errorCode = -13
        errorMsg = '行业二级为空'
    elif not CommonHelp.hasKey('industryL3', datas):
        errorCode = -14
        errorMsg = '行业三级为空'
    elif not CommonHelp.hasKey('scale', datas):
        errorCode = -15
        errorMsg = '公司规模为空'
    elif not CommonHelp.hasKey('income', datas):
        errorCode = -16
        errorMsg = '公式收入为空'
    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -17
        errorMsg = 'session_id为空'
    elif not CommonHelp.hasKey('industryL4', datas):
        errorCode = -18
        errorMsg = '行业四级为空'
    elif not CommonHelp.hasKey('industryL5', datas):
        errorCode = -19
        errorMsg = '行业五级为空'
    else:
        if datas['enterpriseCode']:
            if len(datas['enterpriseCode']) == 9 and not(re.compile(r'^[0-9A-Z]{8}[0-9X]{1}$').match(datas['enterpriseCode'])):
                errorCode = -20
                errorMsg = '组织机构代码规则不符合规范'
            elif len(datas['enterpriseCode']) == 18 and not(re.compile(r'^[159Y]{1}[1239]{1}[0-9]{6}[0-9A-Z]{10}$').match(datas['enterpriseCode'])):
                errorCode = -21
                errorMsg = '社会信用代码规则不符合规范'
            elif len(datas['enterpriseCode']) not in [9, 18]:
                errorCode = -22
                errorMsg = '组织机构代码/社会信用代码长度不符合规范（9位或18位）'

    if not errorMsg:
        # path = DS.getEnterpriseInfo(datas)
        # if not path:
        #     errorCode = -17
        #     errorMsg = '没有相应信息'
        # # 如果之前有logo，删除
        # elif path['logo']:
        #     os.remove("../../"+path['logo'])
        #
        # if not errorMsg:
        datas['email'] = datas['email'].lower()
        res = DS.modifyEnterpriseInfo(datas)
        if not res:
            errorCode = -1
            errorMsg = '修改信息失败'
        else:
            # 获取企业logo放到后面做，预留
            errorCode = 0
            errorMsg = '修改成功'
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def resetPasswordByEmail(sid, cmd, datas):
    '''通过邮件修改密码
        email
        session_id
        type 0:后台修改密码发短信验证码 1：后台修改邮箱发邮件验证按
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('email', datas):
        errorCode = -2
        errorMsg = '邮箱为空'
    elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['email'], re.I):
        errorCode = -3
        errorMsg = '邮箱不符合规则'
    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -5
        errorMsg = 'session_id为空'
    elif not CommonDag.hasKeyData('type', datas):
        errorCode = -7
        errorMsg = '类型为空'
    elif datas['type'] not in [0, 1]:
        errorCode = -8
        errorMsg = '类型错误，选择0-1'
    else:
        if not datas['type']:
            if DS.uniqueEmail(datas):
                errorCode = -4
                errorMsg = '邮箱未注册'
        else:
            if not DS.uniqueEmail(datas):
                errorCode = -6
                errorMsg = '邮箱已经注册'

    if not errorMsg:
        datas['email'] = datas['email'].lower()
        # 主题
        subject = '账户验证码'
        number = "%6d"%(random.randint(100000, 999999))
        # cd = base64.b64encode(datas['email'].encode()).decode()
        # addr = config.link + cd + '&time=' + startTime
        vTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        # g.vNumber = number
        session_value = dict()
        session_value['verifyCode'] = number
        session_value['vTime'] = vTime
        # 将验证码和时间信息保存内存数据库
        SessionHelper.Session().set(datas['email'] + "_email", session_value)
        with open('servers/DAIG_SYS/emailCode.html', 'r', encoding='utf-8') as f:
                html_body = f.read()

        try:
            # 开辟线程发邮件
            th = Thread(target=CommonDag.send_mail(subject, datas['email'], html_body%(number)))
            th.start()
            # CommonDag.send_mail(config.subject, datas['email'], config.html_body%(addr))
        except:
            errorCode = -1
            errorMsg = '邮件发送失败'
        else:
            errorCode = 0
            errorMsg = 'ok'
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def checkVerifyCodeByEmail(sid, cmd, datas):
    '''校验邮件验证码
        email
        verifyCode
        session_id
    '''
    errorCode = -1
    errorMsg  = ''
    if not CommonDag.hasKeyData('email', datas):
        errorCode = -6
        errorMsg = '邮箱为空'
    elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['email'], re.I):
        errorCode = -7
        errorMsg = '邮箱不符合规则'
    elif DS.uniqueEmail(datas):
        errorCode = -8
        errorMsg = '邮箱未注册'
    elif not CommonDag.hasKeyData('verifyCode', datas):
        errorCode = -2
        errorMsg = '验证码为空'
    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -4
        errorMsg = 'session_id为空'
    else:
        datas['email'] = datas['email'].lower()
        rest = SessionHelper.Session().get(datas['email']+'_email')
        if rest:
            startTime = datetime.strptime(rest['vTime'], "%Y-%m-%d %H:%M:%S")
            endTime = datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "%Y-%m-%d %H:%M:%S")
            if (endTime - startTime).seconds > 300:
                errorCode = -1
                errorMsg = '验证码失效，重新获取'
            elif datas['verifyCode'] != rest['verifyCode']:
                errorCode = -3
                errorMsg = '验证码错误'
            else:
                errorCode = 0
                errorMsg = '验证ok'
        else:
            errorCode = -5
            errorMsg = '验证码不存在'

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def checkVerifyCodeByMobile(sid, cmd, datas):
    '''校验手机验证码
            mobile
            verifyCode
            session_id
        '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('mobile', datas):
        errorCode = -3
        errorMsg = '密码为空'
    elif not re.compile(r"^1[3456789]\d{9}$").match(datas['mobile']):
        errorCode = -4
        errorMsg = '手机号不符合规则'
    elif not CommonDag.hasKeyData('verifyCode', datas):
        errorCode = -5
        errorMsg = '验证码为空'

    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -6
        errorMsg = 'session_id为空'
    else:
        rest = SessionHelper.Session().get(datas['mobile'] + "_sms")
        if rest:
            startTime = datetime.strptime(rest['sTime'], "%Y-%m-%d %H:%M:%S")
            endTime = datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "%Y-%m-%d %H:%M:%S")
            if (endTime - startTime).seconds > 300:
                errorCode = -1
                errorMsg = '验证码失效，重新获取'
            elif datas['verifyCode'] != rest['verifyCode']:
                errorCode = -2
                errorMsg = '验证码错误'
            else:
                errorCode = 0
                errorMsg = '验证ok'
        else:
            errorCode = -7
            errorMsg = '验证码不存在'

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def resetPassword(sid, cmd, datas):
    '''重置密码
    id 邮箱或者手机
    password 密码
    session_id
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('password', datas):
        errorCode = -2
        errorMsg = '密码为空'
    elif not CommonDag.hasKeyData('id', datas):
        errorCode = -5
        errorMsg = '邮箱或手机为空'
    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -6
        errorMsg = 'session_id为空'
    elif CommonDag.judgeStrIsNum('id', datas):
        datas['attr'] = 'mobile'
        if not re.compile(r"^1[3456789]\d{9}$").match(datas['id']):
            errorCode = -3
            errorMsg = '手机号不符合规则'
    else:
        # 邮箱登陆
        datas['id'] = datas['id'].lower()
        datas['attr'] = 'email'
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['id'], re.I):
            errorCode = -4
            errorMsg = '邮箱不符合规则'

    if not errorMsg:
        # 密码加密 sha256
        import hashlib
        datas['password'] = hashlib.sha256(datas['password'].encode()).hexdigest()
        res = DS.modifyPassword(datas)
        if not res:
            errorCode = -1
            errorMsg = '修改密码失败'
        else:
            cl = DS.clearSessionTime(datas)
            if not cl:
                errorCode = -2
                errorMsg = '删除session时间失败'
            else:
                errorCode = 0
                errorMsg = '修改密码ok'
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def getUserInformation(sid, cmd, datas):
    '''获取用户信息
        email
        session_id
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('email', datas):
        errorCode = -2
        errorMsg = '邮箱为空'
    elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['email'], re.I):
        errorCode = -3
        errorMsg = '邮箱不符合规则'
    elif DS.uniqueEmail(datas):
        errorCode = -4
        errorMsg = '邮箱未注册'
    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -5
        errorMsg = 'session_id为空'

    if not errorMsg:
        datas['email'] = datas['email'].lower()
        res = DS.getUserInfo(datas)
        if not res:
            errorCode = -1
            errorMsg = '获取失败'
        else:
            errorCode = 0
            errorMsg = '获取成功'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg,
                "result":res
            }
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def modifyUserInfo(sid, cmd, datas):
    '''修改用户信息
        email
        department,`position`,birthday,gender,
        session_id
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('email', datas):
        errorCode = -2
        errorMsg = '邮箱为空'
    elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['email'], re.I):
        errorCode = -3
        errorMsg = '邮箱不符合规则'
    elif DS.uniqueEmail(datas):
        errorCode = -4
        errorMsg = '有未注册'
    elif not CommonHelp.hasKey('birthday', datas):
        errorCode = -5
        errorMsg = '出生日期为空'
    elif not CommonHelp.hasKey('department', datas):
        errorCode = -6
        errorMsg = '部门为空'
    elif not CommonHelp.hasKey('position', datas):
        errorCode = -7
        errorMsg = '职位为空'
    elif not CommonDag.hasKeyData('gender', datas):
        errorCode = -8
        errorMsg = '性别为空'
    elif not CommonDag.judgeIntType('gender', datas):
        errorCode = 9
        errorMsg = '性别不为整数'
    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -10
        errorMsg = 'session_id为空'

    if not errorMsg:
        datas['email'] = datas['email'].lower()
        up = DS.updateUserInfo(datas)
        if not up:
            errorCode = -1
            errorMsg = '更新失败'
        else:
            errorCode = 0
            errorMsg = '更新成功'
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def modifyUserName(sid, cmd, datas):
    '''修改用户名
        email：邮箱
        name：用户名
        session_id
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('email', datas):
        errorCode = -2
        errorMsg = '邮箱为空'
    elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['email'], re.I):
        errorCode = -3
        errorMsg = '邮箱不符合规则'
    elif DS.uniqueEmail(datas):
        errorCode = -4
        errorMsg = '邮箱未注册'
    elif not CommonDag.hasKeyData('name', datas):
        errorCode = -5
        errorMsg = '姓名为空'
    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -6
        errorMsg = 'session_id为空'

    if not errorMsg:
        datas['email'] = datas['email'].lower()
        up = DS.modifyName(datas)
        if not up:
            errorCode = -1
            errorMsg = '更新失败'
        else:
            errorCode = 0
            errorMsg = '更新成功'
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


def logout(sid, cmd, datas):
    '''退出接口
        email
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('email', datas):
        errorCode = -2
        errorMsg = '邮箱为空'
    elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['email'], re.I):
        errorCode = -3
        errorMsg = '邮箱不符合规则'
    elif DS.uniqueEmail(datas):
        errorCode = -4
        errorMsg = '邮箱未注册'

    if not errorMsg:
        datas['email'] = datas['email'].lower()
        out = DS.logout(datas)
        if not out:
            errorCode = -1
            errorMsg = '登出失败'
        else:
            errorCode = 0
            errorMsg = '成功'

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


def get_industry_type(sid, cmd, datas):
    '''获取分类
        value: 获取一级直接传空,其他传入上级的值
    '''

    errorCode = -1
    errorMsg = ''
    if not CommonHelp.hasKey('value', datas):
        errorCode = -2
        errorMsg = '传入值为空'

    if not errorMsg:
        con = DS.getIndustryInfo(datas)
        if not con:
            errorCode = -1
            errorMsg = '获取信息失败'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }
        else:
            errorCode = 0
            errorMsg = '获取成功'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg,
                "return": con
            }

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def getUserTestAllInfo(sid, cmd, datas):
    '''获取用户评测的问卷
        session_id :
        key：关键字搜索
        status：1已完成,  2未完成 ,3全部
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('session_id', datas):
        errorCode = -2
        errorMsg = '传入session_id为空'
    elif not CommonHelp.hasKey('key', datas):
        errorCode = -4
        errorMsg = '搜索key为空'
    elif not CommonHelp.hasKey('status', datas):
        errorCode = -5
        errorMsg = '状态为空'
    elif datas['status']:
        if not CommonDag.judgeIntType('status', datas):
            errorCode = -6
            errorMsg = '状态不为整数'
        elif datas['status'] not in [1, 2, 3]:
            errorCode = -7
            errorMsg = '状态参数不正确，应为1-3'

    if not errorMsg:
        datas['user_id'] = int(base64.b64decode(datas['session_id'].encode()).decode())
        try:
            user_test_info = DS.getUserAllInfo(datas)
        except Exception as e:
            errorCode = -1
            errorMsg = '数据库异常'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }
        else:
        # if not user_test_info:
        #     errorCode = 0
        #     errorMsg = '获取用户答卷信息失败'
        # else:
            doing = list()
            done = list()
            # 获取用户中心的相关用户和企业信息
            user_enter = DS.getUserCenterInfo(datas)
            if not user_enter:
                errorCode = -8
                errorMsg = '获取工作台相关信息失败'
                return {
                    "errorCode": errorCode,
                    "errorMsg": errorMsg
                }
            for ct in user_test_info:
                ct['enterpriseId'] = user_enter['enterpriseId']
                if not ct['completeStatus']:
                    try:
                        result = DS.getQuestionsInfo(ct)
                        # 转换字符串
                        result = json.loads(result)
                        q_length = len(result)
                    except:
                        errorCode = -3
                        errorMsg = '获取问题数目异常'
                        return {
                            "errorCode": errorCode,
                            "errorMsg": errorMsg
                        }
                    else:
                        questioned_count = DS.getQuestionedCount(ct)
                        ct['answered_count'] = questioned_count
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
                        "user_enter": user_enter,
                        "doing": doing,
                        "done": done
                    }
                }
            else:
                return {
                    "errorCode": errorCode,
                    "errorMsg": errorMsg,
                    "return": {
                        "info": user_test_info
                    }
                }
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


# 忘记密码后修改接口（3个）
def resetPasswordByEmail1(sid, cmd, datas):
    '''通过邮件修改密码
        email
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('email', datas):
        errorCode = -2
        errorMsg = '邮箱为空'
    elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['email'], re.I):
        errorCode = -3
        errorMsg = '邮箱不符合规则'
    elif DS.uniqueEmail(datas):
        errorCode = -4
        errorMsg = '邮箱未注册'

    if not errorMsg:
        datas['email'] = datas['email'].lower()
        # 主题
        subject = '账户验证码'
        number = "%6d"%(random.randint(100000, 999999))
        vTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        session_value = dict()
        session_value['verifyCode'] = number
        session_value['vTime'] = vTime
        # 将验证码和时间信息保存内存数据库
        SessionHelper.Session().set(datas['email'] + "_email", session_value)
        with open('servers/DAIG_SYS/emailCode.html', 'r', encoding='utf-8') as f:
                html_body = f.read()

        try:
            # 开辟线程发邮件
            th = Thread(target=CommonDag.send_mail(subject, datas['email'], html_body%(number)))
            th.start()
            # CommonDag.send_mail(config.subject, datas['email'], config.html_body%(addr))
        except:
            errorCode = -1
            errorMsg = '邮件发送失败'
        else:
            errorCode = 0
            errorMsg = 'ok'
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


def checkVerifyCodeByEmail1(sid, cmd, datas):
    '''校验邮件验证码
        email
        verifyCode
    '''
    errorCode = -1
    errorMsg  = ''
    if not CommonDag.hasKeyData('email', datas):
        errorCode = -6
        errorMsg = '邮箱为空'
    elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['email'], re.I):
        errorCode = -7
        errorMsg = '邮箱不符合规则'
    elif DS.uniqueEmail(datas):
        errorCode = -8
        errorMsg = '邮箱未注册'
    elif not CommonDag.hasKeyData('verifyCode', datas):
        errorCode = -2
        errorMsg = '验证码为空'
    else:
        datas['email'] = datas['email'].lower()
        rest = SessionHelper.Session().get(datas['email']+'_email')
        if rest:
            startTime = datetime.strptime(rest['vTime'], "%Y-%m-%d %H:%M:%S")
            endTime = datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "%Y-%m-%d %H:%M:%S")
            if (endTime - startTime).seconds > 300:
                errorCode = -1
                errorMsg = '验证码失效，重新获取'
            elif datas['verifyCode'] != rest['verifyCode']:
                errorCode = -3
                errorMsg = '验证码错误'
            else:
                errorCode = 0
                errorMsg = '验证ok'
        else:
            errorCode = -5
            errorMsg = '验证码不存在'

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


def checkVerifyCodeByMobile1(sid, cmd, datas):
    '''校验手机验证码
            mobile
            verifyCode
        '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('mobile', datas):
        errorCode = -3
        errorMsg = '密码为空'
    elif not re.compile(r"^1[3456789]\d{9}$").match(datas['mobile']):
        errorCode = -4
        errorMsg = '手机号不符合规则'
    elif not CommonDag.hasKeyData('verifyCode', datas):
        errorCode = -5
        errorMsg = '验证码为空'
    else:
        rest = SessionHelper.Session().get(datas['mobile'] + "_sms")
        if rest:
            startTime = datetime.strptime(rest['sTime'], "%Y-%m-%d %H:%M:%S")
            endTime = datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "%Y-%m-%d %H:%M:%S")
            if (endTime - startTime).seconds > 300:
                errorCode = -1
                errorMsg = '验证码失效，重新获取'
            elif datas['verifyCode'] != rest['verifyCode']:
                errorCode = -2
                errorMsg = '验证码错误'
            else:
                errorCode = 0
                errorMsg = '验证ok'
        else:
            errorCode = -7
            errorMsg = '验证码不存在'

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


def resetPassword1(sid, cmd, datas):
    '''重置密码
    id 邮箱或者手机
    password 密码
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('password', datas):
        errorCode = -2
        errorMsg = '密码为空'
    elif not CommonDag.hasKeyData('id', datas):
        errorCode = -5
        errorMsg = '邮箱或手机为空'
    elif CommonDag.judgeStrIsNum('id', datas):
        datas['attr'] = 'mobile'
        if not re.compile(r"^1[3456789]\d{9}$").match(datas['id']):
            errorCode = -3
            errorMsg = '手机号不符合规则'
    else:
        # 邮箱登陆
        datas['attr'] = 'email'
        datas['id'] = datas['id'].lower()
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['id'], re.I):
            errorCode = -4
            errorMsg = '邮箱不符合规则'

    if not errorMsg:
        # 密码加密 sha256
        import hashlib
        datas['password'] = hashlib.sha256(datas['password'].encode()).hexdigest()
        res = DS.modifyPassword(datas)
        if not res:
            errorCode = -1
            errorMsg = '修改密码失败'
        else:
            errorCode = 0
            errorMsg = '修改密码ok'
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def modifyUserMobile(sid, cmd, datas):
    '''修改用户手机
        new_mobile
        verifyCode
        session_id
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('new_mobile', datas):
        errorCode = -2
        errorMsg = '手机为空'
    elif not re.compile(r"^1[3456789]\d{9}$").match(datas['new_mobile']):
        errorCode = -3
        errorMsg = '手机号不符合规则'
    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -5
        errorMsg = 'session_id为空'
    elif not CommonDag.hasKeyData('verifyCode', datas):
        errorCode = -6
        errorMsg = '验证码为空'
    else:
        datas['user_id'] = int(base64.b64decode(datas['session_id'].encode()).decode())
        datas['mobile'] = datas['new_mobile']
        if not DS.uniqueMobile(datas):
            errorCode = -4
            errorMsg = '电话已经注册'

    if not errorMsg:
        rest = SessionHelper.Session().get(datas['new_mobile'] + "_sms")
        if rest:
            startTime = datetime.strptime(rest['sTime'], "%Y-%m-%d %H:%M:%S")
            endTime = datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "%Y-%m-%d %H:%M:%S")
            if (endTime - startTime).seconds > 300:
                errorCode = -8
                errorMsg = '验证码失效，重新获取'
            elif datas['verifyCode'] != rest['verifyCode']:
                errorCode = -9
                errorMsg = '验证码错误'
            else:
                datas['attr'] = "mobile"
                datas['attrV'] = datas['new_mobile']
                con = DS.modifyMobileOrEmail(datas)
                if not con:
                    errorCode = -1
                    errorMsg = '更新失败'
                else:
                    errorCode = 0
                    errorMsg = '更新ok'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg,
                        "return": {
                            "mobile": datas['new_mobile']
                        }
                    }
        else:
            errorCode = -7
            errorMsg = '验证码不存在'


    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def modifyUserEmail(sid, cmd, datas):
    '''修改用户邮箱
        new_email
        verifyCode
        session_id
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('new_email', datas):
        errorCode = -2
        errorMsg = '邮箱为空'
    elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['new_email'], re.I):
        errorCode = -3
        errorMsg = '邮箱不符合规则'
    elif not CommonDag.hasKeyData('session_id', datas):
        errorCode = -5
        errorMsg = 'session_id为空'
    elif not CommonDag.hasKeyData('verifyCode', datas):
        errorCode = -6
        errorMsg = '验证码为空'
    else:
        datas['new_email'] = datas['new_email'].lower()
        datas['user_id'] = int(base64.b64decode(datas['session_id'].encode()).decode())
        datas['email'] = datas['new_email'].lower()
        if not DS.uniqueEmail(datas):
            errorCode = -4
            errorMsg = '邮箱已经注册'

    if not errorMsg:
        rest = SessionHelper.Session().get(datas['new_email'] + '_email')
        if rest:
            startTime = datetime.strptime(rest['vTime'], "%Y-%m-%d %H:%M:%S")
            endTime = datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "%Y-%m-%d %H:%M:%S")
            if (endTime - startTime).seconds > 300:
                errorCode = -7
                errorMsg = '验证码失效，重新获取'
            elif datas['verifyCode'] != rest['verifyCode']:
                errorCode = -9
                errorMsg = '验证码错误'
            else:
                datas['attr'] = "email"
                datas['attrV'] = datas['new_email']
                con = DS.modifyMobileOrEmail(datas)
                if not con:
                    errorCode = -1
                    errorMsg = '更新失败'
                else:
                    errorCode = 0
                    errorMsg = '更新ok'
                    return {
                        "errorCode": errorCode,
                        "errorMsg": errorMsg,
                        "return": {
                            "email": datas['new_email']
                        }
                    }
        else:
            errorCode = -8
            errorMsg = '验证码不存在'

    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


@CommonDag.login_required
def deleteTesting(sid, cmd, datas):
    '''删除正在测评的试卷
    id 问卷id
    session_id
    '''
    errorCode = -1
    errorMsg = ''
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
    else:
        # 回答者的id
        datas['user_id'] = int(base64.b64decode(datas['session_id'].encode()).decode())

    if not errorMsg:
        cc = DS.getTestingId(datas)
        if not cc:
            errorMsg = -7
            errorCode = '无评测信息'
        else:
            res = DS.deleteTestingMainInfo(datas)
            if not res:
                errorCode = -6
                errorMsg = '删除总评信息失败'
            else:
                datas['idx'] = cc['idx']
                con = DS.deleteTestingAnswerInfo(datas)
                errorCode = 0
                errorMsg = '删除ok'
                # if not con:
                #     # 未作答的删除时肯定没有信息。放过
                #     pass
                # else:
                #     errorCode = 0
                #     errorMsg = '删除ok'
    return {
        "errorMsg": errorMsg,
        "errorCode": errorCode
    }


def retry_send_active_link(sid, cmd, datas):
    """重新发送激活链接
        email
    """
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('email', datas):
        errorCode = -2
        errorMsg = '邮箱为空'
    elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['email'], re.I):
        errorCode = -3
        errorMsg = '邮箱不符合规则'
    elif DS.uniqueEmail(datas):
        errorCode = -4
        errorMsg = '邮箱未注册'

    if not errorMsg:
        datas['email'] = datas['email'].lower()
        email = base64.b64encode(datas['email'].encode()).decode()
        con = parse.urlencode({"mail": email})
        addr = config.link + con

        with open('servers/DAIG_SYS/emailTpl.html', 'r', encoding='utf-8') as f:
            config.html_body = f.read()

        # 设置邮件链接失效期
        SessionHelper.Session().set(datas['email'] + '_link', time.time())
        try:
            # 开辟线程发邮件
            th = Thread(target=CommonDag.send_mail(config.subject, datas['email'], config.html_body % (addr)))
            th.start()
            # CommonDag.send_mail(config.subject, datas['email'], config.html_body%(addr))
        except:
            errorCode = -1
            errorMsg = '邮件发送失败'
        else:
            errorCode = 0
            errorMsg = '邮件发送成功'
    return {
        'errorCode': errorCode,
        'errorMsg': errorMsg
    }


def remove_pre_register_user(sid, cmd, datas):
    """删除注册用户
        id:手机或者邮箱
    """
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('id', datas):
        errorCode = -2
        errorMsg = 'id为空'
    else:
        if CommonDag.judgeStrIsNum('id', datas):
            datas['mobile'] = datas['id']
            datas['attr'] = 'mobile'
            if not re.compile(r"^1[3456789]\d{9}$").match(datas['id']):
                errorCode = -3
                errorMsg = '手机号不符合规则'
            elif DS.uniqueMobile(datas):
                errorCode = -4
                errorMsg = '手机号未注册'
        else:
            datas['email'] = datas['id']
            datas['attr'] = 'email'
            if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['id'], re.I):
                errorCode = -5
                errorMsg = '邮箱不符合规则'
            elif DS.uniqueEmail(datas):
                errorCode = -6
                errorMsg = '邮箱未注册'
    if not errorMsg:
        datas['email'] = datas['email'].lower()
        con = DS.AccountIsActiveAndPassword(datas)
        if con['isActive']:
            errorCode = -7
            errorMsg = '账户已激活，不能删除'
        else:
            DS.deleteUser(datas)
            errorCode = 0
            errorMsg = 'ok'
    return {
        'errorCode': errorCode,
        'errorMsg': errorMsg
    }


def change_email_send_link(sid, cmd, datas):
    """换邮箱发送激活链接
        email
        mobile
        verifyCode
    """
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('email', datas):
        errorCode = -2
        errorMsg = '邮箱为空'
    elif not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', datas['email'], re.I):
        errorCode = -3
        errorMsg = '邮箱不符合规则'
    elif not CommonDag.hasKeyData('mobile', datas):
        errorCode = -5
        errorMsg = '手机为空'
    elif not re.compile(r"^1[3456789]\d{9}$").match(datas['mobile']):
        errorCode = -6
        errorMsg = '手机号不符合规则'
    elif not CommonDag.hasKeyData('verifyCode', datas):
        errorCode = -7
        errorMsg = '验证码为空'
    elif not DS.uniqueEmail(datas):
        errorCode = -8
        errorMsg = '邮箱已注册'
    elif DS.uniqueMobile(datas):
        errorCode = -4
        errorMsg = '电话未注册'
    else:
        # 取验证码和时间信息
        rest = SessionHelper.Session().get(datas['mobile'] + "_sms")
        if rest:
            if datas['verifyCode'] != rest['verifyCode']:
                errorCode = -9
                errorMsg = '验证码错误'
            else:
                startTime = datetime.strptime(rest['sTime'], "%Y-%m-%d %H:%M:%S")
                endTime = datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "%Y-%m-%d %H:%M:%S")
                if (endTime - startTime).seconds > 300:
                    errorCode = -10
                    errorMsg = '验证码失效，重新获取'
        else:
            errorCode = -12
            errorMsg = '验证码不存在'

    if not errorMsg:
        datas['email'] = datas['email'].lower()
        # 密码加密 sha256
        res = DS.changeUserEmail(datas)
        if res:
            email = base64.b64encode(datas['email'].encode()).decode()
            con = parse.urlencode({"mail": email})
            addr = config.link + con

            with open('servers/DAIG_SYS/emailTpl.html', 'r', encoding='utf-8') as f:
                config.html_body = f.read()

            # 设置邮件链接失效期
            SessionHelper.Session().set(datas['email'] + '_link', time.time())
            try:
                # 开辟线程发邮件
                th = Thread(target=CommonDag.send_mail(config.subject, datas['email'], config.html_body % (addr)))
                th.start()
                # CommonDag.send_mail(config.subject, datas['email'], config.html_body%(addr))
            except:
                errorCode = -11
                errorMsg = '邮件发送失败'
            else:
                errorCode = 0
                errorMsg = 'ok'
        else:
            errorCode = -1
            errorMsg = '更新失败信息失败'
    return {
        'errorCode': errorCode,
        'errorMsg': errorMsg
    }


# todo:工博会demo接口开发
def send_sms_demo(sid, cmd, datas):
    '''发送信息
        mobile
    '''
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('mobile', datas):
        errorCode = -2
        errorMsg = '手机号为空'
    elif not CommonDag.judgeStrIsNum('mobile', datas):
        errorCode = -3
        errorMsg = '手机号不是纯数字'
    elif not re.compile(r"^1[3456789]\d{9}$").match(datas['mobile']):
        errorCode = -4
        errorMsg = '手机号不符合规则'
    # elif not DS.unique_mobile(datas):
    #     errorCode = -5
    #     errorMsg = '电话已存在'

    if not errorMsg:
        verifyCode = "%4d" % (random.randint(1000, 9999))
        sTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        session_value = dict()
        session_value['verifyCode'] = verifyCode
        session_value['sTime'] = sTime
        # 将验证码和时间信息保存内存数据库
        SessionHelper.Session().set(datas['mobile']+"_sms", session_value)
        # print(type(SessionHelper.Session().get(datas['mobile']+"_sms")))
        # set_sms.set(key=datas['mobile']+'_sms', value=session_value)
        TEMPLATE_PARAM = '[' + verifyCode + ']'
        try:
            res = sms.main(datas['mobile'], TEMPLATE_PARAM, config.APP_KEY, config.APP_SECRET, config.sender,
                           config.url, config.TEMPLATE_ID, config.statusCallBack)

        except:
            errorCode = -6
            errorMsg = '发送验证码异常'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg,
            }
        else:
            res = json.loads(res)
            if res['description'] == 'Success' and res['code'] == '000000':
                errorCode = 0
                errorMsg = 'ok'
            else:
                errorCode = -1
                errorMsg = '发送短信验证码异常'
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


def register_user_demo(sid, cmd, datas):
    """添加用户
        name
        mobile
        ent_name
        verifyCode
    """
    errorCode = -1
    errorMsg = ''
    if not CommonDag.hasKeyData('mobile', datas):
        errorCode = -2
        errorMsg = '手机为空'
    elif not re.compile(r"^1[3456789]\d{9}$").match(datas['mobile']):
        errorCode = -3
        errorMsg = '手机号不符合规则'
    elif not CommonDag.hasKeyData('verifyCode', datas):
        errorCode = -4
        errorMsg = '验证码为空'
    # elif not DS.unique_mobile(datas):
    #     errorCode = -5
    #     errorMsg = '电话已注册'
    elif not CommonDag.hasKeyData('ent_name', datas):
        errorCode = -6
        errorMsg = '企业名称为空'
    elif not CommonDag.hasKeyData('name', datas):
        errorCode = -7
        errorMsg = '姓名为空'
    else:
        # 取验证码和时间信息
        rest = SessionHelper.Session().get(datas['mobile'] + "_sms")
        if rest:
            if datas['verifyCode'] != rest['verifyCode']:
                errorCode = -10
                errorMsg = '验证码错误'
            else:
                startTime = datetime.strptime(rest['sTime'], "%Y-%m-%d %H:%M:%S")
                endTime = datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "%Y-%m-%d %H:%M:%S")
                if (endTime - startTime).seconds > 300:
                    errorCode = -8
                    errorMsg = '验证码失效，重新获取'
        else:
            errorCode = -9
            errorMsg = '验证码不存在'

    if not errorMsg:
        res = DS.add_user_demo(datas)
        if not res:
            errorCode = -1
            errorMsg = '添加用户失败'
        errorCode=0
        errorMsg = 'ok'
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg
    }


def statistic_data_demo(sid, cmd, datas):
    """统计总分
        score
    """
    errorCode = -1
    errorMsg = ''
    pec = 0
    pecent_ent = 0
    if not CommonDag.hasKeyData('score', datas):
        errorCode = -2
        errorMsg = '分数为空'
    elif not CommonDag.judgeIntType('score', datas):
        errorCode = -3
        errorMsg = '分数不为整数'
    elif datas['score'] > 100:
        errorCode = -4
        errorMsg = '分数超上限'
    elif datas['score'] < 0:
        errorCode = -5
        errorMsg = '分数超下限'

    if not errorMsg:
        score_list = DS.get_score_demo(datas)
        count = len(score_list) + 1
        for rep in score_list:
            if datas['score'] >= rep:
                pec += 1
        pecent_ent += pec * 100 // count

        res = DS.add_score_demo(datas)
        if not res:
            errorCode = -1
            errorMsg = '添加分数失败'
            return {
                "errorCode": errorCode,
                "errorMsg": errorMsg
            }

        errorMsg = 'ok'
        errorCode = 0
    return {
        "errorCode": errorCode,
        "errorMsg": errorMsg,
        "return": pecent_ent
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
servers.append(IBUS.IFS_SERVER("getTestInfo", False, "public", "获取问卷信息", getTestInfo))
servers.append(IBUS.IFS_SERVER("getQuestion", False, "public", "获取问题", getQuestion))
servers.append(IBUS.IFS_SERVER("getTestId", False, "public", "模糊查询", getTestId))
servers.append(IBUS.IFS_SERVER("addAnswer", False, "public", "添加答案", addAnswer))
servers.append(IBUS.IFS_SERVER("getTotalScoreInfo", False, "public", "评分1", getTotalScoreInfo))
servers.append(IBUS.IFS_SERVER("getLevelInfo", False, "public", "分类评分", getLevelInfo))
servers.append(IBUS.IFS_SERVER("registerUser", False, "public", "注册用户", registerUser))
servers.append(IBUS.IFS_SERVER("activeAccount", False, "public", "激活账户", activeAccount))
servers.append(IBUS.IFS_SERVER("login", False, "public", "登录", login))
servers.append(IBUS.IFS_SERVER("sendSms", False, "public", "获取短信验证码", sendSms))
servers.append(IBUS.IFS_SERVER("check_login", False, "public", "检查登录状态", check_login))
servers.append(IBUS.IFS_SERVER("registerEnterpriseInfo", False, "public", "注册企业信息", registerEnterpriseInfo))
servers.append(IBUS.IFS_SERVER("getEnterpriseInfo", False, "public", "获取企业信息", getEnterpriseInfo))
servers.append(IBUS.IFS_SERVER("modifyEnterpriseInfo", False, "public", "修改企业信息", modifyEnterpriseInfo))
servers.append(IBUS.IFS_SERVER("uploadImage", False, "public", "上传图片", uploadImage))
servers.append(IBUS.IFS_SERVER("uploadImageBase64", False, "public", "上传图片base64", uploadImageBase64))
servers.append(IBUS.IFS_SERVER("resetPasswordByEmail", False, "public", "邮箱发验证码", resetPasswordByEmail))
servers.append(IBUS.IFS_SERVER("resetPasswordByEmail1", False, "public", "忘记密码，邮箱发验证码", resetPasswordByEmail1))
servers.append(IBUS.IFS_SERVER("checkVerifyCodeByEmail", False, "public", "邮箱校验验证码", checkVerifyCodeByEmail))
servers.append(IBUS.IFS_SERVER("checkVerifyCodeByEmail1", False, "public", "忘记密码，邮箱校验验证码", checkVerifyCodeByEmail1))
servers.append(IBUS.IFS_SERVER("checkVerifyCodeByMobile", False, "public", "手机校验验证码", checkVerifyCodeByMobile))
servers.append(IBUS.IFS_SERVER("checkVerifyCodeByMobile1", False, "public", "忘记密码，手机校验验证码", checkVerifyCodeByMobile1))
servers.append(IBUS.IFS_SERVER("resetPassword", False, "public", "重置密码", resetPassword))
servers.append(IBUS.IFS_SERVER("resetPassword1", False, "public", "忘记密码，重置密码", resetPassword1))
servers.append(IBUS.IFS_SERVER("getUserInformation", False, "public", "获取用户信息", getUserInformation))
servers.append(IBUS.IFS_SERVER("modifyUserInfo", False, "public", "修改用户信息", modifyUserInfo))
servers.append(IBUS.IFS_SERVER("modifyUserName", False, "public", "修改用户名", modifyUserName))
servers.append(IBUS.IFS_SERVER("logout", False, "public", "退出登录", logout))
servers.append(IBUS.IFS_SERVER("get_industry_type", False, "public", "获取行业信息", get_industry_type))
servers.append(IBUS.IFS_SERVER("getUserTestAllInfo", False, "public", "获取用户评测的问卷相关信息", getUserTestAllInfo))
servers.append(IBUS.IFS_SERVER("modifyUserMobile", False, "public", "修改用户手机", modifyUserMobile))
servers.append(IBUS.IFS_SERVER("modifyUserEmail", False, "public", "修改用户邮箱", modifyUserEmail))
servers.append(IBUS.IFS_SERVER("deleteTesting", False, "public", "删除正在作答试卷", deleteTesting))
servers.append(IBUS.IFS_SERVER("retry_send_active_link", False, "public", "从新发送激活链接", retry_send_active_link))
# servers.append(IBUS.IFS_SERVER("remove_pre_register_user", False, "public", "移除注册用户", remove_pre_register_user))
servers.append(IBUS.IFS_SERVER("change_email_send_link", False, "public", "换邮箱发送激活链接", change_email_send_link))
servers.append(IBUS.IFS_SERVER("report_datas_statistic", False, "public", "报告信息统计", report_datas_statistic))
servers.append(IBUS.IFS_SERVER("get_report_datas", False, "public", "获取报告", get_report_datas))
# todo:工博会demo
servers.append(IBUS.IFS_SERVER("send_sms_demo", False, "public", "发送demo短信信息", send_sms_demo))
servers.append(IBUS.IFS_SERVER("register_user_demo", False, "public", "添加demo用户信息", register_user_demo))
servers.append(IBUS.IFS_SERVER("statistic_data_demo", False, "public", "统计用户占比", statistic_data_demo))
IBUS.addServer("DAIG_SYS", servers)

# 事件
events = list()
events.append(IBUS.IF_ENENT(onEvent))
IBUS.addEvent(events)


