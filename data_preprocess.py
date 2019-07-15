from classpkg.preprocess import preprocesses

input_datadir = './person'
output_datadir = './person_processed'

obj=preprocesses(input_datadir,output_datadir) # initialize
nrof_images_total,nrof_successfully_aligned=obj.collect_data()  

print('Total number of images: %d' % nrof_images_total)
print('Number of successfully aligned images: %d' % nrof_successfully_aligned)



