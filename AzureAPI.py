import cognitive_face as CF
import operator
from glob import iglob
import os
#
KEY = 'ce7bf170a154482ba9ef08a557467576'  # Replace with a valid Subscription Key here.
CF.Key.set(KEY)
#
BASE_URL = 'https://metfaceapi.cognitiveservices.azure.com/face/v1.0/'  # Replace with your regional Base URL
CF.BaseUrl.set(BASE_URL)
#
#img_url = 'https://raw.githubusercontent.com/Microsoft/Cognitive-Face-Windows/master/Data/detection1.jpg'
#result = CF.face.detect(img_url)
#print (result)
person_group_id =   'employee'

def start_training():
    global person_group_id
    
    r = CF.person_group.lists()
    #print(r)
    
    if person_group_id in [i['personGroupId'] for i in r]:
        print('{0} person group already exists..'.format(person_group_id))
    else:
        CF.person_group.create(person_group_id)    
        print('{0} person group created..'.format(person_group_id))
        
    final_folder = 'person_processed'
    
    efolders = [name for name in os.listdir(final_folder)]
    
    #r = CF.person.lists(person_group_id)
    #print(r)
    
    personIds = CF.person.lists(person_group_id)
    personId = [(person["name"], person['personId']) for person in personIds]
    #print(personId)
    
    for f in efolders:
        print('Enrolling {0}..'.format(f))
        for i, j in personId:
            if i == f:
                CF.person.delete(person_group_id,j)
        for filename in iglob(os.path.join(final_folder, f,'*.jpg'),recursive=False):
            #print(filename)
            res = CF.person.create(person_group_id, f)
            person_id = res['personId']
            CF.person.add_face(filename, person_group_id, person_id)
    
    CF.person_group.train(person_group_id)
    
    #r = CF.person.lists(person_group_id)
    #print(r)

def start_identify(file):
    personIds = CF.person.lists(person_group_id)
    personId = {person['personId']: person["name"] for person in personIds}
    #print(personId)
    
    res = CF.face.detect(file)
    #print(res)
    face_ids = [d['faceId'] for d in res]
    res = CF.face.identify(face_ids,person_group_id)
    #print(res)
    c = res[0]['candidates']
    candidates = {i['personId']:i['confidence'] for i in c}
    max_candidates = max(candidates.items(), key=operator.itemgetter(1))[0]
    print(personId[max_candidates], candidates[max_candidates])    

def delete_person_group(grps):
    global person_group_id
    for i in grps:
        res = CF.person.get(person_group_id,person_id[i])
    CF.person.lists(person_group_id)
    #personIds = CF.person.lists(person_group_id)
    #personId = [(person["name"], person['personId']) for person in personIds]
    #for i, j in personId:
    #    if i in grps:
    #        CF.person.delete(person_group_id,j)

def delete_group(grp_id):
    r = CF.person_group.lists()
    if grp_id in [i['personGroupId'] for i in r]:
        CF.person_group.delete(grp_id)
        print('{0} person group deleted'.format(grp_id))

        
if __name__ == '__main__':
    #personIds = CF.person.lists(person_group_id)
    #personId = {person['personId']: person["name"] for person in personIds}    
    #print(personId)
    #delete_person_group([128537,128538])
    delete_group(person_group_id)
    #start_training()
    #global person_group_id
    #start_identify('test1.jpg')
    

    
    
