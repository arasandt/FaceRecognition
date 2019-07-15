from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import tensorflow as tf
from scipy import misc
import cv2, math
import numpy as np
import classpkg.facenet as facenet
from PIL import ImageFont, Image, ImageDraw
import classpkg.detect_face as detect_face
import os
import time
import pickle

input_video="D:\\Arasan\\Misc\\GitHub\\VideoCapture\\MotionDetection\\Met1MDFEntrance.mp4.outpy.avi"
modeldir = './model/FaceNet_20180408-102900.pb'
classifier_filename1 = './model/SVCRBFclassifier.pkl'
classifier_filename2 = './model/SVCLinearclassifier.pkl'
classifier_filename3 = './model/SVCGammaclassifier.pkl'
npy='./model/'
train_img="./person"

class FrameC:
    oriframe = None
    modiframe = None
    modiflag = 0
    nrof_faces = 0
    def __init__():
        pass
    @classmethod
    def get_frame(self):
        return self.oriframe
    
with tf.Graph().as_default():
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.6)
    sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options, log_device_placement=False))
    with sess.as_default():
        pnet, rnet, onet = detect_face.create_mtcnn(sess, npy)

        minsize = 20  # minimum size of face
        threshold = [0.6, 0.7, 0.7]  # three steps's threshold
        factor = 0.709  # scale factor
        margin = 44
        frame_interval = 1
        batch_size = 1000
        image_size = 182
        input_image_size = 160
        
        HumanNames = os.listdir(train_img)
        HumanNames.sort()

        print('Loading Model')
        facenet.load_model(modeldir)
        images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
        embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
        phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
        embedding_size = embeddings.get_shape()[1]


        classifier_filename_exp1 = os.path.expanduser(classifier_filename1)
        classifier_filename_exp2 = os.path.expanduser(classifier_filename2)
        classifier_filename_exp3 = os.path.expanduser(classifier_filename3)
        with open(classifier_filename_exp1, 'rb') as infile1:
            (model1, class_names) = pickle.load(infile1)

        with open(classifier_filename_exp2, 'rb') as infile2:
            (model2, class_names) = pickle.load(infile2)

        with open(classifier_filename_exp3, 'rb') as infile3:
            (model3, class_names) = pickle.load(infile3)

        video_capture = cv2.VideoCapture(input_video)
        c = 0

        length = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_width = int(video_capture.get(3))
        frame_height = int(video_capture.get(4))
        print('Start Recognition')
        prevTime = 0
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        vout = cv2.VideoWriter(input_video + '.output.avi', fourcc, 25, (frame_width,frame_height))
        #x1 = [0,0,0,0]
        #x2 = None
        #x3 = None
        #x4 = 0
        while True:
            ret, frame = video_capture.read()
            
            if not ret:
                continue
            #else:
            #    vout.write(frame)
            #if ret:
            #    vout.write(frame)
            #    continue
            FrameC.oriframe = frame
            FrameC.modiframe = frame
            #frame = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)    #resize frame (optional)
            
            curTime = time.time() + 1    # calc fps
            timeF = frame_interval
            #x4 = 0
            nrof_faces = 0
            if (c % timeF == 0):
                find_results = []

                if frame.ndim == 2:
                    frame = facenet.to_rgb(frame)
                frame = frame[:, :, 0:3]
                save_frame = np.copy(frame)
                bounding_boxes, _ = detect_face.detect_face(frame, minsize, pnet, rnet, onet, threshold, factor)
                nrof_faces = bounding_boxes.shape[0]
                print('Detected_FaceNum: %d' % nrof_faces)
                FrameC.nrof_faces = nrof_faces
                if nrof_faces > 0:
                    det = bounding_boxes[:, 0:4]
                    img_size = np.asarray(frame.shape)[0:2]

                    cropped = []
                    scaled = []
                    scaled_reshape = []
                    bb = np.zeros((nrof_faces,4), dtype=np.int32)
                    for i in range(nrof_faces):
                        emb_array = np.zeros((1, embedding_size))

                        bb[i][0] = det[i][0]
                        bb[i][1] = det[i][1]
                        bb[i][2] = det[i][2]
                        bb[i][3] = det[i][3]

                        # inner exception
                        if bb[i][0] <= 0 or bb[i][1] <= 0 or bb[i][2] >= len(frame[0]) or bb[i][3] >= len(frame):
                            print('Face is very close!')
                            continue

                        cropped.append(frame[bb[i][1]:bb[i][3], bb[i][0]:bb[i][2], :])
                        try:
                            cropped[i] = facenet.flip(cropped[i], False)
                        except:
                            cv2.imwrite('Image.jpg', frame)
                            continue
                            
                        scaled.append(misc.imresize(cropped[i], (image_size, image_size), interp='bilinear'))
                        scaled[i] = cv2.resize(scaled[i], (input_image_size,input_image_size),
                                               interpolation=cv2.INTER_CUBIC)
                        scaled[i] = facenet.prewhiten(scaled[i])
                        scaled_reshape.append(scaled[i].reshape(-1,input_image_size,input_image_size,3))
                        feed_dict = {images_placeholder: scaled_reshape[i], phase_train_placeholder: False}
                        emb_array[0, :] = sess.run(embeddings, feed_dict=feed_dict)
                        
                        predictions1 = model1.predict_proba(emb_array)
                        best_class_indices1 = np.argmax(predictions1, axis=1)
                        best_class_probabilities1 = predictions1[np.arange(len(best_class_indices1)), best_class_indices1]
                        #print(predictions1)
                        #print(best_class_indices1,' with accuracy ',best_class_probabilities1)
                        
                        predictions2 = model2.predict_proba(emb_array)
                        best_class_indices2 = np.argmax(predictions2, axis=1)
                        best_class_probabilities2 = predictions1[np.arange(len(best_class_indices2)), best_class_indices2]
                        #print(predictions2)
                        #print(best_class_indices2,' with accuracy ',best_class_probabilities2)

                        predictions3 = model1.predict_proba(emb_array)
                        best_class_indices3 = np.argmax(predictions3, axis=1)
                        best_class_probabilities3 = predictions3[np.arange(len(best_class_indices3)), best_class_indices3]
                        #print(predictions3)
                        #print(best_class_indices3,' with accuracy ',best_class_probabilities3)
                        
                        best_class_probabilities = np.mean([best_class_probabilities1,best_class_probabilities2,best_class_probabilities3])
                        #best_class_indices = list({best_class_indices1[0][0],best_class_indices2[0][0],best_class_indices3[0][0]})
                        #print(type(best_class_indices1),best_class_indices1)
                        best_class_indices = set()
                        from collections import Counter
                        from operator import itemgetter
                        best_class_indices = Counter([best_class_indices1[0],best_class_indices2[0],best_class_indices3[0]])
                        best_class_indices = max(best_class_indices.items(), key=itemgetter(1))
                        #best_class_indices.add(best_class_indices1[0])
                        #best_class_indices.add(best_class_indices2[0])
                        #best_class_indices.add(best_class_indices3[0])
                        #best_class_indices = list(best_class_indices.counter)
                        #print(best_class_indices)
                        #x4 = best_class_probabilities
                        print(best_class_indices,' with accuracy ',best_class_probabilities)
                        if best_class_probabilities > 0.75:
                            cv2.rectangle(frame, (bb[i][0], bb[i][1]), (bb[i][2], bb[i][3]), (0, 255, 0), 2)    #boxing face
# =============================================================================
#                             x1[0] = bb[i][0]
#                             x1[1] = bb[i][1]
#                             x1[2] = bb[i][2]
#                             x1[3] = bb[i][3]
#                             
#                             x2 = best_class_indices
#                             x3 = best_class_probabilities
# =============================================================================
                            #plot result idx under box
                            text_x = bb[i][0]
                            text_y = bb[i][3] #+ 20
                            print('Result Indices: ', best_class_indices[0])
                            print(HumanNames)
                            for H_i in HumanNames:
                                if HumanNames[best_class_indices[0]] == H_i:
                                    result_names = str(HumanNames[best_class_indices[0]]) + ' ' + str(math.floor(best_class_probabilities * 100)) + '%'
                                    cv2_im_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                    pil_im = Image.fromarray(cv2_im_rgb)
                                    draw = ImageDraw.Draw(pil_im)
                                    font = ImageFont.truetype("arial.ttf", 10)
                                    w, h = font.getsize(result_names)
                                    draw.rectangle((text_x, text_y, text_x + w, text_y + h), fill='black')
                                    draw.text((text_x, text_y), result_names, font=font,fill=(255,255,255,255))
                                    frame = cv2.cvtColor(np.array(pil_im), cv2.COLOR_RGB2BGR)
                                    cv2.imwrite( input_video + '_ori_frames_' + str(c) + str(i) + "_.jpg", save_frame)
                                    cv2.imwrite( input_video + '_frames_' + str(c) + str(i) + "_.jpg", frame)
                                    #result_names = str(HumanNames[best_class_indices[0]]) + str(math.floor(best_class_probabilities * 100)) + '%'
                                    #cv2.putText(frame, result_names, (text_x, text_y),  cv2.FONT_HERSHEY_COMPLEX_SMALL, 
                                    #            1, (0, 0, 255), thickness=1,lineType=2)
                            FrameC.modiframe = frame
                            FrameC.modiflag = 1
                else:
                    print('Alignment Failure. No faced found.')
                #cv2.imshow('Video', frame)
                #if nrof_faces: 
                #    os.system("pause")
            else:
                pass #cv2.imshow('Video', frame)
# =============================================================================
#             elif x1[0] and x3 > 0.75:
#                 cv2.rectangle(frame, (x1[0], x1[1]), (x1[2], x1[3]), (0, 255, 0), 2)    #boxing face
#                 text_x = x1[0]
#                 text_y = x1[3] #+ 20
#                 for H_i in HumanNames:
#                     if HumanNames[x2[0]] == H_i:
#                         result_names = str(HumanNames[x2[0]]) + ' ' + str(math.floor(x3 * 100)) + '%'
#                         cv2_im_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#                         pil_im = Image.fromarray(cv2_im_rgb)
#                         draw = ImageDraw.Draw(pil_im)
#                         font = ImageFont.truetype("arial.ttf", 10)
#                         w, h = font.getsize(result_names)
#                         draw.rectangle((text_x, text_y, text_x + w, text_y + h), fill='black')
#                         draw.text((text_x, text_y), result_names, font=font,fill=(255,255,255,255))
#                         frame = cv2.cvtColor(np.array(pil_im), cv2.COLOR_RGB2BGR)
# =============================================================================
                #place boxing face there itself for all remaining frames
            if ret == True: 
                vout.write(FrameC.modiframe)
            if FrameC.modiflag == 1:
                cv2.imshow('Video', FrameC.modiframe)
                FrameC.modiflag = 0
            else:
                cv2.imshow('Video', FrameC.oriframe)
            print('{0} --> {1}'.format(c,length))
            
            #if x4: 
            #    os.system("pause")
            c += 1
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        vout.release()
        cv2.destroyAllWindows()
        
