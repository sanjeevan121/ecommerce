import concurrent.futures 
from datetime import datetime
import pymongo as pmg
import os
import uuid

class Logit:

    """
    logger class
    use this class to log the execution of the program.

    code for usage:
    
    >>>from logger.logit import Logit
    >>>l = Logit()
    >>>l.log("scope","message")   # where scope = function name or class name and message = any string
    
         
    """
    def __init__(self):
        # self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

        # DEFAULT_CONNECTION_URL = 'localhost:27017'
        # client = pmg.MongoClient(DEFAULT_CONNECTION_URL)
        client = pmg.MongoClient(os.getenv('connection'))

        self.conn = client["execution_log"]["log"] 

    def UPDATE(self, DICT):
        self.conn.update_one({"_id": int(str(datetime.now().date()).replace("-",""))},{ '$push' : DICT})

    def INSERT(self, DICT):
        self.conn.insert_one(DICT)

    def log(self, scope, msg):

        id_obj=self.conn.find({}, {"_id"})
        idxt = []
        for idx in id_obj:
            idxt.append(idx["_id"])
        # self.conn.insert_one({"_id":int(str(datetime.now().date()).replace("-","")),f"{uuid.uuid1()}":f"{str(datetime.now().date())} {str(datetime.now().strftime('%H:%M:%S'))} {scope} {msg}"})
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            if int(str(datetime.now().date()).replace("-","")) in idxt:
                executor.submit(self.UPDATE, {f"{uuid.uuid1()}":f"{str(datetime.now().date())} {str(datetime.now().strftime('%H:%M:%S'))} {scope} {msg}"})
            else:
                executor.submit(self.INSERT, {"_id":int(str(datetime.now().date()).replace("-","")),f"{uuid.uuid1()}":f"{str(datetime.now().date())} {str(datetime.now().strftime('%H:%M:%S'))} {scope} {msg}"})


# if __name__=="__main__":
#     l = Logit()
#     for i in range(10):
#         l.log("none","I'm a log")
#     l.log("nope","test")