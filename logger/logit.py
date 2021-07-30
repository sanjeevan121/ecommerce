import concurrent.futures 
import logging
from datetime import datetime


class Logit:

    """
    logger class
    use this class to log the execution of the program.

    code for usage:
    
    from logger.logit import Logit
    l = logit()
    l.log("message",type=logging.error)
         
    """
    def __init__(self):
        logging.basicConfig(filename=None
                            #,
                            #level=logging.DEBUG
        )
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1) 

    def log(self,file_object, msg , type=logging.info):
        self.executor.submit(type, f"{datetime.now().date()} {datetime.now().strftime('%H:%M:%S')} {msg}")


# if __name__=="__main__":
#     l = Logit()
#     for i in range(10):
#         l.log("I'm a log",type=logging.error)
#     l.log("test")