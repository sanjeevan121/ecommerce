import concurrent.futures
from datetime import datetime
import pymongo as pmg
import os
import uuid
from dotenv import load_dotenv
load_dotenv()
import pytz

tz_ind = pytz.timezone('Asia/Kolkata')
now = datetime.now(tz_ind)

class Logit:
    """
    logger class
    use this class to log the execution of the program.
    code for usage:

    #>>>from logger.logit import Logit
    #>>>l = Logit()
    #>>>l.log("scope","message")   # where scope = function name or class name and message = any string


    """

    def __init__(self):
        # self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

        # DEFAULT_CONNECTION_URL = 'localhost:27017'
        # client = pmg.MongoClient(DEFAULT_CONNECTION_URL)
        client = pmg.MongoClient(os.getenv('connection'))

        self.conn = client["execution_log"]["log"]

    def UPDATE(self, DICT):
        self.conn.update_one({"_id": int(str(datetime.now().date()).replace("-", ""))}, {'$push': DICT})

    def INSERT(self, DICT):
        self.conn.insert_one(DICT)

    def log(self, scope, msg):

        id_obj = self.conn.find({}, {"_id"})
        idxt = []
        for idx in id_obj:
            idxt.append(idx["_id"])
        # self.conn.insert_one({"_id":int(str(datetime.now().date()).replace("-","")),f"{uuid.uuid1()}":f"{str(datetime.now().date())} {str(datetime.now().strftime('%H:%M:%S'))} {scope} {msg}"})
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            if int(str(datetime.now().date()).replace("-", "")) in idxt:
                executor.submit(self.UPDATE, {
                    f"{uuid.uuid1()}": f"{str(datetime.now().date())} {str(datetime.now().strftime('%H:%M:%S'))} {scope} {msg}"})
            else:
                executor.submit(self.INSERT, {"_id": int(str(datetime.now().date()).replace("-", "")),
                                              f"{uuid.uuid1()}": f"{str(datetime.now().date())} {str(datetime.now().strftime('%H:%M:%S'))} {scope} {msg}"})

    def userlog(self, userId, action, performedOn, categoryId, productId, totalPayment):
        client = pmg.MongoClient(os.getenv('connection'))
        self.conn = client["Clean_user"]["CleanUser"]
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(self.conn.insert_one, {"user_id": userId, "action": action, "performed_on": performedOn,
                                                    "category_ID": categoryId, "productId": productId,
                                                    "totalPayment": totalPayment, "year": now.year, "month": now.month,
                                                    "day": now.day, "hour": now.hour, "minute": now.minute,
                                                    'second': now.second})

#l=Logit()
#l.userlog(userId=8, action='clicked', performedOn='category', categoryId=4, productId="",
              #         totalPayment="")
    # if __name__=="__main__":
    #     l = Logit()
    #     for i in range(10):
    #         l.log("none","I'm a log")
    #     l.log("nope","test")
