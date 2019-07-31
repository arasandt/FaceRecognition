from __future__ import absolute_import
from __future__ import print_function

from glob import iglob

from utils import getFileTime
from datetime import timedelta, datetime
from dateutil import tz
import numpy as np

import win32pipe, win32file
import os, cv2, sys, time
import random
import base64

from extract_face import recognize_face

import pickle


from PIL import Image

data_retention = 10

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
    
    minimum_hit = 1
    
    def __init__(self, label_id):
        self.id = label_id
        self.time_keeper = None
        self.counter = 0
        self.displayed = False
        self.displayed_time = None
    
    def set_time(self, time_k):
        self.time_keeper = time_k.replace(tzinfo=tz.gettz('America/New_York'))
        self.time_keeper_fmt = self.time_keeper.strftime('%m/%d/%Y %I:%M:%S %p')
    
    def increment_count(self):
        self.counter += 1
    
    def assign_face(self,img, bb):
        self.face_img = img
        self.bb_box = bb


    def send_to_display(self, func, office, floor):
        if self.counter == self.minimum_hit:
            #img = cv2.imread('img2.png') 
            img = cv2.resize(self.face_img,(64,64))
            #height, width, depth = img.shape
            #img = np.array(img)
            #print(img.mean())
            img_as_bytes = pickle.dumps(img)
            #print(img_as_bytes)
            #print(type(img_as_bytes))
            #img_str = cv2.imencode('.png', img)[1].tostring()
            #print(img_str)   
            
            #auth_detail = func(self.id,office,floor) + '__' + self.time_keeper_fmt + '__' + str(width) + '__' + str(height) + '__' + str1
            auth_detail = func(self.id,office,floor) + '__' + self.time_keeper_fmt
            win32file.WriteFile(pipe, auth_detail.encode())
            win32file.WriteFile(pipe, img_as_bytes)
            self.displayed = True
            self.displayed_time = datetime.now().replace(tzinfo=tz.gettz('America/New_York'))
      
        

def create_pipe():
    print('Connecting to Display..')
    pipe = win32pipe.CreateNamedPipe(r'\\.\pipe\Foo',
                                     win32pipe.PIPE_ACCESS_DUPLEX,
                                     win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                                     1, 65536, 65536,0,None)
    win32pipe.ConnectNamedPipe(pipe, None)
    
    return pipe

def close_pipe(pipe):
    win32file.CloseHandle(pipe)


def print_details(person_detail):
    for i,j in person_detail.items():
        n = datetime.now().replace(tzinfo=tz.gettz('America/New_York'))
        if j.displayed_time is not None:
            secs = n - j.displayed_time        
            print('{0} {1} expiring in {2} sec..'.format(i,j.counter,int(data_retention - secs.total_seconds())))      
        else:
            secs = n         
            print('{0} {1}'.format(i,j.counter))            
    
    
def remove_old_items(person_detail):
    remove = []
    for i,j in person_detail.items():
            n = datetime.now().replace(tzinfo=tz.gettz('America/New_York'))
            now = n - timedelta(seconds=data_retention)
            if j.displayed_time is not None:
                if j.displayed_time >= now:
                    pass
                else:
                    remove.append(i)
    
    [person_detail.pop(i) for i in remove]
    return person_detail     
        


def expand_bb(bb, shp, percentage=0.25):
    
    wpadding = int(bb[3] * percentage) # 25% increase
    hpadding = int(bb[2] * percentage)

    det = [0,0,0,0]
    det[0] = max(bb[0] - wpadding, 0)
    det[1] = max(bb[1] - hpadding,0)
    det[2] = min(bb[2] + bb[0] + wpadding,shp[1])
    det[3] = min(bb[3] + bb[1] + hpadding,shp[0])
    
    return det


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
    from mtcnn.mtcnn import MTCNN
    detector = MTCNN()
    
    while True:
        (ret, frame) = video.read()
        
        if not ret:
            break
        
            
        # send frame for face detection and recognition
        bb_box = detector.detect_faces(frame)
        bb_box = [i for i in bb_box if i['confidence'] >= 0.9 ]
        #print(bb_box)
            
        nrof_faces = len(bb_box)
        
        face_box = []
        cropped_image = []
        
        if nrof_faces > 0:
            for i in range(nrof_faces):
                bb = bb_box[i]['box']
                
                det = expand_bb(bb, frame.shape, percentage=0)
                
                orig_image = frame[det[1]:det[3], det[0]:det[2]].copy()

                #det = expand_bb(bb, frame.shape, percentage=0.25)
                det = expand_bb(bb, frame.shape, percentage=0)
                
                face_box.append(det)
                
                cropped_image.append(frame[det[1]:det[3], det[0]:det[2]].copy())
                
                
                #cv2.rectangle(frame, (det[0], det[1]), (det[2], det[3]), (0, 255, 0), 2)
                
                #cropped_images.append(frame[bb[1]:bb[1]+bb`[3], bb[0]:bb[0]+bb[2]].copy())
                #cv2.rectangle(frame, (max(bb[0]-wpadding,0), max(bb[1]-hpadding,0)), (min(bb[0] + bb[2] + wpadding,frame.shape[1]), min(bb[1] + bb[3] + hpadding,frame.shape[0])), (0, 255, 0), 2)
                
                #print(orig_image.shape)
                orig_image = cv2.resize(orig_image,(160,160))
                #print(orig_image.shape)
                label_id = recognize_face(orig_image, i)
                # get label of persons identified and details
                
                #time.sleep(10)
            

            
                #######label_id = random.randint(128537,128538)
                if label_id is not None:
                    if person_detail.get(label_id, 0) == 0:
                        person_detail[label_id] = Person_Details(label_id)
                    
                    person_detail[label_id].increment_count()
                    person_detail[label_id].assign_face(cropped_image[i], bb)
                    person_detail[label_id].set_time(datetime.now())
        
                    if not person_detail[label_id].displayed:
                        person_detail[label_id].send_to_display(check_auth, office, floor)
          
            person_detail = remove_old_items(person_detail)
            print('*******************',datetime.now().strftime('%m/%d/%Y %I:%M:%S %p %Z'))
            print_details(person_detail)
        
        for i, det in enumerate(face_box):
            cv2.rectangle(frame, (det[0], det[1]), (det[2], det[3]), (0, 255, 0), 2)
            text_x = det[0]
            text_y = det[3] + 20            
            cv2.putText(frame, str(i), (text_x, text_y), cv2.FONT_HERSHEY_COMPLEX_SMALL,1, (0, 0, 255), thickness=1, lineType=2)            
        
        cv2.imshow('Image', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            sys.exit()        
        #time.sleep(1)
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
        
        from classpkg.classifier import training
        
        datadir = './person_processed'
        modeldir = './model/FaceNet_20180408-102900.pb'
        classifier_filename = './model/SVCRBFclassifier.pkl'
        
        print ("Training Start")
        
        obj=training(datadir,modeldir,classifier_filename)
        
        get_file=obj.main_train() # # create new classifier after training with the input images
        
        print('Saved classifier model to file {0}'.format(get_file))
        
        # code
        print('Training Complete..')

    if action == 'enroll':
        
        enroll_folder = 'person'    
        final_folder = 'person_processed'

        ffolders = [name for name in os.listdir(final_folder)]
        efolders = [name for name in os.listdir(enroll_folder) if name not in ffolders]
        
        if efolders:
            for f in efolders:
                print('Enrolling {0}..'.format(f))
                for filename in iglob(os.path.join(enroll_folder, f,'*.jpg'),recursive=False):
                    #print(filename)
                    im = cv2.imread(filename)
                    
                    from mtcnn.mtcnn import MTCNN
                    detector = MTCNN()                    
                    
                    box = detector.detect_faces(im)
                    box = [i for i in box if i['confidence'] >= 0.9 ]
                    if box:
                        bb = box[0]['box']
                        det = expand_bb(bb, [9999,9999], 0)
                        ex_img = im[det[1]:det[3], det[0]:det[2]].copy()
                        ex_img = cv2.resize(ex_img, (160,160),interpolation=cv2.INTER_CUBIC)
                        cv2.imwrite(filename + '_mtcnn',ex_img)
                    
        
            for f in efolders:
                import shutil
                shutil.move(os.path.join(enroll_folder,f), os.path.join(final_folder,f))
        
            print('Enrollment Complete. Please re-train..')
        else:
            print('No new enrollment found..')
                
        
        
        
        
        
        