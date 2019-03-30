try:
    import pyodbc
except:
    print('module "pyodbc" is not avalable for your recent system circustance')
    pass
try:
    import pymysql
except:
    print('module "pymysql" is not avalable for your recent system circustance')
    pass
try:
    import pymssql
except:
    print('module "pymssql" is not avalable for your recent system circustance')
    pass



class Database:
    """
    This class support three ways to connect to database system.
    At first you have to get one of these packages : pymysql, pyodbc, pymssql.
    Param dbConfig is a dictionary including at least the following params : host, user, password, dbname.
    :param host         :       the server name or ip of your database system
    :param user         :       user's login name or id ect
    :param password     :       your password
    :param dbname       :       database name that you want to use
    :param mode         :       the way you choose to use to connect to database system
                                1 means pymysql to mysql, 2 means pyodbc to sqlserver and 3 is pymssql to sqlserver
    So the dbConfig should looks like :
        dbConfig={'host': 'localhost', 'user': 'root', 'password': 'xxx', 'dbname': 'test', 'mode': 1}
    """

    def __init__(self, dbConfig={'host': 'localhost', 'user': 'root', 'password': '321', 'dbname': 'tmp', 'mode': 1}):
        self.dbConfig = dbConfig
        self.con = self.getCon(self.dbConfig)
        self.cur = self.con.cursor()

        # add belows to make it convenience for us to make detail params in dnConig
        self.mode = int(dbConfig['mode'])
        self.host = dbConfig['host']
        self.user = dbConfig['user']
        self.passwrod = dbConfig['password']
        self.dbname = dbConfig['dbname']
        if 'tbname' in self.dbConfig:
            self.tbname = self.dbConfig['tbname']
        else:
            self.tbname = ''

    @staticmethod
    def getCon(dbConfig):
        """
        建立连接的函数，之前是写在类里面的
        :param host         :       the server name or ip of your database system
        :param user         :       user's login name or id ect
        :param password     :       your password
        :param dbname       :       database name that you want to use
        :param mode         :       the way you choose to use to connect to database system
                                    1 means pymysql to mysql, 2 means pyodbc to sqlserver and 3 is pymssql to sqlserver
        So the dbConfig should look like :
            dbConfig={'host': 'localhost', 'user': 'root', 'password': 'xxx', 'dbname': 'test', 'mode': 1}
        """
        mode = int(dbConfig['mode'])
        host = dbConfig['host']
        user = dbConfig['user']
        passwrod = dbConfig['password']
        dbname = dbConfig['dbname']
        # way to connect to mysql with pymysql
        if mode == 1:
            con = pymysql.connect(host='%s' % host, user='%s' % user,
                                  password='%s' % passwrod, charset="utf8")

        # way to connect to sqlserver with pyodbc
        elif mode == 2:
            con = pyodbc.connect(
                'DRIVER={SQL Server};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s' % (
                    host, dbname, user, passwrod))

        # way to connect to sqlserver with pymssql
        else:
            con = pymssql.connect(server='%s' % host, user='%s' % user,
                                  password='%s' % passwrod, database='%s' % dbname, charset='UTF-8')
            pymssql.set_max_connections(200000)
        return con

    def build(self,dbname,tbname, data, mode):
        """
           This method is mainly designed to build up sql sentence, with extra value which has to satisfy the grammar of each module that imported
           @:param see method "insert"
       """
        # field = list(sorted(data.keys(), key=lambda x: x[0]))
        field = list(data.keys())
        value = [str(data[x]) for x in field]

        # sql for mysql, with params of type dict
        if mode == 1:
            sql = """insert into %s.%s(%s)values(%s)""" % (
                dbname, tbname, str(field)[1:-1].replace("'", ''),
                '%(' + ('-'.join(field)).replace('-', ')s,%(') + ')s')
            return sql, data

        # sql for pyodbc, with params of type list
        elif mode == 2:
            sql = """insert into %s.dbo.%s (%s) values (%s)""" % (
                dbname, tbname, str(field).replace(", ", '],[').replace("'", ''),
                (len(field) * '?,')[:-1])
            return sql, value

        # sql for pymssql, with params of type tuple
        else:
            sql = """insert into %s.dbo.%s(%s)values(%s)""" % (
                dbname, tbname, str(field).replace(", ", '],[').replace("'", ''),
                str('%s,' * len(field))[0:-1])
            return sql, tuple(value)

    @staticmethod
    def tuple_to_dict(data):
        """
        把tuple类型的数据格式转成dict类型
        :param data:    以元组形式存放的list，如：[('name':'罗大黑'), ('age': 25)]
        :return:        以字典形式存放的list，如：{'name': '罗大黑', 'age': 25}
        """
        return dict(data)

    def insert(self,data,dbname=None,tbname=None,mode=None):
        """
        This methed support some convenient ways for you to insert your data into database.
        :param dbname       :          name of database
        :param tbname       :          name of table
        :param data         :          data you that want to insert into, type dict or list with dicts
        :param mode         :          mode, different mode leads to different database system
        If mode == 1, the insert sql looks like :
            insert into dbname.tbname (field1, field2, field3) values (%(field1)s, %(field2)s, %(field3)s)
        if mode == 2:
            insert into dbname.tbname (field1, field2, field3) values (?, ?, ?)
        if mode == 3:
            insert into dbname,tbname (field1, field2, field3) values (%s, %s, %s)......
        And your data should be like data={'itemid': xxx, 'itemtitle': xxx}
        """
        if mode is None:
            mode = self.dbConfig['mode']

        if not dbname:
            dbname = self.dbConfig['dbname']
        if not tbname:
            if 'tbname' in self.dbConfig:
                tbname = self.dbConfig['tbname']
            else:
                raise Exception('请在self.dbConfig传入表名或在insert函数传入表名')

        if tbname.find('.') > 0:
            tbname = tbname.split('.')[-1]

        # type dict
        if type(data) == dict:
            result = self.build(dbname,tbname, data, mode)
            self.cur.execute(result[0], result[1])
            self.con.commit()

        # type list with dict
        if type(data) == list:
            for m_data in data:
                if isinstance(m_data, dict):
                    result = self.build(dbname, tbname, m_data, mode)
                elif isinstance(m_data, list):
                    result = self.tuple_to_dict(m_data)
                self.cur.execute(result[0], result[1])
                self.con.commit()


    def execute(self, sql, *params):
        self.cur.execute(sql, *params)
        # if sql.find('select') >= 0:
        #     return self.cur.fetchall()
        return self.cur

    def commit(self):
        self.con.commit()

    def fetchall(self):
        self.cur.fetchall()

    def fetchone(self):
        self.cur.fetchone()

    def close(self):
        self.con.close()
