import time
import base64
import numpy as np
import win32pipe, win32file, pywintypes
from datetime import timedelta, datetime  
from dateutil import tz
import threading
import tkinter as tk
from tkinter import Text
import queue as Queue
from PIL import Image
import cv2
import pickle


thread_active = True
data_cap = []
display_refresh = 1000
data_retention = 10


def display_main():
    
    class ThreadedTask(threading.Thread):
        def __init__(self, master):
            threading.Thread.__init__(self)
            self.master = master
            self.quit_thread = False
        
        def run(self):
            while not self.quit_thread:
                try:
                    handle = win32file.CreateFile(r'\\.\pipe\Foo',
                                                  win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                                                  0,None,
                                                  win32file.OPEN_EXISTING,
                                                  0,None)
                    
                    res = win32pipe.SetNamedPipeHandleState(handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)
                    
                    if res == 0:
                        print(f"SetNamedPipeHandleState return code: {res}")
        
                    while True:
                        resp = win32file.ReadFile(handle, 64*1024)
                        #det, time1, width, height, imgg = resp[1].decode(encoding='utf-8', errors='strict').split('__')
                        det, time1 = resp[1].decode(encoding='utf-8', errors='strict').split('__')
                        
                        resp = win32file.ReadFile(handle, 4096*4096)
                        
                        imgg  = pickle.loads(resp[1])
                        #print(imgg.mean())
                        #cv2.imshow('pic',imgg)
                        #cv2.waitKey(10)
                        #imgg = imgg.encode()
                        #print(imgg)
                        #print(type(imgg))
                        #imgg = np.fromstring(imgg, np.uint8)
                        #print(imgg)
                        #print(type(imgg))
                        #imgg = cv2.imdecode(imgg,cv2.IMREAD_COLOR)
                        #print(imgg)
                        #print(type(imgg))

                        #imgg = base64.b64decode(imgg)
                        #print(imgg)
                        #img = Image.frombytes('RGB',(int(width),int(height)), imgg)
                        #img.show()
                        est = datetime.strptime(time1,'%m/%d/%Y %I:%M:%S %p')
                        est = est.replace(tzinfo=tz.gettz('America/New_York'))                
                        global data_cap
                        data_cap.append((det,est, imgg))
                except pywintypes.error as e:
                    if e.args[0] == 2:
                        time.sleep(display_refresh)
                    elif e.args[0] == 109:
                        self.quit_thread = True
        
    
    class GUI:
        def __init__(self, master):
            self.master = master
            self.master.title("Display Monitor")
            self.queue = Queue.Queue()
            self.qt = ThreadedTask(self.master)
            self.qt.start()
            self.data = Text(self.master,height=30, width=100)
            self.data.pack(side="left")
        
        def counter_label(self):
            
            def disp_data(data_cap):
                if data_cap:
                    temp = []
                    n = datetime.now().replace(tzinfo=tz.gettz('America/New_York'))
                    for i,j,k in data_cap:
                        id, msg = i.split('_')
                        msg = msg.ljust(50)
                        secs = (n - j)
                        time = j.strftime('%I:%M:%S %p')
                        temp.append('{0}   {1}   {2} expiring in {3} secs'.format(time,id,msg, 1 + int(data_retention - secs.total_seconds())))
                    return '\n\n'.join(temp)
                else:
                    return ""
                
            
            def count():
                global data_cap
                self.master.title("Display Monitor - " + datetime.now().strftime('%m/%d/%Y %I:%M:%S %p %Z'))
                self.data.delete('1.0', tk.END)
                data_cap = remove_old_data(data_cap)
                self.data.insert(tk.END,disp_data(data_cap))
                if not self.qt.quit_thread:
                    self.data.after(display_refresh, count)
                else:
                    self.master.quit()
            count()        
        
    root = tk.Tk()
    
    main_ui = GUI(root)
    main_ui.counter_label()
    root.mainloop()
    
def remove_old_data(data):
    now = datetime.now().replace(tzinfo=tz.gettz('America/New_York')) - timedelta(seconds=data_retention)
    data = [(i,j,k) for i,j,k in data if j >= now ]
    return data

if __name__ == '__main__':
    display_main()

