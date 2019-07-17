import time
import win32pipe, win32file, pywintypes
from datetime import timedelta, datetime  

from threading import Thread

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
                data_cap = remove_old_data(data_cap)
            else:
                print('{0} - {1}'.format(datetime.now(),[]))
            time.sleep(display_refresh)
        else:
            break



def remove_old_data(data):
    now = datetime.now() - timedelta(seconds=data_retention)
    #print(now)
    data = [(i,j) for i,j in data if j > now ]
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
                data_cap.append((resp[1].decode(encoding='utf-8', errors='strict'), datetime.now()))
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
    pipe_client()

