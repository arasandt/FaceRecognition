import tensorflow as tf
import cv2
import classpkg.facenet as facenet
#import classpkg.detect_face as detect_face
import os
import numpy as np
import pickle

npy='./model/'
modeldir = './model/FaceNet_20180408-102900.pb'
classifier_filename = './model/SVCRBFclassifier.pkl'


def recognize_face(frame, i):
    #print(frame.shape)
    with tf.Graph().as_default():
        gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.6)
        sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options, log_device_placement=False))
        with sess.as_default():
            #pnet, rnet, onet = detect_face.create_mtcnn(sess, npy)
    
#            minsize = 20  # minimum size of face
#            threshold = [0.6, 0.7, 0.7]  # three steps's threshold
#            factor = 0.709  # scale factor
#            margin = 44
#            frame_interval = 3
#            batch_size = 1000
#            image_size = 182
            input_image_size = 160
            #HumanNames = os.listdir(train_img)
            #HumanNames.sort()
    
            print('Loading feature extraction model')
            facenet.load_model(modeldir)
    
            images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
            embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
            embedding_size = embeddings.get_shape()[1]
    
    
            classifier_filename_exp = os.path.expanduser(classifier_filename)
            with open(classifier_filename_exp, 'rb') as infile:
                (model, class_names) = pickle.load(infile)
            #print(frame.shape)    
            frame = facenet.prewhiten(frame)
            #print(frame.shape)    
            emb_array = np.zeros((1, embedding_size))
            
            frame_reshape = frame.reshape(-1,input_image_size,input_image_size,3)
            #frame_reshape = frame.copy()
            feed_dict = {images_placeholder: frame_reshape, phase_train_placeholder: False}
            emb_array[0, :] = sess.run(embeddings, feed_dict=feed_dict)
            predictions = model.predict_proba(emb_array)
            #print(predictions)
            best_class_indices = np.argmax(predictions, axis=1)            
            best_class_probabilities = predictions[np.arange(len(best_class_indices)), best_class_indices]
            #print(best_class_indices,' with accuracy ',best_class_probabilities, 'for ', str(i))
            best_class_probabilities
            #best_class_indices = [i for i in best_class_indices if i >= 0.80]
            if best_class_indices:
                if best_class_probabilities[0] > 0.75:
                    print(class_names[best_class_indices[0]])
                    return class_names[best_class_indices[0]]
            else:
                return None
            
            

if __name__ == '__main__':
    img = cv2.imread('61.jpg')
    x = recognize_face(img,0)
    print(x)
    
            