import json
from decimal import Decimal
from util import DBHelper


class DaigSys():
    '''诊断'''
    def searchQuestion(datas):
        '''查问题'''
        db = DBHelper.DB()
        result = db.fetchone(
            'select idx from _questionnaire_q_questions where question="{q}" and answer !="{c}" '.format(q=datas['question'], c=datas['cc']))
        return result

    def searchType(datas):
        '''查询分类'''
        db = DBHelper.DB()
        result = db.fetchone(
            'select idx from _questionnaire_q_question_test_type where level1="{l1}" and level2="{l2}" and '
            'level3="{l3}" and level4="{l4}" and level5="{l5}" and qid={id}'
                .format(l1=datas['level1'], l2=datas['level2'], l3=datas['level3'], l4=datas['level4'],
                        l5=datas['level5'], id=datas['qid']))
        return result

    def addQuestion(datas):
        '''添加问题'''
        db = DBHelper.DB()
        result = db.updateRowid('insert into _questionnaire_q_questions (question,answerType,answer,createTime,'
                                'createBy,status) values ("{q}", {ant}, "{ans}", now(), "{by}", {st})'
                                .format(q=datas['question'], ant=datas['answerType'], ans=datas['answer'],
                                        by=datas['createBy'], st=datas['status']))
        return result

    def addTypeQuestion(datas):
        '''添加问题分类'''
        db = DBHelper.DB()
        result = db.update(
            'insert into _questionnaire_q_question_test_type (level1,level2,level3,level4,level5,mark,qid,testId,createBy,'
            'createTime)values ("{l1}", "{l2}", "{l3}", "{l4}", "{l5}", "{mark}", {qid}, 4,"{by}", now())'
                .format(l1=datas['level1'], l2=datas['level2'], l3=datas['level3'], mark=datas['mark'],
                        qid=datas['qid'], by=datas['createBy'], l4=datas['level4'], l5=datas['level5']))
        return result

    def getTestAllInfo(datas):
        '''获取问卷信息'''
        db = DBHelper.DB()
        result = db.fetchall('select  id, remark, hot, `name`, industry from _questionnaire_q_test_attribute')
        lt = list()
        for temp in result:
            dic = dict()
            dic['name'] = temp['name']
            dic['id'] = temp['id']
            dic['description'] = temp['remark']
            dic['heat'] = temp['hot']
            dic['categories'] = temp['industry']
            lt.append(dic)
        return lt

    def getLevel1Type(datas):
        '''获取一级分类'''
        db = DBHelper.DB()
        if datas['id']:
            result = db.fetchall('select level1 from _questionnaire_q_question_test_type where testId={}'.format(datas['id']))
        else:
            result = db.fetchall('select distinct level1 from _questionnaire_q_question_test_type where testId != 0')

        lt = list()
        for temp in result:
            lt.append(temp['level1'])
        return lt

    def searchTestId(datas):
        '''查询问卷id'''
        db = DBHelper.DB()
        result = db.fetchone('select count(1) from _questionnaire_q_id_relation where testId={}'.format(datas['id']))
        if result['count(1)']:
            return True
        return False

    def getAnswerCount(datas):
        '''获取正在答问卷的数量'''
        db = DBHelper.DB()
        result = db.fetchone(
            'select count(1) from _questionnaire_q_review_main where answerUser={} and completeStatus=0'
                .format(datas['user_id']))
        return result['count(1)']

    def getQuestionsInfo(datas):
        '''获取问卷的所有问题'''
        db = DBHelper.DB()
        res = db.fetchone('select questionId from _questionnaire_q_id_relation where testId={}'.format(datas['id']))
        return res['questionId']

    def get_test_hot_info(datas):
        """获取问卷热度"""
        db = DBHelper.DB()
        result = db.fetchone(
            'select hot, quantity from _questionnaire_q_test_attribute where id={}'.format(datas['evaluationId']))
        return result

    def update_hot_info(datas):
        """更新问卷点击数"""
        db = DBHelper.DB()
        result = db.update('update _questionnaire_q_test_attribute set {}={} where id={}'
                           .format(datas['attr'], datas['attrV'], datas['evaluationId']))
        return result

    def searchTestStatus(datas):
        '''获取总答题的状态'''
        db = DBHelper.DB()
        res = db.fetchone('select idx from _questionnaire_q_review_main where testId={} and completeStatus=0 and '
                          'answerUser={}'.format(datas['id'], datas['user_id']))
        return res

    def addTotalScoreInfo(datas):
        '''添加总分信息'''
        db = DBHelper.DB()
        result = db.updateRowid('insert into _questionnaire_q_review_main(testId,startTime,completeStatus,answerUser) '
                                'values ({},now(),0,{})'.format(datas['id'], datas['user_id']))
        return result

    def getAnswerInfo(datas):
        '''获取选项信息详情'''
        db = DBHelper.DB()
        res = db.fetchall('select testId,questionId,expectData,answer from _questionnaire_q_answer_detail where id={}'
                          .format(datas['id']))
        return res

    def getQuestionInfo(datas):
        '''获取单个题目信息'''
        db = DBHelper.DB()
        res = db.fetchone(
            'select * from(select question,answerType,answer,level1,level2,level3,level4,level5,A.idx from '
            '_questionnaire_q_questions as A join _questionnaire_q_question_test_type as B on A.idx = B.qId and '
            'B.testId={})as C where C.idx={}'.format(datas['id'], datas['qId']))
        rt = dict()
        if res:
            res['answer'] = json.loads(res['answer'].replace("\'", "\""))
            rt['id'] = res['idx']
            rt['question'] = res['question']
            rt['answerType'] = res['answerType']
            rt['answerLists'] = res['answer']
            rt['level1'] = res['level1']
            rt['level2'] = res['level2']
            rt['level3'] = res['level3']
            rt['level4'] = res['level4']
            rt['level5'] = res['level5']
        return rt

    def getTestId(datas):
        '''获取问卷id'''
        db = DBHelper.DB()
        res = db.fetchall('select distinct C.id from (SELECT level1, A.id, A.`name`, A.remark, A.tag from '
                          '_questionnaire_q_test_attribute as A join _questionnaire_q_question_test_type as B WHERE '
                          'A.id=B.testId) as C where concat(C.`name`,C.remark) like "%{}%"'
                          .format(datas['keywords']))
        return res

    def get_enterprise_id(datas):
        """获取企业id"""
        db = DBHelper.DB()
        res = db.fetchone('select enterpriseId from _questionnaire_q_user_info where idx={}'.format(datas['user_id']))
        return res

    def addAnswerInfo(datas):
        '''添加答案信息'''
        db = DBHelper.DB()
        result = db.update(
            'insert into _questionnaire_q_answer_detail(testId,questionId,answer,answerUser,answerTime,id,expectData) '
            'values ({}, {}, {}, {},now(),{},{})'.format(datas['evaluationId'], datas['questionId'], datas['answer'],
                                                           datas['user_id'], datas['idx'], datas['expectData']))
        return result

    def searchAnswerInfo(datas):
        db = DBHelper.DB()
        res = db.fetchone('select count(*) from _questionnaire_q_answer_detail where id={} and questionId={} and '
                          'answerUser={}'.format(datas['idx'], datas['questionId'], datas['user_id']))
        if res['count(*)']:
            return True
        return False

    def deleteAnswerInfo(datas):
        '''删除答案'''
        db = DBHelper.DB()
        result = db.update('delete from _questionnaire_q_answer_detail where id={} and questionId={} and '
                          'answerUser={}'.format(datas['idx'], datas['questionId'], datas['user_id']))
        return result

    def uniqueIdx(datas):
        '''总评唯一性'''
        db = DBHelper.DB()
        res = db.fetchone(
            'select count(*) from _questionnaire_q_review_main where idx={} and completeStatus=0 '.format(datas['idx']))
        if res['count(*)']:
            return True
        return False

    def updateMainTestStatus(datas):
        '''更新主评表状态'''
        db = DBHelper.DB()
        result = db.update(
            'update _questionnaire_q_review_main set completeStatus={},score={},expectScore={},endTime=now() where '
            'idx={} and answerUser={}'.format(datas['status'], datas['score'], datas['expectScore'], datas['idx'],
                                              datas['user_id']))
        return result

    def totalScore(datas):
        '''统计总分'''
        db = DBHelper.DB()
        result = db.fetchone(
            'select sum(score) as total from(select A.questionId, A.testId, B.answerType, A.answer from '
            '_questionnaire_q_answer_detail as A join _questionnaire_q_questions as B where A.questionId=B.idx and '
            'A.id={} and A.answerUser={}) as C join _questionnaire_q_score_relation as D where '
            'C.answerType=D.answerType and C.answer=D.flag'.format(datas['idx'], datas['user_id']))
        return result

    def get_relation_power_and_level(datas):
        """获取权重与层级关系"""
        db = DBHelper.DB()
        result = db.fetchall(
            'select C.id as idx,powerL1,powerL2,powerL3,powerL4,powerL5,level1,level2,level3,level4,level5,qId,score,'
            'testId,F.id,expectScore from (SELECT id,powerL1,powerL2,powerL3,powerL4,powerL5,level1,level2,level3,'
            'level4,level5,qId,A.testId from _questionnaire_q_power_value as A join '
            '_questionnaire_q_question_test_type as B ON A.id=B.idx and A.testId={})as C JOIN (SELECT '
            'expectScore, score, id, R.questionId FROM ((SELECT score as expectScore, '
            'questionId  FROM _questionnaire_q_score_relation as D JOIN _questionnaire_q_answer_detail as E ON '
            'D.flag=E.expectData and id={})AS Z JOIN (SELECT score, id, questionId  FROM '
            '_questionnaire_q_score_relation as F JOIN _questionnaire_q_answer_detail as G ON F.flag=G.answer and '
            'id={})as R ON Z.questionId=R.questionId)) as F on C.qId=F.questionId'
                .format(datas['evaluationId'], datas['idx'], datas['idx']))
        lt = list()
        for temp in result:
            dic = dict()
            dic['idx'] = temp['idx']
            dic['powerL1'] = temp['powerL1']
            dic['powerL2'] = temp['powerL2']
            dic['powerL3'] = temp['powerL3']
            dic['powerL4'] = temp['powerL4']
            dic['powerL5'] = temp['powerL5']
            dic['level1'] = temp['level1']
            dic['level2'] = temp['level2']
            dic['level3'] = temp['level3']
            dic['level4'] = temp['level4']
            dic['level5'] = temp['level5']
            dic['qId'] = temp['qId']
            dic['testId'] = temp['testId']
            dic['score'] = temp['score']
            dic['expectScore'] = temp['expectScore']
            dic['id'] = temp['id']
            lt.append(dic)
        return lt

    def statistic_power_value(datas):
        """统计模块的总权值"""
        db = DBHelper.DB()
        if datas['level'] == 0:
            result = db.fetchall(
                'SELECT DISTINCT level1, (powerL1) as pw FROM _questionnaire_q_question_test_type as A JOIN '
                '_questionnaire_q_power_value as B on B.id=A.idx WHERE A.testId={}'.format(datas['evaluationId']))
            con = 0
            for temp in result:
                con += temp['pw']
            for temp in result:
                temp['pw'] = con
        elif datas['level'] == 1:
            result = db.fetchall(
                'SELECT DISTINCT level1, level2,(powerL1) as pw FROM _questionnaire_q_question_test_type as A JOIN '
                '_questionnaire_q_power_value as B on B.id=A.idx WHERE A.testId={}'.format(datas['evaluationId']))
            lt = set([rt['level1'] for rt in result])
            for rn in lt:
                con = 0
                for temp in result:
                    if temp['level1'] == rn:
                        con += temp['pw']
                for temp in result:
                    if temp['level1'] == rn:
                            temp['pw'] = con
        elif datas['level'] == 2:
            result = db.fetchall(
                'SELECT DISTINCT level1,level2,level3,(powerL2) as pw FROM _questionnaire_q_question_test_type as A '
                'JOIN _questionnaire_q_power_value as B on B.id=A.idx WHERE A.testId={}'.format(datas['evaluationId']))
            lt = set([rt['level1']+'_'+rt['level2'] for rt in result])
            for rn in lt:
                con = 0
                for temp in result:
                    rt = rn.split('_')
                    if temp['level1'] == rt[0] and temp['level2'] == rt[1]:
                        con += temp['pw']
                for temp in result:
                    if temp['level1'] == rt[0] and temp['level2'] == rt[1]:
                            temp['pw'] = con
        elif datas['level'] == 3:
            result = db.fetchall(
                'SELECT DISTINCT level1,level2,level3,level4,(powerL3) as pw FROM _questionnaire_q_question_test_type '
                'as A JOIN _questionnaire_q_power_value as B on B.id=A.idx WHERE A.testId={}'
                    .format(datas['evaluationId']))
            lt = set([rt['level1'] + '_' + rt['level2']+'_'+rt['level3'] for rt in result])
            for rn in lt:
                con = 0
                for temp in result:
                    rt = rn.split('_')
                    if temp['level1'] == rt[0] and temp['level2'] == rt[1] and temp['level3'] == rt[2]:
                        con += temp['pw']
                for temp in result:
                    if temp['level1'] == rt[0] and temp['level2'] == rt[1] and temp['level3'] == rt[2]:
                            temp['pw'] = con
        elif datas['level'] == 4:
            result = db.fetchall(
                'SELECT DISTINCT level1,level2,level3,level4,level5,(powerL4) as pw FROM '
                '_questionnaire_q_question_test_type as A JOIN _questionnaire_q_power_value as B on B.id=A.idx WHERE '
                'A.testId={}'.format(datas['evaluationId']))
            lt = set([rt['level1'] + '_' + rt['level2'] + '_' + rt['level3'] + '_' + rt['level4'] for rt in result])
            for rn in lt:
                con = 0
                for temp in result:
                    rt = rn.split('_')
                    if temp['level1'] == rt[0] and temp['level2'] == rt[1] and temp['level3'] == rt[2] and \
                            temp['level4'] == rt[3]:
                        con += temp['pw']
                for temp in result:
                    if temp['level1'] == rt[0] and temp['level2'] == rt[1] and temp['level3'] == rt[2] and \
                            temp['level4'] == rt[3]:
                            temp['pw'] = con
        return result

    def search_model_count_power(datas):
        """查询问卷的权重是否存在"""
        db = DBHelper.DB()
        if datas['level'] == 1:
            result = db.fetchone('select idx from _questionnaire_q_model_power_value where n1="{}" and '
                                 'testId={}'.format(datas['level1'], datas['id']))
        elif datas['level'] == 2:
            result = db.fetchone(
                'select idx from _questionnaire_q_model_power_value where n1="{}" and n2="{}" and testId={}'
                    .format(datas['level1'], datas['level2'], datas['id']))
        elif datas['level'] == 3:
            result = db.fetchone(
                'select idx from _questionnaire_q_model_power_value where n1="{}" and n2="{}" and n3="{}" '
                'and testId={}'
                    .format(datas['level1'], datas['level2'], datas['level3'],datas['id']))
        elif datas['level'] == 4:
            result = db.fetchone(
                'select idx from _questionnaire_q_model_power_value where n1="{}" and n2="{}" and n3="{}" '
                'and n4="{}" and testId={}'
                    .format(datas['level1'], datas['level2'], datas['level3'], datas['level4'], datas['id']))
        elif datas['level'] == 5:
            result = db.fetchone(
                'select idx from _questionnaire_q_model_power_value where n1="{}" and n2="{}" and n3="{}" '
                'and n4="{}" and n5="{}" and testId={}'
                    .format(datas['level1'], datas['level2'], datas['level3'], datas['level4'], datas['level5'],
                            datas['id']))
        # if not result or not result['idx']:
        #     return False
        # return True
        return result

    # def delete_model_count_power(datas):
    #     """删除模块权重"""
    #     db = DBHelper.DB()
    #     if datas['level'] == 1:
    #         result = db.update(
    #             'delete from _questionnaire_q_model_power_value where n1="{}" and `level`={} and testId={}'
    #                 .format(datas['level1'], datas['level'], datas['id']))
    #     elif datas['level'] == 2:
    #         result = db.update(
    #             'delete from _questionnaire_q_model_power_value where n1="{}" and n2="{}" and `level`={} and testId={}'
    #                 .format(datas['level1'], datas['level2'], datas['level'], datas['id']))
    #     elif datas['level'] == 3:
    #         result = db.update(
    #             'delete from _questionnaire_q_model_power_value where n1="{}" and n2="{}" and n3="{}" and `level`={} '
    #             'and testId={}'
    #                 .format(datas['level1'], datas['level2'], datas['level3'], datas['level'], datas['id']))
    #     elif datas['level'] == 4:
    #         result = db.update(
    #             'delete from _questionnaire_q_model_power_value where n1="{}" and n2="{}" and n3="{}" and n4="{}" and '
    #             '`level`={} and testId={}'
    #                 .format(datas['level1'], datas['level2'], datas['level3'], datas['level4'], datas['level'],
    #                         datas['id']))
    #     elif datas['level'] == 5:
    #         result = db.update(
    #             'delete from _questionnaire_q_model_power_value where n1="{}" and n2="{}" and n3="{}" and n4="{}" and '
    #             'n5="{}" and `level`={} and testId={}'
    #                 .format(datas['level1'], datas['level2'], datas['level3'], datas['level4'], datas['level5'],
    #                         datas['level'], datas['id']))
    #     return result

    def add_model_count_power(datas):
        """添加模块权重值"""
        db = DBHelper.DB()
        if datas['level'] == 1:
            result = db.updateRowid(
                'insert into _questionnaire_q_model_power_value(n1,`level`,testId, power,modifyTime) values("{}",{},{},'
                '{},now())'.format(datas['level1'], datas['level'], datas['id'], datas['pw']))
        elif datas['level'] == 2:
            result = db.updateRowid(
                'insert into _questionnaire_q_model_power_value(n1,n2,`level`,testId, power,modifyTime) values("{}",'
                '"{}",{},{},{},now())'
                    .format(datas['level1'], datas['level2'], datas['level'], datas['id'], datas['pw']))
        elif datas['level'] == 3:
            result = db.updateRowid(
                'insert into _questionnaire_q_model_power_value(n1,n2,n3,`level`,testId,power,modifyTime) values("{}",'
                '"{}","{}",{},{},{},now())'.format(datas['level1'], datas['level2'], datas['level3'], datas['level'],
                                                   datas['id'], datas['pw']))
        elif datas['level'] == 4:
            result = db.updateRowid(
                'insert into _questionnaire_q_model_power_value(n1,n2,n3,n4,`level`,testId,power,modifyTime) '
                'values("{}","{}","{}","{}",{},{},{},now())'
                    .format(datas['level1'], datas['level2'], datas['level3'], datas['level4'], datas['level'],
                            datas['id'],  datas['pw']))
        elif datas['level'] == 5:
            result = db.updateRowid(
                'insert into _questionnaire_q_model_power_value(n1,n2,n3,n4,n5,`level`,testId,power,modifyTime) '
                'values("{}","{}","{}","{}","{}",{},{},{},now())'
                    .format(datas['level1'], datas['level2'], datas['level3'], datas['level4'], datas['level5'],
                            datas['level'], datas['id'],  datas['pw']))
        return result

    def add_model_score_info(datas):
        """添加模块信息"""
        db = DBHelper.DB()
        result = db.update('insert into _questionnaire_q_model_score(id, entId, modifyTime) values({}, {}, now())'
                           .format(datas['pid'], datas['eid']))
        return result

    def update_model_score_flag(datas):
        """更新模块总分"""
        db = DBHelper.DB()
        result = db.update(
            'update _questionnaire_q_model_score set scoreFlag=0,modifyTime=now() where id={} and entId={}'
                .format(datas['pid'], datas['eid']))
        return result

    def search_model_score_info(datas):
        """查询是否存在"""
        db = DBHelper.DB()
        result = db.fetchone('select count(*) as nu from _questionnaire_q_model_score where  id={} and entId={}'
                             .format(datas['pid'], datas['eid']))
        if not result or not result['nu']:
            return False
        return True

    def get_model_power_count(datas):
        """获取模块的权重值值"""
        db = DBHelper.DB()
        if datas['type'] == 5:
            sql = 'testId={} and n1="{}" and n2="{}" and n3="{}" and n4="{}" and n5="{}"'.format(datas['testId'], datas['level1'], datas['level2'], datas['level3'],datas['level4'],datas['level5'])
        elif datas['type'] == 4:
            sql = 'testId={} and n1="{}" and n2="{}" and n3="{}" and n4="{}" and n5=""'.format(datas['testId'], datas['level1'], datas['level2'], datas['level3'], datas['level4'])
        elif datas['type'] == 3:
            sql = 'testId={} and n1="{}" and n2="{}" and n3="{}" and n4="" and n5=""'.format(datas['testId'], datas['level1'], datas['level2'], datas['level3'])
        elif datas['type'] == 2:
            sql = 'testId={} and n1="{}" and n2="{}" and n3="" and n4="" and n5=""'.format(datas['testId'], datas['level1'], datas['level2'])
        elif datas['type'] == 1:
            sql = 'testId={} and n1="{}" and n2="" and n3="" and n4="" and n5=""'.format(datas['testId'], datas['level1'])
        result = db.fetchone('select power, flag from _questionnaire_q_model_power_value where {} and 1=1'
                             .format(sql))
        return result

    def update_model_power_value(datas):
        """更新模块权重值"""
        db = DBHelper.DB()
        if datas['type'] == 5:
            sql = 'power={},modifyTime=now(),flag={} where testId={} and n1="{}" and n2="{}" and n3="{}" and n4="{}" ' \
                  'and n5="{}"'.format(datas['p'], datas['flag'], datas['testId'], datas['level1'], datas['level2'],
                                   datas['level3'], datas['level4'], datas['level5'])
        elif datas['type'] == 4:
            sql = 'power={},modifyTime=now(),flag={} where testId={} and n1="{}" and n2="{}" and n3="{}" and n4="{}" ' \
                  'and n5=""'.format(datas['p'], datas['flag'], datas['testId'], datas['level1'], datas['level2'],
                                 datas['level3'], datas['level4'])
        elif datas['type'] == 3:
            sql = 'power={},modifyTime=now(),flag={} where testId={} and n1="{}" and n2="{}" and n3="{}" and n4="" ' \
                  'and n5=""'.format(datas['p'], datas['flag'], datas['testId'], datas['level1'], datas['level2'],
                                 datas['level3'])
        elif datas['type'] == 2:
            sql = 'power={},modifyTime=now(),flag={} where testId={} and n1="{}" and n2="{}" and n3="" and n4="" ' \
                  'and n5=""'.format(datas['p'], datas['flag'], datas['testId'], datas['level1'], datas['level2'])
        elif datas['type'] == 1:
            sql = 'power={},modifyTime=now(),flag={} where testId={} and n1="{}" and n2="" and n3="" and n4="" ' \
                  'and n5=""'.format(datas['p'], datas['flag'], datas['testId'], datas['level1'])
        result = db.update('update _questionnaire_q_model_power_value set {}'.format(sql))
        if not result:
            return False
        return True

    def get_question_count(datas):
        """获取题数"""
        db = DBHelper.DB()
        result = db.fetchall('select * from _questionnaire_q_question_test_type where level1="{}" '
                             'and level2="{}" and level3="{}" and level4="{}" and level5="{}" and testId={}'
                             .format(datas['level1'], datas['level2'], datas['level3'], datas['level4'],
                                     datas['level5'], datas['testId']))
        return result

    def get_enterprise_info(datas):
        '''获取企业报告信息'''
        db = DBHelper.DB()
        result = db.fetchone('select A.idx,enterpriseName,logo,enterpriseCode,province,city,area,industryL1,'
                             'industryL2,industryL3,industryL4,industryL5,`scale`,income from '
                             '_questionnaire_q_enterprise_info as A join '
                             '_questionnaire_q_user_info as B where A.idx=B.enterpriseId and B.idx={}'
                             .format(datas['user_id']))
        return result

    def get_model_power(datas):
        """获取问卷的权重信息"""
        db = DBHelper.DB()
        # result = db.fetchall(
        #     'select * from _questionnaire_q_model_power_value where testId={}'
        #     .format(datas['evaluationId']))
        result = db.fetchall(
            'select n1,n2,n3,n4,n5,`level`,testId,power,flag,actModelScore,expModelScore, scoreFlag, entId '
            'from _questionnaire_q_model_power_value as A join _questionnaire_q_model_score as B on '
            'A.idx=B.id where A.testId={} and B.entId={}'.format(datas['evaluationId'], datas['eid']))
        return result

    def get_question_list(datas):
        """获取问题列表"""
        db = DBHelper.DB()
        result = db.fetchall(
            'select qId from _questionnaire_q_question_test_type where level1="{}" and level2="{}" and level3="{}" '
            'and level4="{}" and level5="{}" and testId={}'.format(datas['n1'], datas['n2'], datas['n3'], datas['n4'],
                                                                   datas['n5'], datas['testId']))
        lt = list()
        for temp in result:
            lt.append(temp['qId'])
        return lt

    def update_model_score(datas):
        """"更新模块总分"""
        db = DBHelper.DB()
        result = db.update(
            'update _questionnaire_q_model_score set actModelScore={},expModelScore={},scoreFlag=1, modifyTime=now() '
            'where entId={} and id=(select idx from _questionnaire_q_model_power_value where n1="{}" and n2="{}" and '
            'n3="{}" and n4="{}" and n5="{}" and testId={})'
                .format(datas['act_model_score'], datas['exp_model_score'], datas['entId'], datas['n1'], datas['n2'],
                        datas['n3'], datas['n4'], datas['n5'], datas['testId']))
        return result

    def get_model_score(datas):
        """获取模块分数"""
        db = DBHelper.DB()
        if datas['type'] == 4:
            sql = ' A.n1="{}" and A.n2="{}" and A.n3="{}" and A.n4 = "{}" and A.n5 != "" and A.level=5 and B.entId={}'\
                .format(datas['n1'], datas['n2'], datas['n3'], datas['n4'], datas['entId'])
        elif datas['type'] == 3:
            sql = 'A.n1="{}" and A.n2="{}" and A.n3="{}" and A.n4 !="" and A.level=4 and B.entId={}'\
                .format(datas['n1'], datas['n2'], datas['n3'], datas['entId'])
        elif datas['type'] == 2:
            sql = 'A.n1="{}" and A.n2="{}" and A.n3 != "" and A.level=3 and B.entId={}'\
                .format(datas['n1'], datas['n2'], datas['entId'])
        elif datas['type'] == 1:
            sql = 'A.n1= "{}" and A.n2 !="" and A.level=2 and B.entId={}'.format(datas['n1'], datas['entId'])
        result = db.fetchall(
            'select B.actModelScore, B.expModelScore, power from _questionnaire_q_model_power_value as A join '
            '_questionnaire_q_model_score as B on A.idx=B.id and A.testId={} where {}'.format(datas['testId'], sql))
        cat = dict()
        acs = 0
        exs = 0
        for rt in result:
            acs += Decimal(rt['actModelScore'] * rt['power'])
            exs += Decimal(rt['expModelScore'] * rt['power'])
        cat['acs'] = acs
        cat['exs'] = exs
        return cat

    def uniqueTestMain(datas):
        '''查询是否存在此卷'''
        db = DBHelper.DB()
        result = db.fetchone('select count(*) as num from _questionnaire_q_review_main where idx={} and testId={}'
                             .format(datas['idx'], datas['evaluationId']))

        if result['num']:
            return True
        return False

    def getTestScore(datas):
        '''获取测试分数'''
        db = DBHelper.DB()
        result = db.fetchone('select score, expectScore, endTime from _questionnaire_q_review_main where idx={} and '
                             'answerUser={}'.format(datas['idx'], datas['user_id']))
        return result

    def GetTotalScore(datas):
        '''获取总分信息'''
        db = DBHelper.DB()
        result = db.fetchone('select score from _questionnaire_q_score_relation where answerType={} and flag={}'
                             .format(datas['type'], datas['length']))
        return result

    def getLevelinfo(datas):
        '''获取不同层级的信息'''
        db = DBHelper.DB()
        if datas['level'] == 1:
            datas['name'] = 'level1'
        elif datas['level'] == 2:
            datas['name'] = 'level2'
        elif datas['level'] == 3:
            datas['name'] = 'level3'
        elif datas['level'] == 4:
            datas['name'] = 'level4'
        elif datas['level'] == 5:
            datas['name'] = 'level5'

        # result = db.fetchall(
        #     'select {}, sum(score)as sc, sum(expectData) as ed from(select level1,level2,level3,qId,testId,answerType,'
        #     'C.answer,C.expectData from(select expectData,answer,A.testId,id,qId,level1,level2,level3 from '
        #     '_questionnaire_q_answer_detail as A join _questionnaire_q_question_test_type as B where '
        #     'A.questionId=B.qId and A.id={}) as C join _questionnaire_q_questions as D where C.qId=D.idx)as E join  '
        #     '_questionnaire_q_score_relation as F where E.answerType=F.answerType and E.answer=F.flag and '
        #     'E.expectData=F.flag group by {}'.format(datas['name'], datas['idx'], datas['name']))

        result = db.fetchall(
            'select G.{}, sc, respect from (select {}, sum(score)as sc from (select level1,level2,level3,level4,level5,'
            'qId,testId,answerType,C.answer from(select answer,A.testId,id,qId,level1,level2,level3,level4,level5 from '
            '_questionnaire_q_answer_detail as A join _questionnaire_q_question_test_type as B where '
            'A.questionId=B.qId and A.id={} and A.answerUser={}) as C join _questionnaire_q_questions as D where '
            'C.qId=D.idx) as E join _questionnaire_q_score_relation as F where E.answerType=F.answerType and '
            'E.answer=F.flag GROUP BY {}) as G join (select {}, sum(score)as respect  from (select level1,level2,'
            'level3,level4,level5,qId,testId,answerType,W.expectData from(select expectData,U.testId,id,qId,level1,'
            'level2,level3,level4,level5 from _questionnaire_q_answer_detail as U join '
            '_questionnaire_q_question_test_type as V where U.questionId=V.qId and U.id={} and U.answerUser={}) as W '
            'join _questionnaire_q_questions as X where W.qId=X.idx) as Y join _questionnaire_q_score_relation as Z '
            'where Y.answerType=Z.answerType and Y.expectData=Z.flag GROUP BY {})as H where G.{} = H.{}'
                .format(datas['name'], datas['name'], datas['idx'], datas['user_id'], datas['name'], datas['name'],
                        datas['idx'], datas['user_id'], datas['name'], datas['name'], datas['name']))

        lt = []
        for temp in result:
            dit = dict()
            dit['lev'] = temp[datas['name']]
            dit['score'] = int(temp['sc'])
            dit['expectScore'] = int(temp['respect'])
            lt.append(dit)
        return lt

    def get_report_info_compare(datas):
        """获取各层级信息"""
        db = DBHelper.DB()
        if datas['val'] == 1:
            sql = 'testId={} and flag=1 and entpId !={}'.format(datas['evaluationId'], datas['id'])
        elif datas['val'] == 2:
            sql = 'testId={} and flag=1 and entpId !={} and industry="{}"'\
                .format(datas['evaluationId'], datas['id'], datas['industry'])
        elif datas['val'] == 3:
            sql = 'testId={} and flag=1 and entpId !={} and province="{}"'\
                .format(datas['evaluationId'], datas['id'], datas['province'])
        elif datas['val'] == 4:
            sql = 'testId={} and flag=1 and entpId !={} and province="{}" and city="{}"'\
                .format(datas['evaluationId'], datas['id'], datas['province'], datas['city'])
        elif datas['val'] == 5:
            sql = 'testId={} and flag=1 and entpId !={} and province="{}" and city="{}" and area="{}"'\
                .format(datas['evaluationId'], datas['id'], datas['province'], datas['city'], datas['area'])
        result = db.fetchall(
            'select idx, entpId, expectScore, activeScore, actL1, expL1 from _questionnaire_q_report_datas where {}'
                .format(sql))
        for temp in result:
            temp['actL1'] = json.loads(temp['actL1'].replace("\'", "\""))
            temp['expL1'] = json.loads(temp['expL1'].replace("\'", "\""))
        return result

    def get_report_compare_data(datas):
        """获取同行业、地区数据"""
        db = DBHelper.DB()
        if datas['val'] == 1:
            sql = 'testId={} and flag=1 and entpId !={} and industry="{}" and idx < {}'\
                .format(datas['evaluationId'], datas['enterprise_id'], datas['industry'], datas['idx'])
        elif datas['val'] == 2:
            sql = 'testId={} and flag=1 and entpId !={} and province="{}" and idx < {}'\
                .format(datas['evaluationId'], datas['enterprise_id'], datas['province'], datas['idx'])
        elif datas['val'] == 3:
            sql = 'testId={} and flag=1 and entpId !={} and province="{}" and city="{}" and idx < {}'\
                .format(datas['evaluationId'], datas['enterprise_id'], datas['province'], datas['city'], datas['idx'])
        elif datas['val'] == 4:
            sql = 'testId={} and flag=1 and entpId !={} and province="{}" and city="{}" and area="{}" and idx < {}'\
                .format(datas['evaluationId'], datas['enterprise_id'], datas['province'], datas['city'], datas['area'], datas['idx'])
        result = db.fetchall('select l11L2,l12L2 from _questionnaire_q_report_datas where {}'.format(sql))
        lt = list()
        for temp in result:
            dic = dict()
            dic['l11L2'] = json.loads(temp['l11L2'].replace("\'", "\""))
            dic['l12L2'] = json.loads(temp['l12L2'].replace("\'", "\""))
            lt.append(dic)
        return lt

    def get_test_name(datas):
        """获取问卷名称"""
        db = DBHelper.DB()
        result = db.fetchone(
            'select `name` from _questionnaire_q_test_attribute where id={}'.format(datas['evaluationId']))
        return result

    def update_report_flag(datas):
        """更新企业报告数据标记"""
        db = DBHelper.DB()
        result = db.update('update _questionnaire_q_report_datas set flag=0 where flag=1 and entpId={} and testId={}'
                           .format(datas['entpId'], datas['evaluationId']))
        return result

    def add_report_datas(datas):
        """添加报告信息"""
        db = DBHelper.DB()
        result = db.updateRowid(
            'insert into _questionnaire_q_report_datas(testId,entpId,expectScore,activeScore,actL1,expL1,allLv,l11,l12,'
            'l11L2,l12L2,l11IndPec,l11ProvincePec,l11CityPec,l11AreaPec,l12IndPec,l12ProvincePec,l12CityPec,l12AreaPec,'
            'l11L3,l12L3,industry,province,city,area,income,`scale`,`name`,flag,createTime,id,testName) values ({},{},'
            '{},{},"{}","{}","{}","{}","{}","{}","{}",{},{},{},{},{},{},{},{},"{}","{}","{}","{}","{}","{}","{}","{}",'
            '"{}",1,now(),{},"{}")'
                .format(datas['evaluationId'], datas['entpId'], datas['expectScore'], datas['activeScore'],
                        datas['actL1'], datas['expL1'], datas['allLv'], datas['l11'], datas['l12'], datas['l11L2'],
                        datas['l12L2'], datas['l11IndPec'], datas['l11ProvincePec'], datas['l11CityPec'],
                        datas['l11AreaPec'], datas['l12IndPec'], datas['l12ProvincePec'], datas['l12CityPec'],
                        datas['l12AreaPec'], datas['l11L3'], datas['l12L3'], datas['industry'], datas['province'],
                        datas['city'], datas['area'], datas['income'], datas['scale'], datas['name'], datas['idx'],
                        datas['test_name']))
        return result

    def check_enterprise_id(datas):
        '''获取企业id是否存在'''
        db = DBHelper.DB()
        result = db.fetchone('select count(*) as nu from _questionnaire_q_enterprise_info where idx={}'
                             .format(datas['enterprise_id']))
        if not result['nu']:
            return False
        return True

    def check_review_main_id(datas):
        '''查询是否存在主表id'''
        db = DBHelper.DB()
        result = db.fetchone('select count(*) as num from _questionnaire_q_review_main where idx={}'
                             .format(datas['id']))

        if not result['num']:
            return False
        return True

    def get_report_else_info(datas):
        """获取其他企业的数据"""
        db = DBHelper.DB()
        result = db.fetchall('select actL1 from _questionnaire_q_report_datas where entpId !={} and flag=1 and '
                             'testId={} and idx < {}'
                             .format(datas['enterprise_id'], datas['evaluationId'], datas['idx']))

        lt = list()
        cz = list()
        if result:
            rc = json.loads(result[0]['actL1'].replace("\'", "\""))
            for v in rc.keys():
                cz.append(v)
        lt.append(cz)
        for temp in result:
            dic = list()
            rt = json.loads(temp['actL1'].replace("\'", "\""))
            dic.append(rt[cz[0]])
            dic.append(rt[cz[1]])
            # dic["expL1"] = json.loads(temp['expL1'].replace("\'", "\""))
            lt.append(dic)
        return lt

    def get_report_all_info(datas):
        """获取报告信息"""
        db = DBHelper.DB()
        temp = db.fetchone('select * from _questionnaire_q_report_datas where entpId={} and id={}'
                             .format(datas['enterprise_id'], datas['id']))
        if temp:
            temp['actL1'] = json.loads(temp['actL1'].replace("\'", "\""))
            temp['expL1'] = json.loads(temp['expL1'].replace("\'", "\""))
            temp['allLv'] = json.loads(temp['allLv'].replace("\'", "\""))
            temp['l11'] = json.loads(temp['l11'].replace("\'", "\""))
            temp['l12'] = json.loads(temp['l12'].replace("\'", "\""))
            temp['l11L2'] = json.loads(temp['l11L2'].replace("\'", "\""))
            temp['l12L2'] = json.loads(temp['l12L2'].replace("\'", "\""))
            temp['l11L3'] = json.loads(temp['l11L3'].replace("\'", "\""))
            temp['l12L3'] = json.loads(temp['l12L3'].replace("\'", "\""))
            temp['expectScore'] = float(temp['expectScore'])
            temp['activeScore'] = float(temp['activeScore'])
            temp['l11IndPec'] = float(temp['l11IndPec'])
            temp['l12IndPec'] = float(temp['l12IndPec'])
            temp['l11ProvincePec'] = float(temp['l11ProvincePec'])
            temp['l11CityPec'] = float(temp['l11CityPec'])
            temp['l11AreaPec'] = float(temp['l11AreaPec'])
            temp['l12ProvincePec'] = float(temp['l12ProvincePec'])
            temp['l12CityPec'] = float(temp['l12CityPec'])
            temp['l12AreaPec'] = float(temp['l12AreaPec'])
            temp['l12CityPec'] = float(temp['l12CityPec'])
        return temp

    def addUser(datas):
        '''添加注册用户'''
        db = DBHelper.DB()
        result = db.update(
            # 'insert into _questionnaire_q_user_info(email,password,mobile,roleId,createTime) values ("{}", '
            # '"{}", "{}", {}, now())'
            #     .format(datas['email'].lower(), datas['password'], datas['mobile'], datas['roleId']))
            # 添加用户协议
            'insert into _questionnaire_q_user_info(email,password,mobile,roleId,createTime,protocol) values ("{}", '
            '"{}", "{}", {}, now(), {})'
                .format(datas['email'].lower(), datas['password'], datas['mobile'], datas['roleId'], datas['protocol']))
        return result

    def uniqueEmail(datas):
        '''邮箱唯一性'''
        db = DBHelper.DB()
        result = db.fetchone('select count(*) from _questionnaire_q_user_info where email="{}"'
                             .format(datas['email'].lower()))
        if result['count(*)']:
            return False
        return True

    def uniqueMobile(datas):
        '''电话唯一性'''
        db = DBHelper.DB()
        result = db.fetchone('select count(*) from _questionnaire_q_user_info where mobile="{}"'
                             .format(datas['mobile']))
        if result['count(*)']:
            return False
        return True

    def getUserAddTime(datas):
        '''获取用户注册时间'''
        db = DBHelper.DB()
        result = db.fetchone('select createTime from _questionnaire_q_user_info where email="{}"'
                             .format(datas['email'].lower()))
        return result

    def AccountIsActiveAndPassword(datas):
        '''账户是否激活和密码'''
        db = DBHelper.DB()
        result = db.fetchone(
            'select idx, isActive, password, enterpriseId, mobile, email, image from _questionnaire_q_user_info where '
            '{}="{}"'.format(datas['attr'], datas['id']))
        return result

    def AccountIsActive(datas):
        '''账户是否激活'''
        db = DBHelper.DB()
        result = db.fetchone(
            'select isActive from _questionnaire_q_user_info where {}="{}"'.format(datas['attr'], datas['id']))
        if result['isActive']:
            return True
        return False

    def updateOnlineStatus(datas):
        '''更新登录状态'''
        db = DBHelper.DB()
        result = db.update('update _questionnaire_q_user_info set `online`={},sessionTime=now() where {}="{}"'
                             .format(datas['online'], datas['attr'], datas['id']))
        return result

    def updateAccountActive(datas):
        '''激活账户'''
        db = DBHelper.DB()
        result = db.update('update _questionnaire_q_user_info set isActive=1 where email="{}"'
                           .format(datas['email']))
        return result

    def checkUserLoginStatus(datas):
        '''检查登陆状态'''
        db = DBHelper.DB()
        result = db.fetchone('select idx, `online`, sessionTime, email from _questionnaire_q_user_info where idx={}'
                           .format(datas['id']))
        return result

    def getEnterpriseInfo(datas):
        '''获取企业信息'''
        db = DBHelper.DB()
        result = db.fetchone('select A.idx,enterpriseName,shortName,logo,enterpriseCode,province,city,area,industryL1,'
                             'industryL2,industryL3,industryL4,industryL5,`scale`,income from '
                             '_questionnaire_q_enterprise_info as A join '
                             '_questionnaire_q_user_info as B where A.idx=B.enterpriseId and B.email="{}"'
                             .format(datas['email']))
        return result

    def modifyEnterpriseInfo(datas):
        '''修改企业信息'''
        db = DBHelper.DB()
        result = db.update(
            'update _questionnaire_q_enterprise_info set enterpriseName="{}",shortName="{}",modifyTime=now(),'
            'enterpriseCode="{}",province="{}",city="{}",area="{}",industryL1="{}",industryL2="{}",industryL3="{}",'
            '`scale`="{}",income="{}" where idx=(select enterpriseId from _questionnaire_q_user_info where email="{}")'
                .format(datas['enterpriseName'], datas['shortName'], datas['enterpriseCode'],
                        datas['province'], datas['city'], datas['area'], datas['industryL1'], datas['industryL2'],
                        datas['industryL3'], datas['scale'], datas['income'], datas['email']))
        return result

    def addEnterpriseInfo(datas):
        '''注册企业信息'''
        db = DBHelper.DB()
        result = db.updateRowid(
            'insert into _questionnaire_q_enterprise_info(enterpriseName,shortName,enterpriseCode,province,city,'
            'area,industryL1,industryL2,industryL3,industryL4,industryL5,`scale`,income,createTime,flag) values ("{}", '
            '"{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}",now(),"{}")'
                .format(datas['enterpriseName'], datas['shortName'], datas['enterpriseCode'],
                        datas['province'], datas['city'], datas['area'], datas['industryL1'], datas['industryL2'],
                        datas['industryL3'], datas['industryL4'], datas['industryL5'], datas['scale'], datas['income'],
                        datas['flag']))
        return result

    def updateUserEnterpriseId(datas):
        '''更新用户信息中的企业id'''
        db = DBHelper.DB()
        result = db.update('update _questionnaire_q_user_info set enterpriseId={} where email="{}"'
                           .format(datas['id'], datas['email']))
        return result

    def modifyPassword(datas):
        '''修改密码'''
        db = DBHelper.DB()
        result = db.update('update _questionnaire_q_user_info set password="{}",modifyTime=now() where {}="{}"'
                           .format(datas['password'], datas['attr'], datas['id']))
        return result

    def clearSessionTime(datas):
        """清理sessionTime"""
        db = DBHelper.DB()
        result = db.update('update _questionnaire_q_user_info set sessionTime=NULL,modifyTime=now() where {}="{}"'
                           .format(datas['attr'], datas['id']))
        return result

    def getUserInfo(datas):
        '''获取用户信息'''
        db = DBHelper.DB()
        result = db.fetchone('select `name`,image,email,mobile,department,`position`,birthday,gender,shortName '
                             'from _questionnaire_q_enterprise_info as A join '
                             '_questionnaire_q_user_info as B where A.idx=B.enterpriseId and B.email="{}"'
                             .format(datas['email']))
        return result

    def updateUserInfo(datas):
        '''修改用户信息'''
        db = DBHelper.DB()
        result = db.update(
            'update _questionnaire_q_user_info set department="{}",`position`="{}",birthday="{}",gender={},'
            'modifyTime=now() where email="{}"'.format(datas['department'], datas['position'], datas['birthday'],
                                                       datas['gender'], datas['email']))
        return result

    def modifyName(datas):
        '''修改用户名'''
        db = DBHelper.DB()
        result = db.update(
            'update _questionnaire_q_user_info set `name`="{}",modifyTime=now() where email="{}"'
                .format(datas['name'], datas['email']))
        return result

    def update_logo_Info(datas):
        '''更新企业图片信息'''
        db = DBHelper.DB()
        result = db.update(
            'update _questionnaire_q_enterprise_info set logo="{}",modifyTime=now() where idx={}'
                .format(datas['logo'], datas['id']))
        return result

    def updateImageInfo(datas):
        '''更新用户图片信息'''
        db = DBHelper.DB()
        result = db.update(
            'update _questionnaire_q_user_info set `image`="{}",modifyTime=now() where email="{}"'
                .format(datas['image'], datas['email']))
        return result

    def logout(datas):
        '''退出登录'''
        db = DBHelper.DB()
        result = db.update(
            'update _questionnaire_q_user_info set `online`=0,modifyTime=now() where email="{}"'
                .format(datas['email']))
        return result

    def getIndustryInfo(datas):
        '''获取行业信息'''
        db = DBHelper.DB()
        if not datas['value']:

            result = db.fetchall('select aid, title from _questionnaire_q_industry_type where pid is null')
        else:
            result = db.fetchall(
                'select B.aid, B.title as title from _questionnaire_q_industry_type as A join _questionnaire_q_industry_type '
                'as B on A.aid=B.pid where A.title="{}"'.format(datas['value']))

        lt = list()
        for temp in result:
            dic = dict()
            dic['id'] = temp['aid']
            dic['title'] = temp['title']
            dic['lable'] = temp['title']
            lt.append(dic)
        return lt

    def getUserAllInfo(datas):
        '''获取用户答题问卷信息'''
        db = DBHelper.DB()
        sql = ''
        if not datas['key'] and not datas['status']:
            sql = ' 1=1 '
        elif datas['status'] and not datas['key']:
            if datas['status'] == 3:
                sql += ' 1=1 '
            elif datas['status'] == 2:
                sql += ' completeStatus=0'
            else:
                sql += ' completeStatus=1'
        else:
            if datas['status'] == 3:
                sql += ''
            elif datas['status'] == 2:
                sql += ' completeStatus=0 and'
            else:
                sql += ' completeStatus=1 and'
            sql += ' concat(`name`, remark) like "%{}%"'.format(datas['key'])
        sql += ' order by startTime desc'
        result = db.fetchall(
            'select idx, id, `name`, startTime, endTime, completeStatus, remark from _questionnaire_q_review_main as A '
            'join _questionnaire_q_test_attribute as B on A.testId=B.id where A.answerUser={} and {}'
                .format(datas['user_id'], sql))
        lt = list()
        for temp in result:
            dic = dict()
            dic['idx'] = temp['idx']
            dic['id'] = temp['id']
            dic['name'] = temp['name']
            dic['startTime'] = temp['startTime']
            dic['endTime'] = temp['endTime']
            dic['completeStatus'] = temp['completeStatus']
            dic['remark'] = temp['remark']
            lt.append(dic)
        return lt

    def getQuestionedCount(datas):
        '''获取已经做答得问题个数'''
        db = DBHelper.DB()
        result = db.fetchone('select count(*) from _questionnaire_q_answer_detail where id={}'.format(datas['idx']))
        if result['count(*)']:
            return result['count(*)']
        return 0

    def getUserCenterInfo(datas):
        '''获取用户信息'''
        db = DBHelper.DB()
        result = db.fetchone('select `name`,image,email,mobile,department,`position`,enterpriseName,logo, enterpriseId '
                             'from _questionnaire_q_enterprise_info as A join '
                             '_questionnaire_q_user_info as B where A.idx=B.enterpriseId and B.idx={}'
                             .format(datas['user_id']))
        return result

    def modifyMobileOrEmail(datas):
        '''修改用户手机或者邮箱'''
        db = DBHelper.DB()
        result = db.update('update _questionnaire_q_user_info set {attr}="{attrV}",modifyTime=now() where idx={id}'
                             .format(attr=datas['attr'], attrV=datas['attrV'], id=datas['user_id']))
        return result

    def getTestingId(datas):
        """获取主评id"""
        db = DBHelper.DB()
        result = db.fetchone(
            'select idx from _questionnaire_q_review_main where testId={} and answerUser={} and completeStatus=0'
                .format(datas['id'], datas['user_id']))
        return result

    def deleteTestingMainInfo(datas):
        '''删除正在测评的问卷相关信息'''
        db = DBHelper.DB()
        result = db.update(
            'delete from _questionnaire_q_review_main where testId={} and answerUser={} and completeStatus=0'
                .format(datas['id'],  datas['user_id']))
        return result

    def deleteTestingAnswerInfo(datas):
        '''删除相关的答案'''
        db = DBHelper.DB()
        result = db.update('delete from _questionnaire_q_answer_detail where id={} and answerUser={}'
                           .format(datas['idx'], datas['user_id']))
        return result

    def deleteUser(datas):
        '''删除用户'''
        db = DBHelper.DB()
        result = db.update('delete from _questionnaire_q_user_info where {attr}="{id}"'
                           .format(attr=datas['attr'], id=datas['id']))
        return result

    def changeUserEmail(datas):
        """更换账户邮箱"""
        db = DBHelper.DB()
        result = db.update(
            'update _questionnaire_q_user_info set email="{}",modifyTime=now() where mobile="{}"'
                .format(datas['email'],datas['mobile']))
        return result

    # todo:工博会demo接口函数
    def unique_mobile(datas):
        '''电话唯一性'''
        db = DBHelper.DB()
        result = db.fetchone('select count(*) from _questionnaire_q_user_demo where mobile="{}"'
                             .format(datas['mobile']))
        if result['count(*)']:
            return False
        return True

    def add_user_demo(datas):
        """添加用户信息"""
        db = DBHelper.DB()
        result = db.update(
            'insert into _questionnaire_q_user_demo(`name`, mobile, entName, createTime) values("{}","{}","{}",now())'
                .format(datas['name'], datas['mobile'], datas['ent_name']))
        return result

    def get_score_demo(datas):
        """获取总分列表"""
        db = DBHelper.DB()
        result = db.fetchall('select score from _questionnaire_q_score_demo')
        lt = list()
        for temp in result:
            lt.append(temp['score'])
        return lt

    def add_score_demo(datas):
        """添加分数"""
        db = DBHelper.DB()
        result = db.update(
            'insert into _questionnaire_q_score_demo(score) values({})'.format(datas['score']))
        return result