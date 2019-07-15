from __future__ import absolute_import # will find standard library version first using absolute imports rather relative imports.
from __future__ import division # will use truediv for division
from __future__ import print_function # enables python 2.7 print to work in python 3
import sys
from classpkg.classifier import training

datadir = './person_processed'   # location of the processed input images
modeldir = './model/FaceNet_20180408-102900.pb' # location of the pre-trained model
classifier_filename = './model/SVCRBFclassifier.pkl' # location of the trained classifier
print ("Training Start")
obj=training(datadir,modeldir,classifier_filename) 
get_file=obj.main_train() # # create new classifier after training with the input images
print('Saved classifier model to file "%s"' % get_file)
sys.exit("All Done")
