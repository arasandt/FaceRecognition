from __future__ import absolute_import
from __future__ import print_function

from glob import iglob
from utils import getFileTime, getFileHex
from datetime import timedelta, datetime
from dateutil import tz

import win32pipe, win32file
import os, cv2, sys, time
import random

data_retention = 20

def check_auth(label_id, office, floor):
    label_id = str(label_id)
    office = str(office)
    floor = str(floor)
    
    authorized = {'128537': ['Active','KNC', '6']}
    
    msg = ['Welcome..','Unknown','Not Authorized', 'Not Authorized for entry into ','Not Authorized for entry into floor ']
    
    if label_id in authorized.keys():
        if authorized[label_id][0] == 'Active':
            if authorized[label_id][1] == office:
                if authorized[label_id][2] == floor:
                    ret_msg = msg[0]
                else:
                    ret_msg = msg[4] + office + '#' + floor
            else:
                ret_msg = msg[3] + office
        else:
            ret_msg = msg[2] 
    else:
        ret_msg = msg[1] 
    return label_id + '_' + ret_msg
    

class Person_Details():
    
    def __init__(self, label_id):
        self.id = label_id
        self.time_keeper = None
        self.counter = 0
    
    def set_time(self, time_k):
        self.time_keeper = time_k.replace(tzinfo=tz.gettz('America/New_York'))
        self.time_keeper_fmt = self.time_keeper.strftime('%m/%d/%Y %I:%M:%S %p')
    
    def increment_count(self):
        self.counter += 1
        
    def send_to_display(self, func, office, floor):
        if self.counter == 5:
            auth_detail = func(self.id,office,floor) + '__' + self.time_keeper_fmt
            win32file.WriteFile(pipe, auth_detail.encode())
        

#data_hex = ['1d4750c785cec00']
#data_time = ['11/05/2018 08:35:52 AM']
#print(data_hex[0], "-->", getFileTime(data_hex[0]).strftime('%m/%d/%Y %I:%M:%S %p %Z'))
#print(data_time[0], "EST -->", getFileHex(data_time[0]))
#

#def run():
#    input_video_folder = 'input'
#    input_video_format = 'mp4'
#    for filename in iglob(os.path.join(input_video_folder,'*.' + input_video_format), recursive=False):    
#        name_with_ext = os.path.basename(filename).replace('.' + input_video_format,'')
#        timestamp, office, floor, camera_name, camera_id = name_with_ext.split('_')
#        timestamp = getFileTime(timestamp)
#        
#        video = cv2.VideoCapture(filename)
#        
#        fps = video.get(cv2.CAP_PROP_FPS)
#        total_frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
#        width = video.get(cv2.CAP_PROP_FRAME_WIDTH)
#        height = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
#        
#        video.release()
#        
#        duration = total_frames // fps 
#        end_time = timestamp + timedelta(seconds=duration) 
#        print(timestamp, office, floor, camera_name, camera_id, fps, total_frames, width, height, duration, end_time)

def create_pipe():
    pipe = win32pipe.CreateNamedPipe(r'\\.\pipe\Foo',
                                     win32pipe.PIPE_ACCESS_DUPLEX,
                                     win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                                     1, 65536, 65536,0,None)
    win32pipe.ConnectNamedPipe(pipe, None)
    print('Connected to Display')
    return pipe

def close_pipe(pipe):
    win32file.CloseHandle(pipe)


def print_details(person_detail):
    for i,j in person_detail.items():
        #print('{0} {1} {2}'.format(i,j.counter,j.time_keeper_fmt))
        n = datetime.now().replace(tzinfo=tz.gettz('America/New_York'))
        secs = n - j.time_keeper        
        print('{0} {1} expiring in {2} sec..'.format(i,j.counter,int(data_retention - secs.total_seconds())))
    
    
def remove_old_items(person_detail):
    remove = []
    for i,j in person_detail.items():
            n = datetime.now().replace(tzinfo=tz.gettz('America/New_York'))
            now = n - timedelta(seconds=data_retention)
            if j.time_keeper >= now:
                pass
            else:
                remove.append(i)
    
    [person_detail.pop(i) for i in remove]
    return person_detail     
        
def process_video_feed(filename, pipe):
    name_with_ext = os.path.basename(filename)
    timestamp, office, floor, camera_name, camera_id = name_with_ext.split('_')
    timestamp = getFileTime(timestamp)
    camera_id = camera_id.split('.')[0]
    
    video = cv2.VideoCapture(filename)
    
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
    width = video.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
    
    
    
    duration = total_frames // fps 
    end_time = timestamp + timedelta(seconds=duration) 
    print(timestamp, office, floor, camera_name, camera_id, fps, total_frames, width, height, duration, end_time)    
    
    count = 0
    
    person_detail = {}
    
    while True:
        (ret, frame) = video.read()
        
        if not ret:
            break
        
            
        # send frame for face detection and recognition
        
        # get label of persons identified and details
        #label_id = 128537
        
        label_id = random.randint(128537,128541)
        
        
        
        if person_detail.get(label_id, 0) == 0:
            #person_detail[label_id] = [1,datetime.now().replace(tzinfo=tz.gettz('America/New_York'))]
            person_detail[label_id] = Person_Details(label_id)
            #person_detail[label_id].set_time(datetime.now())
        #else:
#            person_detail[label_id][0] += 1
        if label_id == 128537 and person_detail[label_id].counter > 10:
            pass
        else:
            person_detail[label_id].set_time(datetime.now())
                #person_detail[label_id][1] = datetime.now().replace(tzinfo=tz.gettz('America/New_York'))
            
        person_detail[label_id].increment_count()
        person_detail[label_id].send_to_display(check_auth, office, floor)
        
        #if person_detail[label_id].counter == 5:
        #    auth_detail = check_auth(label_id, office, floor) + '__' + person_detail[label_id].time_keeper.strftime('%m/%d/%Y %I:%M:%S %p')
        #    win32file.WriteFile(pipe, auth_detail.encode())
        #for i,j in person_detail.items():
        #    if j == 10:
        #        win32file.WriteFile(pipe, str(i).encode())
                
        # if person has not been detected at all the empty out person_detail.
        
        person_detail = remove_old_items(person_detail)
        print('*******************',datetime.now().strftime('%m/%d/%Y %I:%M:%S %p %Z'))
        print_details(person_detail)
        
        #for i , j in person_detail.items():
        #    print('{0} {1} {2}'.format(i,j[0],j[1].strftime('%m/%d/%Y %I:%M:%S %p %Z')))
        
        
        time.sleep(1)
        count += 1     
        
        
        
        
        
    video.release()
    return pipe

if __name__ == '__main__':
    action = None
    if len(sys.argv) <= 1:
        print('Tell me what to do in argument!!!')
    else:
        action = sys.argv[1]
    
    if action == 'run':
        pipe = create_pipe()
        pipe = process_video_feed('input/1d4750c785cec00_KNC_6_DoorCamera_12345.mp4', pipe)
        close_pipe(pipe)
    
    if action == 'train':
        #pipe = create_pipe()
        #pipe = process_video_feed('input/1d4750c785cec00_KNC_6_DoorCamera_12345.mp4', pipe)
        #close_pipe(pipe)        
        print('Training Complete..')

    
    if action == 'enroll':
        #pipe = create_pipe()
        #pipe = process_video_feed('input/1d4750c785cec00_KNC_6_DoorCamera_12345.mp4', pipe)
        #close_pipe(pipe)        
        print('Enroll Complete. Please re-train..')