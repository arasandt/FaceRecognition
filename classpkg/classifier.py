from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import tensorflow as tf
import numpy as np
import classpkg.facenet as facenet
import os
import math
import pickle
from sklearn.svm import SVC  # support vector classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
#import sys


class training:
    def __init__(self, datadir, modeldir,classifier_filename):
        self.datadir = datadir
        self.modeldir = modeldir
        self.classifier_filename = classifier_filename

    def main_train(self):
        with tf.Graph().as_default():
            with tf.Session() as sess:
                img_data = facenet.get_dataset(self.datadir)  # gets list of classes for each label
                path, label = facenet.get_image_paths_and_labels(img_data) # return all image paths and labels in one continuous list
                print('Classes: %d' % len(img_data))
                print('Images: %d' % len(path))

                facenet.load_model(self.modeldir) # can load *.pb model or checkpoint / meta file into the current session
                images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0") # input into InceptionResNet
                embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0") # output 512-d vector 
                phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0") # input into each layer of InceptionResNet
                embedding_size = embeddings.get_shape()[1]  # earlier it was 128-d vector but now it is 512-d vector

                print('Extracting features of images for model')
                batch_size = 1000 # max # of training images you can give per label
                image_size = 160 # size of the face image 160 x 160
                nrof_images = len(path) # all images of all the labels
                nrof_batches_per_epoch = int(math.ceil(1.0 * nrof_images / batch_size))  # the more the batch_size the less the epoch would be
                emb_array = np.zeros((nrof_images, embedding_size)) # a 2-d array with image and its 512-d vector
                
                for i in range(nrof_batches_per_epoch): # for 200 images, this image will run only once
                    start_index = i * batch_size #  for 200 images, it will be 0
                    end_index = min((i + 1) * batch_size, nrof_images) #  for 200 images, it will be 200
                    paths_batch = path[start_index:end_index] # loading all images path to a batch. if more than 1000, then only 1000 will be loaded.
                    images = facenet.load_data(paths_batch, False, False, image_size) # returns images with its index values, its 160 image size 3-d vector with RGB channel as last dimension.
                    # images will contain all placeholder images with all its values with dimensions 160 x 160.
                    feed_dict = {images_placeholder: images, phase_train_placeholder: False} # pass images into input tensor with phase train as false. Phase train is for batch normalization. learn more on this.
                    emb_array[start_index:end_index, :] = sess.run(embeddings, feed_dict=feed_dict) # Confirm that this returns a inded and 512-d vector

                classifier_file_name = os.path.expanduser(self.classifier_filename)

                # Training Started
                print('Training Started')
                
                #model = RandomForestClassifier()  # learn more
                #model = SVC(kernel='linear', probability=True)  # learn more
                model = SVC(kernel='rbf', probability=True)  # learn more
                #model = SVC(gamma=2, C=1, probability=True)
                model.fit(emb_array, label) # use training on returned array with correpsonding labels.

                class_names = [cls.name.replace('_', ' ') for cls in img_data]  # the underscore in label names are replaced

                # Saving model
                with open(classifier_file_name, 'wb') as outfile:
                    pickle.dump((model, class_names), outfile) # save the fitted classifier and class names as a pickle file
                return classifier_file_name #
