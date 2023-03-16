from time import sleep
import sys
sys.path.insert(0,"/home/pi/lib/python")
#from turret_cam_pipeline import GripPipeline
import threading
import collections


class vision_thread_mgr:
    def __init__(self,cv_method,cv_args):
        self.cv_thread = None
        self.cv_method = cv_method
        self.cv_args = cv_args

    def start(self,delay=2):
        sleep(delay)

        self.cv_thread = threading.Thread(target=self.cv_method,args=self.cv_args)
        self.cv_thread.start()
        
        print("Storm Core vision started thread")
        

    def is_alive(self):
        return self.cv_thread.is_alive()

    def restart(self):
        if not self.cv_thread.is_alive():
            self.cv_thread = threading.Thread(target=self.cv_method,args=self.cv_args)
            self.cv_thread.start()
        

