#coding=utf-8
import pymysql

# import util.ConfigHelp
import os
import json
class DB():

    # 获取数据库访问链接
    def __init__(self):
        DB_SECRET_FILE =  'sysConfig.json'
        if True == os.path.exists(DB_SECRET_FILE):
            with open(DB_SECRET_FILE) as json_file:
                data = json.load(json_file)
                self.DB_HOST = data['DB']['host']
                self.DB_PORT = data['DB']['port']
                self.DB_USER = data['DB']['user']
                self.DB_PWD = data['DB']['password']
                self.DB_NAME = data['DB']['database']
                self.CHAR_SET = data['DB']['charset']

                self.conn = self.getConnection()
                cursorclass = pymysql.cursors.DictCursor
        # data = ConfigHelp.getSysConfig()
        # print(data)
        # if(data != None):
        #     self.DB_HOST = data['DB']['host']
        #     self.DB_PORT = data['DB']['port']
        #     self.DB_USER = data['DB']['user']
        #     self.DB_PWD = data['DB']['password']
        #     self.DB_NAME = data['DB']['database']
        #     self.CHAR_SET = data['DB']['charset']
        #
        #     self.conn = self.getConnection()

        # else:
        #
        #     self.DB_HOST = '127.0.0.1'
        #     self.DB_PORT = '3306'
        #     self.DB_USER = 'root'
        #     self.DB_PWD = 'root'
        #     self.DB_NAME = 'osExtend'
        #     self.CHAR_SET = 'utf8'
        #     self.conn = self.getConnection()

    # def __init__(self, host, port, user, password, database, charset):
    #     self.DB_HOST = host
    #     self.DB_PORT = port
    #     self.DB_USER = user
    #     self.DB_PWD = password
    #     self.DB_NAME = database
    #     self.CHAR_SET = charset
    #
    #     self.conn = self.getConnection()

    def getConnection(self):
        return pymysql.Connect(
            host=self.DB_HOST,  # 设置MYSQL地址
            port=self.DB_PORT,  # 设置端口号
            user=self.DB_USER,  # 设置用户名
            passwd=self.DB_PWD,  # 设置密码
            db=self.DB_NAME,  # 数据库名
            charset= self.CHAR_SET,  # 设置编码
            cursorclass = pymysql.cursors.DictCursor
        )

    def getConnectionLink(self, dbAddr, dbPort, dbUser, dbPass):
        return pymysql.Connect(
            host= dbAddr,  # 设置MYSQL地址
            port= dbPort,  # 设置端口号
            user= dbUser,  # 设置用户名
            passwd= dbPass,  # 设置密码
            charset="utf8",  # 设置编码
            cursorclass = pymysql.cursors.DictCursor
        )

    def fetchall(self, sqlString):
        print(sqlString)
        cursor = self.conn.cursor()
        cursor.execute(sqlString)
        returnData = cursor.fetchall()
        cursor.close()
        self.conn.close()
        return returnData

    def fetchone(self, sqlString):
        print(sqlString)
        cursor = self.conn.cursor()
        cursor.execute(sqlString)
        returnData = cursor.fetchone()
        cursor.close()
        self.conn.close()
        return returnData

    def fetchmany(self, sqlString, size):
        cursor = self.conn.cursor()
        cursor.execute(sqlString)
        returnData = cursor.fetchmany(size)
        cursor.close()
        self.conn.close()
        return returnData

    def rowcount(self, sqlString, size):
        cursor = self.conn.cursor()
        cursor.execute(sqlString)
        returnData = cursor.rowcount(size)
        cursor.close()
        self.conn.close()
        return returnData

    def update(self, sqlString):
        result =0
        try:
            print(sqlString)
            cursor = self.conn.cursor()
            result = cursor.execute(sqlString)
            self.conn.commit()
            cursor.close()
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            self.conn.close()
        return result

    def updateRowid(self, sqlString):
        result = 0
        try:
            print(sqlString)
            cursor = self.conn.cursor()
            cursor.execute(sqlString)
            self.conn.commit()
            cursor.close()
            result = cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            self.conn.close()
        return result

    def fetchallByPageAndLimit(self, sqlString, pagesize, limit):
        limtWhere = ""
        if pagesize != "" and limit != "":
            limtWhere += " LIMIT %d, %d" % (((int(pagesize) - 1) * int(limit)), int(limit))
        sqlString = sqlString + limtWhere
        print(sqlString)
        cursor = self.conn.cursor()
        cursor.execute(sqlString)
        returnData = cursor.fetchall()
        cursor.close()
        self.conn.close()
        return returnData


# if __name__=="__main__":
#     db=DB()
#     #print(db.query("SELECT * FROM ANDON_EVENT_RECORD;"))
#     print (db.fetchall("select * from _sys_t_sdl_service;"))