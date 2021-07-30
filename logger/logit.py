import concurrent.futures 
import logging
from datetime import datetime
import pymongo as pmg
import uuid
class Logit:

    """
    logger class
    use this class to log the execution of the program.

    code for usage:
    
    >>>from logger.logit import Logit
    >>>l = Logit()
    >>>l.log("scope","message")
         
    """
    def __init__(self):
        logging.basicConfig(filename='execution.log', level=logging.DEBUG)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        DEFAULT_CONNECTION_URL = 'localhost:27017'
        client = pmg.MongoClient(DEFAULT_CONNECTION_URL)

        self.conn = client["execution_log"]["log"] 
        # conn.insert_one()
    def log(self, scope,msg):

        id_obj=self.conn.find({}, {"_id"})
        idxt = []
        for idx in id_obj:
            idxt.append(idx)

        if datetime.now().date() in idxt:
            self.executor.submit(self.conn.update, {"_id":datetime.now().date(),f"{uuid.uuid1()}":f"{datetime.now().date()} {datetime.now().strftime('%H:%M:%S')} {scope} {msg}"})
        else:
            self.executor.submit(self.conn.insert_one, {"_id":datetime.now().date(),f"{uuid.uuid1()}":f"{datetime.now().date()} {datetime.now().strftime('%H:%M:%S')} {scope} {msg}"})


# if __name__=="__main__":
#     l = Logit()
#     for i in range(10):
#         l.log("I'm a log",type=logging.error)
#     l.log("test")