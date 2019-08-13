from __future__ import absolute_import
from __future__ import print_function

import random


import cognitive_face as CF
KEY = 'ce7bf170a154482ba9ef08a557467576'  # Replace with a valid Subscription Key here.
CF.Key.set(KEY)
BASE_URL = 'https://metfaceapi.cognitiveservices.azure.com/face/v1.0/'  # Replace with your regional Base URL
CF.BaseUrl.set(BASE_URL)
person_group_id =   'employee'



from glob import iglob
import operator
from utils import getFileTime
from datetime import timedelta, datetime
from dateutil import tz
import numpy as np
import collections 

import win32pipe, win32file
import os, cv2, sys, time
import random
import base64

from extract_face import recognize_face

import pickle

person_detail = {}

from PIL import Image

hits_window_size = 50 # (fps * 2 secs)
hits_required =  hits_window_size * 0.20 #(20% of window size should have good hits)
cool_time = timedelta(seconds=10)
retention_time = timedelta(seconds=5)
label_size = 150
picture_size = 100
decision_size = 50
each_row_size = 100
unknown_size = 100

def check_auth(label_id, office, floor):
    label_id = str(label_id)
    office = str(office)
    floor = str(floor)
    
    authorized = {'128537': ['Active','KNC', '6'],
                  '128538': ['InActive','KNC', '6'],
                  '128539': ['Active','CKC', '6'],
                  '128540': ['Active','KNC', '5',],
                  }
    
    msg = ['Welcome..','Not Authorized', 'Not Authorized for entry into ','Not Authorized for entry into floor ']
    
    if label_id in authorized.keys():
        if authorized[label_id][0] == 'Active':
            if authorized[label_id][1] == office:
                if authorized[label_id][2] == floor:
                    ret_msg = msg[0]
                else:
                    ret_msg = msg[3] + office + ' # ' + floor
            else:
                ret_msg = msg[2] + office
        else:
            ret_msg = msg[1] 
    else:
        ret_msg = msg[1] 
    return label_id + '_' + ret_msg
    

class Person_Details():
    
    
    
    def __init__(self, label_id):
        self.id = label_id
        self.time_keeper = None
        self.counter = 0
        self.window = collections.deque([], hits_window_size)
        self.cool_off_time = None
        self.display = 0
        self.display_time = None
        self.confidence = 0
        #self.displayed = False
        #self.displayed_time = None
    
    def set_time(self, time_k):
        self.time_keeper = time_k.replace(tzinfo=tz.gettz('America/New_York'))
        self.time_keeper_fmt = self.time_keeper.strftime('%m/%d/%Y %I:%M:%S %p')
        
    
    def increment_count(self):
        self.counter += 1
    
    def assign_face(self,img, bb, confidence):
        if confidence > self.confidence:
            self.face_img = img
            self.bb_box = bb
            self.confidence = confidence

    def add_label(self, label_id):
        #print('In Label')
        if self.cool_off_time is None or self.time_keeper > self.cool_off_time:
            self.window.append((self.id, label_id))
            #print(self.window)
            if label_id == self.id:
                #print('Incrementing Count')
                self.increment_count()
                self.counter
            
    def reset(self):
        self.counter = 0
        self.display = 1
        self.display_time = self.time_keeper
        self.window = None
        self.window = collections.deque([], hits_window_size)
        self.cool_off_time = self.display_time + cool_time

      
        

    

#
#def close_pipe(pipe):
#    win32file.CloseHandle(pipe)


#def print_details(person_detail):
#    for i,j in person_detail.items():
#        n = datetime.now().replace(tzinfo=tz.gettz('America/New_York'))
#        if j.displayed_time is not None:
#            secs = n - j.displayed_time        
#            print('{0} {1} expiring in {2} sec..'.format(i,j.counter,int(data_retention - secs.total_seconds())))      
#        else:
#            secs = n         
#            print('{0} {1}'.format(i,j.counter))            
    
#    
#def remove_old_items(person_detail):
#    remove = []
#    for i,j in person_detail.items():
#            n = datetime.now().replace(tzinfo=tz.gettz('America/New_York'))
#            now = n - timedelta(seconds=data_retention)
#            if j.displayed_time is not None:
#                if j.displayed_time >= now:
#                    pass
#                else:
#                    remove.append(i)
#    
#    [person_detail.pop(i) for i in remove]
#    return person_detail     
#        


def expand_bb(bb, shp, percentage=0.25):
    
    wpadding = int(bb[3] * percentage) # 25% increase
    hpadding = int(bb[2] * percentage)

    det = [0,0,0,0]
    det[0] = max(bb[0] - wpadding, 0)
    det[1] = max(bb[1] - hpadding,0)
    det[2] = min(bb[2] + bb[0] + wpadding,shp[1])
    det[3] = min(bb[3] + bb[1] + hpadding,shp[0])
    
    return det


def process_video_feed(filename):
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
    #from mtcnn.mtcnn import MTCNN
    #detector = MTCNN()
    
    length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(video.get(cv2.CAP_PROP_FPS))
    frame_width = int(video.get(3))
    frame_height = int(video.get(4))
    
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    vout = cv2.VideoWriter(filename + '.output.avi', fourcc, fps, (frame_width + label_size + picture_size + decision_size + unknown_size, frame_height))
    
    unknown_faceIds = []
    unknown_frame_copy = None
    random.seed(9001)
    
    while True:
        (ret, frame) = video.read()
        
        if not ret:
            break
        
        print('{0}_{1}'.format(count,length), end='\r')
        
#        if count < 36:
#            count += 1
#            continue
#            
#        (h, w) = frame.shape[:2]
#        center = (w / 2, h / 2)
#         
#        angle = 270
#        scale = 1.0
#         
#        # Perform the counter clockwise rotation holding at the center
#        # 90 degrees
        #frame=cv2.transpose(frame)
        #frame=cv2.flip(frame,flipCode=1)    
        # send frame for face detection and recognition
        file = 'temp.jpg'
        cv2.imwrite(file,frame)
        res = CF.face.detect(file)
        #bb_box = detector.detect_faces(frame)
        #bb_box = [i for i in bb_box if i['confidence'] >= 0.9 ]
        #print(bb_box)
        #print(res)
        face_ids = {d['faceId']:d['faceRectangle'] for d in res}
        nrof_faces = len(face_ids.keys())
        #print(face_ids)
        personIds = CF.person.lists(person_group_id)
        personId = {person['personId']: person["name"] for person in personIds}  


        def getRectangle(rect, shp,percentage=0.25):#faceDictionary):
            #rect = faceDictionary['faceRectangle']
            wpadding = int(rect['width'] * percentage) # 25% increase
            hpadding = int(rect['height'] * percentage)
        
            det = [0,0,0,0]
            det[0] = max(rect['left'] - wpadding, 0)
            det[1] = max(rect['top'] - hpadding,0)
            det[2] = min(rect['height'] + rect['left'] + wpadding,shp[1])
            det[3] = min(rect['width'] + rect['top'] + hpadding,shp[0])

            return det

    

        cropped_image = []
        face_box = []
        
        if face_ids:
            face_res = CF.face.identify(list(face_ids.keys()),person_group_id)
            #print(face_res)
            for i, f in enumerate(face_ids.keys()):
                label_id = None
                confidence = 0
                candidates = {x['personId']:x['confidence'] for x in face_res[i]['candidates']}
                #print(candidates)
                if candidates:
                    max_candidates = max(candidates.items(), key=operator.itemgetter(1))[0]
                    if candidates[max_candidates] > 0.50 :
                        label_id = personId[max_candidates]
                        confidence = candidates[max_candidates]            
                #det = expand_bb(face_ids[f], frame.shape, percentage=0.25)
                #det = face_ids[f]
                #cropped_image.append(frame[det[1]:det[3], det[0]:det[2]].copy())
                #face_box.append((det,label_id, confidence))
                
                det = getRectangle(face_ids[f],frame.shape, percentage=0.5)
                cropped_image.append(frame[det[1]:det[3], det[0]:det[2]].copy())
                #print(det, frame.shape)
                face_box.append((det,label_id, confidence))
                #cv2.rectangle(frame, (det[0], det[1]), (det[2], det[3]), (0,255,0), 2)
                if label_id is not None:
                    if person_detail.get(label_id, 0) == 0:
                        person_detail[label_id] = Person_Details(label_id)
                    
                    person_detail[label_id].assign_face(cropped_image[i], det, confidence)
                    person_detail[label_id].set_time(timestamp + timedelta(seconds=(count // fps)))                
                else:
                    unknown_faceIds.append((f,cropped_image[i],det))
                    #cv2.imwrite(f + '.jpg', cropped_image[i])
#                    color = (255,0,255)
#                    cv2.rectangle(frame, (det[0], det[1]), (det[2], det[3]), color, 2)
       
        
        for person in person_detail.keys():
            if person in [j for i,j,k in face_box]:
                person_detail[person].add_label(person)
            else:
                person_detail[person].add_label(None)
        
        unknown_face = []
        find_face = []
        
        
        if len(unknown_faceIds) >= (3 * 25): # 3 seconds * 25 fps
            get_face = [i for i, j, k in unknown_faceIds]
            unknown_face = CF.face.group(get_face)
            print('Found ',len(unknown_face['groups']), 'unknown groups')
            percentage = [len(i) / (3 * 25) for i in unknown_face['groups']]
            #print(percentage)
            percentage = [cnt for cnt, i in enumerate(percentage) if i > 0.80]
            print('Found ',len(percentage), 'unknown groups with confidence')
            for i in percentage:
                x = random.randint(1,len(unknown_face['groups'][i]))
                find_face.append(unknown_face['groups'][i][x])
                x = random.randint(1,len(unknown_face['groups'][i]))
                find_face.append(unknown_face['groups'][i][x])
                x = random.randint(1,len(unknown_face['groups'][i]))
                find_face.append(unknown_face['groups'][i][x])
        #else if unknown_frame_copy is not None:
            
            #print(find_face)
            #break
        
        
        #unknown_faceIds = unknown_faceIds[-3:]
#        unknown_face = {}
#        if len(unknown_faceIds) > 1:
#            get_face = [i for i, j in unknown_faceIds]
#            unknown_face = CF.face.group(get_face)
#            #print('\n',len(unknown_face['groups']),'\n')
#            print(unknown_face['groups'])

        # did anybody reach hits required
        for person in list(person_detail.keys()):
            #print('{0},{1}'.format(person, person_detail[person].counter))
            if person_detail[person].counter == hits_required:
                print('{1} Identified ----> {0}'.format(person, person_detail[person].time_keeper_fmt))
                person_detail[person].reset()
            try:
                if timestamp + timedelta(seconds=(count // fps)) - person_detail[person].display_time > retention_time:
                    person_detail.pop(person, None)   
                    print('{1} Removed    ----> {0}'.format(person,  person_detail[person].time_keeper_fmt))
            except:
                pass
       
        (h, w) = frame.shape[:2]
        label_frame = np.zeros((h, label_size, 3), dtype=np.uint8)        
        picture_frame = np.zeros((h, picture_size, 3), dtype=np.uint8)
        decision_frame = np.zeros((h, decision_size, 3), dtype=np.uint8)
        unknown_frame = np.zeros((h, unknown_size, 3), dtype=np.uint8)
        #unknown_frame_copy = np.zeros((h, unknown_size, 3), dtype=np.uint8)
        
        label_frame.fill(255)
        picture_frame.fill(255)
        decision_frame.fill(255)
        unknown_frame.fill(255)
        #unknown_frame_copy.fill(255)
        
        #row_gap = 10
        
        
        
        if find_face:
            for a, i in enumerate(find_face):
                last_img = [y for x, y, z in unknown_faceIds if x == i][0]
                #print(type(last_img),last_img)
                #last_img = CF.face.group(last_img)
                #print(type(last_img))
            #for a, grps in enumerate(unknown_face['groups']):
            #    last_id = grps[-1] 
            #    last_img = [y for x, y in unknown_faceIds if x == last_id][0]
                y_offset = a * each_row_size
                img_dis = cv2.resize(last_img,(each_row_size,unknown_size))
                rows,cols,_ = img_dis.shape
                unknown_frame[y_offset:y_offset + rows,:] = img_dis    
            unknown_faceIds = []
            unknown_frame_copy = unknown_frame.copy()
            find_face = []
        elif unknown_frame_copy is not None:
            unknown_frame = unknown_frame_copy.copy()
#        for x, y in enumerate(unknown_faceIds):
#            id, face = y
#            y_offset = x * each_row_size
#            img_dis = cv2.resize(face,(each_row_size,unknown_size))
#            rows,cols,_ = img_dis.shape
#            unknown_frame[y_offset:y_offset + rows,:] = img_dis    
        
        i = 0    
        
        for person in person_detail.keys():
        
            if person_detail[person].display:
                #x_offset = 0 #row_gap
                y_offset = i * each_row_size
                decision_frame[y_offset:y_offset + each_row_size,:] = np.full([each_row_size,decision_size,3],[0,255,0],dtype=np.uint8)
                
                img_dis = cv2.resize(person_detail[person].face_img,(each_row_size,picture_size))
                rows,cols,_ = img_dis.shape
                picture_frame[y_offset:y_offset + rows,:] = img_dis
                
                cv2.putText(label_frame, str(person) , (10, y_offset + each_row_size // 2 ), cv2.FONT_HERSHEY_COMPLEX_SMALL,1, (0, 0, 0), thickness=1, lineType=2) 
                

                
                
#                cv2.putText(label_frame, str(person) , (0, i * (label_size + row_gap) + row_gap * 4), cv2.FONT_HERSHEY_COMPLEX_SMALL,1, (255, 255, 255), thickness=1, lineType=2) 
#                img_dis = cv2.resize(person_detail[person].face_img,(int(picture_size * 1), int(picture_size * 1)))
#                
#                rows,cols,_ = img_dis.shape
#
#                x_offset = 0 #row_gap
#                y_offset = i * (picture_size + row_gap) + row_gap 
#                picture_frame[y_offset:y_offset+rows, x_offset: x_offset+cols] = img_dis
#                
#                
#                color_img = np.full([rows,int(picture_size * decision_size),3],[0,255,0],dtype=np.uint8)
#                rows,cols,_ = color_img.shape
#                print(rows,cols)
#                
#                #img_dis = np.full([int(decision_size[0] * 0.75),int(decision_size[1] * 0.75),3],[0,255,0],dtype=np.uint8)
#                #rows,cols,_ = img_dis.shape
#                
#                x_offset = row_gap
#                y_offset = i * (int(picture_size * decision_size) + row_gap)  + row_gap
#                print(x_offset,y_offset)
#                decision_frame[y_offset:y_offset+rows, x_offset: x_offset+cols] = color_img
                
                i += 1
                
                
                #cv2.imshow('Image', np.hstack((picture_frame, label_frame, decision_frame, unknown_frame)))

                
        for det, lab, confi in face_box:
            color = (0,0,255)             
            if lab is None:
                cv2.rectangle(frame, (det[0], det[1]), (det[2], det[3]), color, 2)        
                text_x = det[0]
                text_y = det[3] + 20            
                cv2.putText(frame, 'Unknown', (text_x, text_y), cv2.FONT_HERSHEY_COMPLEX_SMALL,1, color, thickness=1, lineType=2)            
                
        #cv2.imshow('Image',cv2.resize(frame, (500,500)))
        
        final_frame = np.hstack((frame, decision_frame, picture_frame, label_frame, unknown_frame))
        from win32api import GetSystemMetrics
        width = GetSystemMetrics(0)
        height = GetSystemMetrics(1)        
        cv2.imshow("Show by CV2",cv2.resize(final_frame, (int(width*0.75),int(height*0.75))))
        vout.write(final_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            sys.exit()           
        
        count += 1
        continue
            

        
        
        
        
    vout.release()        
    video.release()


if __name__ == '__main__':
    action = None

    if len(sys.argv) <= 1:
        print('Tell me what to do in argument!!!')
    else:
        action = sys.argv[1]
    
    if action == 'run':
        #pipe = create_pipe()
        #pipe = None
        process_video_feed('input/1d4750c785cec00_KNC_6_DoorCamera_12349.mp4')
        #close_pipe(pipe)

    
    if action == 'delete':
        r = CF.person_group.lists()
        if person_group_id in [i['personGroupId'] for i in r]:
            CF.person_group.delete(person_group_id)
            print('{0} person group deleted'.format(person_group_id))    
            
    
    if action == 'list':
        personIds = CF.person.lists(person_group_id)
        personId = {person["name"] for person in personIds}
        print(person_group_id , personId)
            

    if action == 'enroll':

        final_folder = 'person_processed'
        
        r = CF.person_group.lists()
        
        if person_group_id in [i['personGroupId'] for i in r]:
            print('{0} person group already exists..'.format(person_group_id))
        else:
            CF.person_group.create(person_group_id)    
            print('{0} person group created..'.format(person_group_id))
            
        efolders = [name for name in os.listdir(final_folder)]
        
        personIds = CF.person.lists(person_group_id)
        personId = [(person["name"], person['personId']) for person in personIds]
        personname = {person["name"] for person in personIds}
        
        for f in efolders:
            
            if f in personname:
                print('{0} already enrolled..'.format(f))
                continue
            else:
                pass
                
            print('Enrolling {0}..'.format(f))
                #for i, j in personId:
            #    if i == f:
            #        CF.person.delete(person_group_id,j)
            for filename in iglob(os.path.join(final_folder, f,'*.jpg'),recursive=False):
                res = CF.person.create(person_group_id, f)
                person_id = res['personId']
                CF.person.add_face(filename, person_group_id, person_id)
        
        CF.person_group.train(person_group_id)        
                
        
        
        
        
        
        
