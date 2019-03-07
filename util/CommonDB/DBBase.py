import pymysql
import os
import json

class DBTrans():

    def __init__(self):
        DB_SECRET_FILE = 'sysConfig.json'
        if True == os.path.exists(DB_SECRET_FILE):
            with open(DB_SECRET_FILE) as json_file:
                data = json.load(json_file)
                self.DB_HOST = data['DB']['host']
                self.DB_PORT = data['DB']['port']
                self.DB_USER = data['DB']['user']
                self.DB_PWD = data['DB']['password']
                self.DB_NAME = data['DB']['database']
                self.CHAR_SET = data['DB']['charset']

                self.DBConn=self.CreateConnection()
                self.Cursor = self.DBConn.cursor()
    #创建数据库连接
    def CreateConnection(self):
        return pymysql.Connect(
            host=self.DB_HOST,  # 设置MYSQL地址
            port=self.DB_PORT,  # 设置端口号
            user=self.DB_USER,  # 设置用户名
            passwd=self.DB_PWD,  # 设置密码
            db=self.DB_NAME,  # 数据库名
            charset= self.CHAR_SET,  # 设置编码
            cursorclass=pymysql.cursors.DictCursor
        )
    #关闭数据库连接
    def Close(self):
        self.Cursor.close()
        self.DBConn.close()
    #回滚事物
    def Rollback(self):
        self.DBConn.rollback()
    #提交事物
    def Commit(self):
        self.DBConn.commit()

    #查询结果集
    def FetChall(self, sqlString, params = None):
        try:
            self.Cursor.execute(sqlString, params)
            returnData = self.Cursor.fetchall()
            return returnData
        except Exception as e:
            raise e

    #获取一行结果集
    def FetChone(self, sqlString, params = None):
        try:
            self.Cursor.execute(sqlString, params)
            returnData = self.Cursor.fetchone()
            return returnData
        except Exception as e:
            raise e

    #获取指定行结果集
    def FetChmany(self, sqlString, size, params = None):
        try:
            self.Cursor.execute(sqlString, params)
            returnData = self.Cursor.fetchmany(size)
            return returnData
        except Exception as e:
            raise e

    #获取结果集行数
    def RowsCount(self, sqlString, size, params = None):
        try:
            self.Cursor.execute(sqlString, params)
            result = self.Cursor.rowcount(size)
            return result
        except Exception as e:
            raise e

    #执行SQL语句
    def ExecNonQuery(self, sqlString, params = None):
        try:
            result = 0
            print(sqlString)
            result = self.Cursor.execute(sqlString, params)
            return result
        except Exception as e:
            raise e

    # 执行SQL语句，返回主键ID
    def ExecNonQueryNewID(self, sqlString, params = None):
        try:
            result = 0
            self.Cursor.execute(sqlString, params)
            result = self.Cursor.lastrowid
            return result
        except Exception as e:
            raise e


