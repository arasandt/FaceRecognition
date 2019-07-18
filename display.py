import time
import win32pipe, win32file, pywintypes
from datetime import timedelta, datetime  
from dateutil import tz
from threading import Thread
import threading
import tkinter as tk
from tkinter import Button, TOP, ttk, Text
import queue as Queue

thread_active = True
data_cap = []
display_refresh = 3
data_retention = 10


def display():
    while True:
        global data_cap
        if thread_active:
            if data_cap:
                print('{0} - {1}'.format(datetime.now(),[i for i,j in data_cap]))
                #print('{0} - {1}'.format(datetime.now(),[(i,j) for i,j in data_cap]))
                data_cap = remove_old_data(data_cap)
            else:
                print('{0} - {1}'.format(datetime.now(),[]))
            time.sleep(display_refresh)
        else:
            break




def display_main():
    
    class ThreadedTask(threading.Thread):
        def __init__(self, master):
            threading.Thread.__init__(self)
            self.master = master
            self.quit_thread = False
        
        def run(self):
            #time.sleep(5)  # Simulate long running process
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
                        #data_cap.append((resp[1].decode(encoding='utf-8', errors='strict'), datetime.now())
                        det, time1 = resp[1].decode(encoding='utf-8', errors='strict').split('__')
                        est = datetime.strptime(time1,'%m/%d/%Y %I:%M:%S %p')
                        est = est.replace(tzinfo=tz.gettz('America/New_York'))                
                        global data_cap
                        data_cap.append((det,est))
                        #print(data_cap)
                        #self.queue.put(data_cap)
                        #print('')
                        #if len(data_cap) == 1:
                        #    print("")
                        
                        #print([i for i,j in data_cap])
                        #time.sleep(sec)
                        #print(f"got message: {resp}")
                except pywintypes.error as e:
                    if e.args[0] == 2:
                        #print("no data, trying again in a sec",end="\r")
                        time.sleep(1)
                    elif e.args[0] == 109:
                        #print("broken pipe, bye bye")
                        #while data_cap:
                            #data_cap = remove_old_data(data_cap) 
                        #    time.sleep(display_refresh)
                            
                        self.quit_thread = True
                        #global thread_active
                        #thread_active = False            
    
    class GUI:
        def __init__(self, master):
            self.master = master
            self.master.title("Display Monitor")
            self.queue = Queue.Queue()
            self.qt = ThreadedTask(self.master)
            self.qt.start()
            self.data = Text(self.master,height=30, width=100)
            self.data.pack(side="left")
            #self.master.after(100, self.process_queue)
            #return self
        
        
        def counter_label(self):
            
            def disp_data(data_cap):
                #import pprint
                if data_cap:
                    temp = []
                    n = datetime.now().replace(tzinfo=tz.gettz('America/New_York'))
                    for i,j in data_cap:
                        id, msg = i.split('_')
                        msg = msg.ljust(50)
                        secs = (n - j)
                        time = j.strftime('%I:%M:%S %p')
                        temp.append('{0}   {1}   {2} expiring in {3} secs'.format(time,id,msg, 1 + int(data_retention - secs.total_seconds())))
                    return '\n\n'.join(temp)
                else:
                    return ""
                #print('\n'.join(['{0} {1}'.format(str(i),str(j)) for i,j in data_cap]))
                
            
            def count():
                global data_cap
                self.master.title("Display Monitor - " + datetime.now().strftime('%m/%d/%Y %I:%M:%S %p %Z'))
                self.data.delete('1.0', tk.END)
                data_cap = remove_old_data(data_cap)
                self.data.insert(tk.END,disp_data(data_cap))
                if not self.qt.quit_thread:
                    self.data.after(1000, count)
                else:
                    self.master.quit()
            count()        
        
        #def process_queue(self):
        #    if data_cap:
        #        self.data.config(text=data_cap)
        #    else:
        #        self.master.after(100, self.process_queue)            
            #try:
                #msg = self.queue.get(0)
                #print('msg' + str(msg))# Show result of the task if needed
                #self.prog_bar.stop()
                #self.data.config(text=data_cap)
            #except Queue.Empty:
            #    self.master.after(100, self.process_queue)            

    root = tk.Tk()
    
    main_ui = GUI(root)
    main_ui.counter_label()
    root.mainloop()
    #print('Trying to quit thread')
    #main_ui.qt.quit_thread = True
    #print(main_ui.qt.quit_thread)
    #print(root)
    #main_ui.qt.join()
    
def remove_old_data(data):
    n = datetime.now().replace(tzinfo=tz.gettz('America/New_York'))
    now = n - timedelta(seconds=data_retention)
    #print(now)
    data = [(i,j) for i,j in data if j >= now ]
    return data

def pipe_client():
    print("Opening Display")
    quit = False
    global data_cap
    
    Thread(target = display).start()
    
    while not quit:
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
                #data_cap.append((resp[1].decode(encoding='utf-8', errors='strict'), datetime.now())
                det, time1 = resp[1].decode(encoding='utf-8', errors='strict').split('__')
                est = datetime.strptime(time1,'%m/%d/%Y %I:%M:%S %p')
                est = est.replace(tzinfo=tz.gettz('America/New_York'))                
                data_cap.append((det,est))
                data_cap = remove_old_data(data_cap)
                #if len(data_cap) == 1:
                #    print("")
                
                #print([i for i,j in data_cap])
                #time.sleep(sec)
                #print(f"got message: {resp}")
        except pywintypes.error as e:
            if e.args[0] == 2:
                #print("no data, trying again in a sec",end="\r")
                time.sleep(1)
            elif e.args[0] == 109:
                #print("broken pipe, bye bye")
                while data_cap:
                    #data_cap = remove_old_data(data_cap) 
                    time.sleep(display_refresh)
                    
                quit = True
                global thread_active
                thread_active = False


if __name__ == '__main__':
    #pipe_client()
    display_main()

