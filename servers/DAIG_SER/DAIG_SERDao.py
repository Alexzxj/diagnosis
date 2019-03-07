import json

from util import DBHelper


class DaigSys():
    def uniqueAdmin(datas):
        '''用户唯一性'''
        db = DBHelper.DB()
        result = db.fetchone(
            'select count(*) from _questionnaire_q_admin_user where adminName="{}"'.format(datas['user']))
        if result['count(*)']:
            return False
        return True

    def checkAdminLogin(datas):
        """管理员登录查询"""
        db = DBHelper.DB()
        result = db.fetchone(
            'select idx, adminName, adminPwd, rid, mobile, email, remark from _questionnaire_q_admin_user where '
            'adminName="{}"'.format(datas['user']))
        return result

    def updateAdminOnlineStatus(datas):
        '''更新管理员的登录状态'''
        db = DBHelper.DB()
        result = db.update('update _questionnaire_q_admin_user set `online`={},sessionTime=now() where adminName="{}"'
                             .format(datas['online'], datas['user']))
        return result

    def checkAdminLoginStatus(datas):
        """管理员登录查询"""
        db = DBHelper.DB()
        result = db.fetchone(
            'select idx, adminName, rid, mobile, email, online, sessionTime from '
            '_questionnaire_q_admin_user where idx={}'.format(datas['id']))
        return result

    def getAllEnterprise(datas):
        """获取所有企业的数和行业数和参评企业数"""
        db = DBHelper.DB()
        result = db.fetchall(
            'select B.idx, enterpriseName,industryL1,industryL2,industryL3,industryL4,industryL5 from '
            '_questionnaire_q_enterprise_info as A join _questionnaire_q_user_info as B where A.idx=B.enterpriseId ')
        return result

    def statisticTestingCount(datas):
        """获取答题企业数量"""
        db = DBHelper.DB()
        result = db.fetchone(
            'select count(*) as test from _questionnaire_q_review_main where answerUser={}'.format(datas['id']))
        return result['test']

    def getAllEnterpriseInfo(datas):
        """获取对应的企业信息"""
        db = DBHelper.DB()
        sql = '1=1 '
        if datas['province']:
            sql += ' and province="{}"'.format(datas['province'])
        if datas['city']:
            sql += ' and city="{}"'.format(datas['city'])
        if datas['area']:
            sql += ' and area="{}"'.format(datas['area'])
        if datas['industryL1']:
            sql += ' and industryL1="{}"'.format(datas['industryL1'])
        if datas['industryL2']:
            sql += ' and industryL2="{}"'.format(datas['industryL2'])
        if datas['industryL3']:
            sql += ' and industryL3="{}"'.format(datas['industryL3'])
        if datas['industryL4']:
            sql += ' and industryL4="{}"'.format(datas['industryL4'])
        if datas['industryL5']:
            sql += ' and industryL5="{}"'.format(datas['industryL5'])
        if datas['income']:
            sql += ' and income="{}"'.format(datas['income'])
        if datas['scale']:
            sql += ' and scale="{}"'.format(datas['scale'])
        if datas['test_st_time']:
            sql += ' and D.st >= "{}"'.format(datas['test_st_time'])
        if datas['test_en_time']:
            sql += ' and D.st <= "{}"'.format(datas['test_en_time'] + ' 23:59:59')
        if datas['res_st_time']:
            sql += ' and A.createTime >= "{}"'.format(datas['res_st_time'])
        if datas['res_en_time']:
            sql += ' and A.createTime <= "{}"'.format(datas['res_en_time'] + ' 23:59:59')
        if datas['key']:
            sql += ' and concat(enterpriseName, shortName, enterpriseCode) like "%{}%"'.format(datas['key'])
        # 获取所有管理员用户对应的企业
        result = db.fetchall(
            'select distinct A.idx,enterpriseName,shortName,logo,enterpriseCode,province,city,area,industryL1, income, '
            'industryL2,industryL3,industryL4,industryL5,flag,A.createTime as ent_time, A.remark, B.idx as user_id, '
            'B.name,B.email,`scale` from _questionnaire_q_enterprise_info as A JOIN _questionnaire_q_user_info as B on '
            'A.idx=B.enterpriseId left JOIN (select answerUser, MAX(startTime) as st from _questionnaire_q_review_main '
            'GROUP BY answerUser) as D on B.idx=D.answerUser where B.roleId=1 and {}'.format(sql))
        lt = list()
        for temp in result:
            dic = dict()
            dic['idx'] = temp['idx']
            dic['enterpriseName'] = temp['enterpriseName']
            dic['shortName'] = temp['shortName']
            dic['logo'] = temp['logo']
            dic['enterpriseCode'] = temp['enterpriseCode']
            dic['province'] = temp['province']
            dic['city'] = temp['city']
            dic['area'] = temp['area']
            dic['industryL1'] = temp['industryL1']
            dic['industryL2'] = temp['industryL2']
            dic['industryL3'] = temp['industryL3']
            dic['industryL4'] = temp['industryL4']
            dic['industryL5'] = temp['industryL5']
            dic['flag'] = json.loads(temp['flag'])
            dic['ent_register_time'] = temp['ent_time']
            dic['user_id'] = temp['user_id']
            dic['user'] = temp['name']
            dic['email'] = temp['email']
            # dic['startTime'] = temp['startTime']
            dic['remark'] = temp['remark']
            dic['income'] = temp['income']
            dic['scale'] = temp['scale']
            lt.append(dic)
        return lt

    def get_enterprise_flag(datas):
        """获取企业标签"""
        db = DBHelper.DB()
        if len(datas['id']) > 1:
            result = db.fetchall('select idx, flagName from _questionnaire_q_flag_info where relation={} and idx in {}'
                                 .format(datas['type'], tuple(datas['id'])))
            if not result:
                return 0
        elif len(datas['id']) == 1:
            result = db.fetchone('select idx, flagName from _questionnaire_q_flag_info where relation={} and idx={}'
                                 .format(datas['type'], datas['id'][0]))
            if not result:
                return 0
            else:
                lt = list()
                lt.append(result)
                return lt
        else:
            result = db.fetchall('select idx, flagName from _questionnaire_q_flag_info where relation={}'
                                 .format(datas['type']))
            if not result:
                return 0

        lt = list()
        for temp in result:
            dic = dict()
            dic['idx'] = temp['idx']
            dic['flagName'] = temp['flagName']
            lt.append(dic)
        return lt

    def get_recently_test_time(datas):
        """获取最近的评测时间"""
        db = DBHelper.DB()
        result = db.fetchone('select max(startTime) as s_time from _questionnaire_q_review_main where answerUser={}'
                             .format(datas['user_id']))
        return result['s_time']

    def check_flag_exist(datas):
        """查寻标签是否存在"""
        db = DBHelper.DB()
        result = db.fetchone('select idx from _questionnaire_q_flag_info where flagName="{}" and relation=3'
                             .format(datas['flag']))
        return result

    def add_enterprise_flag(datas):
        """添加企业标签"""
        db = DBHelper.DB()
        result = db.updateRowid('insert into _questionnaire_q_flag_info(flagName, relation) values("{}", 3)'
                                .format(datas['flag']))
        return result

    def get_my_enterprise_flag(datas):
        """获取本企业的标签信息"""
        db = DBHelper.DB()
        result = db.fetchone('select flag from _questionnaire_q_enterprise_info where idx={}'.format(datas['idx']))
        return result

    def modify_my_enterprise_flag(datas):
        """更新企业的标签信息"""
        db = DBHelper.DB()
        result = db.update('update _questionnaire_q_enterprise_info set flag="{}",modifyTime=now() where idx={}'
                           .format(datas['flag_id'], datas['idx']))
        return result

    def modify_enterprise_remark_info(datas):
        """修改企业备注信息"""
        db = DBHelper.DB()
        result = db.update('update _questionnaire_q_enterprise_info set remark="{}",modifyTime=now() where idx={}'
                           .format(datas['remark'], datas['idx']))
        return result

    def get_enterprise_user_info(datas):
        """获取企业对应用户的信息"""
        db = DBHelper.DB()
        result = db.fetchall('select idx,`name`,image,email,mobile,department,`position`,birthday,gender,roleId,'
                             'createTime from _questionnaire_q_user_info where enterpriseId={}'
                             .format(datas['idx']))
        lt = list()
        for temp in result:
            dic = dict()
            if temp['roleId'] == 1:
                temp['role_name'] = '管理员'
            else:
                temp['role_name'] = '普通用户'
            dic['idx'] = temp['idx']
            dic['name'] = temp['name']
            dic['image'] = temp['image']
            dic['email'] = temp['email']
            dic['mobile'] = temp['mobile']
            dic['department'] = temp['department']
            dic['position'] = temp['position']
            dic['birthday'] = temp['birthday']
            dic['gender'] = temp['gender']
            dic['role_name'] = temp['role_name']
            dic['createTime'] = temp['createTime']
            lt.append(dic)
        return lt

    def get_enterprise_all_info(datas):
        '''获取企业答题问卷信息'''
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
        if len(datas['user_id']) > 1:
            result = db.fetchall(
                'select idx,id,`name`,startTime,endTime,completeStatus,remark,A.answerUser as user_id from '
                '_questionnaire_q_review_main as A join _questionnaire_q_test_attribute as B on A.testId=B.id where '
                'A.answerUser in {} and {}'.format(datas['user_id'], sql))
        elif len(datas['user_id']) == 1:
            result = db.fetchall(
                'select idx,id,`name`,startTime,endTime,completeStatus,remark,A.answerUser as user_id from '
                '_questionnaire_q_review_main as A join _questionnaire_q_test_attribute as B on A.testId=B.id where '
                'A.answerUser={} and {}'.format(datas['user_id'][0], sql))
        lt = list()
        for temp in result:
            dic = dict()
            dic['idx'] = temp['idx']
            dic['user_id'] = temp['user_id']
            dic['id'] = temp['id']
            dic['name'] = temp['name']
            dic['startTime'] = temp['startTime']
            dic['endTime'] = temp['endTime']
            dic['completeStatus'] = temp['completeStatus']
            dic['remark'] = temp['remark']
            lt.append(dic)
        return lt

    def get_questions_info(datas):
        '''获取问卷的所有问题'''
        db = DBHelper.DB()
        res = db.fetchone('select questionId from _questionnaire_q_id_relation where testId={}'.format(datas['id']))
        return res['questionId']

    def getQuestionedCount(datas):
        '''获取已经做答得问题个数'''
        db = DBHelper.DB()
        result = db.fetchone('select count(*) from _questionnaire_q_answer_detail where id={}'.format(datas['idx']))
        if result['count(*)']:
            return result['count(*)']
        return 0

    def searchTestId(datas):
        '''查询问卷id'''
        db = DBHelper.DB()
        result = db.fetchone('select count(1) from _questionnaire_q_id_relation where testId={}'.format(datas['id']))
        if result['count(1)']:
            return True
        return False

    def getQuestionsInfo(datas):
        '''获取问卷的所有问题'''
        db = DBHelper.DB()
        res = db.fetchone('select questionId from _questionnaire_q_id_relation where testId={}'.format(datas['id']))
        return res['questionId']

    def searchTestStatus(datas):
        '''获取总答题的状态'''
        db = DBHelper.DB()
        res = db.fetchone('select idx from _questionnaire_q_review_main where testId={} and completeStatus={} and '
                          'answerUser={}'.format(datas['id'],datas['completeStatus'], datas['user_id']))
        return res

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
            '_questionnaire_q_questions as A join _questionnaire_q_question_test_type as B where A.idx = B.qId)as C '
            'where C.idx={}'.format(datas['qId']))
        rt = dict()
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

    def get_tree_struct_info(datas):
        """获取试题梳妆结构数据"""
        db = DBHelper.DB()
        sql = ''
        if datas['lv'] == 1:
            sql += 'level1'
        elif datas['lv'] == 2:
            sql += 'level1,level2'
        elif datas['lv'] == 3:
            sql += 'level1,level2,level3'
        elif datas['lv'] == 4:
            sql += 'level1,level2,level3,level4'
        elif datas['lv'] == 5:
            sql += 'level1,level2,level3,level4,level5 '
        res = db.fetchall(
            'select distinct {} from _questionnaire_q_question_test_type where '
            'testId={}'.format(sql, datas['id']))
        return res

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
