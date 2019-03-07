from util import DBHelper

class SystemDao():

    def addSystemDict(dictid, value, valueName):
        """添加数据字典"""
        db = DBHelper.DB()
        result = db.update('INSERT INTO _plat_sys_system_dict (dictid, value, valueName) VALUES ("%s", "%s", "%s")'  % (dictid, value, valueName))
        return result

    def uniqueSystemDict(dictid, value):
        """判断服务参数url和id是否唯一"""
        db = DBHelper.DB()
        result = db.fetchone("select count(1) from _plat_sys_system_dict where dictid = '%s' and value = '%s'" % (
            dictid, value))
        if(result["count(1)"] == 0):
            return True
        return False

    def updateSystemDict(newVlaue, valueName, dictid, oldValue):
        """修改数据字典"""
        db = DBHelper.DB()
        sqlWhere = ""
        if newVlaue != "":
            sqlWhere += " value = '%s'," % (newVlaue)
        # if valueName != "":
        # todo：可以为空， 取消判断
            sqlWhere += "  valueName = '%s',"%(valueName)

        if sqlWhere == "":
            return 0;
        else:
            sqlWhere = sqlWhere[:-1]

        result = db.update("UPDATE _plat_sys_system_dict SET %s WHERE dictid = '%s' AND value = '%s' " %
                           (sqlWhere, dictid, oldValue))
        return result

    # 增加相同值时，更新成功
    # todo: desc:增加函数 modifyBy:zuxiaojun date:20180504
    def selectCommonDict(newValue, ValueName, dictid):
        '''获取数据'''
        db = DBHelper.DB()
        result = db.fetchone('SELECT count(1) FROM _plat_sys_system_dict WHERE dictid="{val}" AND `value`="{value}"AND '
                             'valueName="{name}"'.format(val=dictid, value=newValue, name=ValueName))

        if result["count(1)"]:
            return True
        return False


    def deleteSystemDict(dictid, value):
        """删除数据字典"""
        db = DBHelper.DB()
        sqlWhere = ""
        if value != "":
            sqlWhere = " AND value = '%s' " % (value)
        result = db.update("DELETE FROM _plat_sys_system_dict WHERE dictid = '%s' %s" % (
            dictid, sqlWhere))
        return result

    def getSystemDict(dictid):
        """获取数据字典"""
        db = DBHelper.DB();
        return db.fetchall("SELECT value, valueName FROM _plat_sys_system_dict WHERE dictid = '%s'" %(
              dictid))

    def getErrorMsg(url, errorCode):
        """获取服务错误码描述"""
        db = DBHelper.DB()
        result = db.fetchone(
            "select description from _plat_sys_t_sdl_error where url = '%s' and errorCode = '%s'" % (
                url, errorCode))
        if (result == None):
            return ""
        return result["description"]

    def readSql(sql):
        """执行读SQL命令"""
        db = DBHelper.DB()
        result = db.fetchall(sql)
        return result

    def witerSql(sql):
        """执行写SQL命令"""
        db = DBHelper.DB()
        result = db.update(sql)
        return result