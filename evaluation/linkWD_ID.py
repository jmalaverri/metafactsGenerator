import pandas as pd
import re
from dboqueries import queryWdID

"""Update value variable fact: True|False(when MF) """
name = 'allnewMFgen' #allnewMFcons; allnewMFrestr; 'allnewFacts'
filename = 'results/%s.csv'%(name)

df = pd.read_csv(filename, sep='\t')
df = df.sort_values('subject')
print(len(df))
#print(df.keys())

def saveFiles(filename, data):
    df = pd.DataFrame.from_dict(data, orient='index')
    df.to_csv("results/wikID/%s"%(filename), sep='\t', encoding='utf-8')
    print('saved %s'%(filename), len(data))

last = 0
startFrom = 0
fileCounter = 0
batchsize = 5000
data = {}
fact = False #True: Facts; False: MF
idx = 0
c = 0
lim = 100000000
for _, row in df.iterrows():
    # In case of error continue until startFrom >= last printed
    last += 1    
    if last < startFrom:
        continue    
    #ids.append(queryWdID(row['subject'],row['object']))
    result, values = queryWdID(row['subject'],row['object'])
    if not result:
        continue
    
    sub, obj = values[0]['subID'], values[0]['objID']
    if fact:        
        data[idx] = {'id': row[1],
                     'subject': row['subject'], 'predicate': row['predicate'], 
                     'object': row['object'],
                     'subID': sub, 'objID': obj,
                     'mf_id': row['mf_id'],
                     'rule': row['rule'],
                     'Head Coverage': row['Head Coverage'],
                     'PCA Confidence': row['PCA Confidence']}
    else:
        data[idx] = {'id': row[1],
                     'subject': row['subject'], 'predicate': row['predicate'], 
                     'object': row['object'],
                     'subID': sub, 'objID': obj,
                     'inDateTime': row['inDateTime'],
                     'after': row['after'], 'before': row['before'],
                     'mf_id': row['mf_id'],
                     'rule': row['rule'],                     
                     'Confidence': row['Confidence'],
                     'Head Coverage': row['Head Coverage'],
                     'PCA Confidence': row['PCA Confidence']}
    idx += 1    
    if len(data) >= batchsize:
        print("last = %d"%(last), ': ', row['subject'], ',', row['object'])
        print("File counter: ", fileCounter)
        saveFiles('%s%d.csv'%('newMFgen',fileCounter), data)
        fileCounter += 1
        data = {}
    
    if c == 1000:
        print("Partial rows Processed", c)
     
    if c == lim:
        break    
    c += 1

saveFiles('newMFgenLast.csv', data)
# print(len(ids))
# df['subID'] = [x['subID'] for x in ids]
# df['objID'] = [x['objID'] for x in ids]
    
# df.to_csv("results/%s2.csv"%(name), sep='\t', encoding='utf-8')
# print('saved %s2.csv'%(name), len(df))
print("Processed rows: ", last)
print("Total c: ", c)