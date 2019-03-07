import pymysql
from .DBBase import DBTrans

#查询结果集
def FetChall(sqlString, params = None):
    returnData=[]
    print(sqlString,params)
    DB = DBTrans()
    try:
        returnData = DB.FetChall(sqlString, params)
    finally:
        DB.Close()
    return returnData

#获取一行结果集
def FetChone(sqlString, params = None):
    returnData = []
    DB = DBTrans()
    try:
        returnData = DB.FetChone(sqlString, params)
    finally:
        DB.Close()
    return returnData

#获取指定行结果集
def FetChmany(sqlString, size, params = None):
    returnData = []
    DB = DBTrans()
    try:
        returnData = DB.FetChmany(sqlString, size, params)
    finally:
        DB.Close()
    return returnData


#获取结果集行数
def RowsCount(sqlString, size, params = None):
    returnData = 0
    DB = DBTrans()
    try:
        returnData = DB.RowsCount(sqlString, size, params)
    finally:
        DB.Close()
    return returnData

#执行SQL语句
def ExecNonQuery(sqlString, params = None):
    returnData = 0
    DB = DBTrans()
    try:
        returnData = DB.ExecNonQuery(sqlString, params)
        DB.Commit()
    except Exception as e:
        DB.Rollback()
        raise e
    finally:
        DB.Close()
    return returnData

# 执行SQL语句，返回主键ID
def ExecNonQueryNewID(sqlString, params = None):
    returnData = 0
    DB = DBTrans()
    try:
        print(sqlString)
        returnData = DB.ExecNonQueryNewID(sqlString, params)
        DB.Commit()
    except Exception as e:
        DB.Rollback()
        raise e
    finally:
        DB.Close()
    return returnData

#判断数据表是否存在
def ExistTable(tableName):
    DB = DBTrans()
    returnData = False
    try:
        data = DB.FetChall("show tables like '%s'" %tableName)
        returnData = len(data) > 0
    finally:
        DB.Close()
    return returnData


