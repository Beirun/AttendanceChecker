from sqlite3 import connect,Row

database:str = 'student.db'

def postprocess(sql:str)->bool:
    #connect to database
    db:object = connect(database)
    #create a cursor
    cursor:object = db.cursor()
    #execute the sql command
    cursor.execute(sql)
    #commit the command
    db.commit()
    #close the database
    cursor.close()
    return True if cursor.rowcount>0 else False

def getprocess(sql:str)->list:
    #connect to database
    db:object = connect(database)
    #create a cursor
    cursor:object = db.cursor()
    #convert the record into an object
    cursor.row_factory = Row
    #execute the sql command
    cursor.execute(sql)
    #fetch all the data
    data:list = cursor.fetchall()
    #close the database connection
    cursor.close()
    #return the collected data
    return data