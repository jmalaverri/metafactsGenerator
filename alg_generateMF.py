# coding: utf-8
import pandas as pd
import pickle as pkl
import gzip as gz
from datehandler import *
#from kbqueries import *
from dboqueries import *

f = gz.open('metafacts.pkl.gz','rb')
all_metafacts, idx2o, idx2p, p2idx  = pkl.load(f)
f.close()
print("Number of metafact files: ", len(all_metafacts))


# ## Loading rules
rules = pd.read_csv('rules.csv', sep='\t')
print("Number of rules: ", len(rules))

rules['Head Coverage'] = rules['Head Coverage'].str.replace(',', '.').astype(float)
rules['PCA Confidence'] = rules['PCA Confidence'].str.replace(',', '.').astype(float)

#separate body and header
new = rules["Rule"].str.split("=>", n = 1, expand = True)

#making seperate body column from new data frame 
rules["Body"]= new[0] 

#making seperate header column from new data frame 
rules["Header"]= new[1]


# In[7]:

premises = rules['Body'].str.split(expand=True)
n_temp = len(premises.columns)
num_atoms = n_temp // 3 # 3 means number of elements in an atom; subject, predicate, object = 3 elements
for i in range(num_atoms):
    rules['s%d'%(i)] = premises[i*3]
    rules['p%d'%(i)] = premises[i*3+1].str[1:-1]
    rules = rules.replace({'p%d'%(i): p2idx})
    rules['o%d'%(i)] = premises[i*3+2]


# In[8]:


for _, v in rules[:3].iterrows():
    for i in range(num_atoms):
        print(v['s%d'%(i)], v['p%d'%(i)], v['o%d'%(i)], end=', ')
    print('')


# In[9]:


premises = rules['Header'].str.split(expand=True)
rules['sh'] = premises[0]
rules['ph'] = premises[1].str[1:-1]
rules['oh'] = premises[2]
rules = rules.replace({'ph': p2idx})


# ## Algorithm

# ### Query propagated header and add new fact and new metafact

# In[10]:



hastimestamp = {'actedIn', 'directed', 'wroteMusicFor', 'created',
                'participatedIn', 'hasChild', 'edited'}
hastimeinterval = {'worksAt', 'isPoliticianOf', 'graduatedFrom', 'isMarriedTo',
                   'playsFor', 'isLeaderOf', 'owns', 'isAffiliatedTo', 'holdsPoliticalPosition','hasAcademicAdvisor', 'isKnownFor'}


allnew_MF_cons = set()
allnew_MF_restr = set()

# In[11]:

def Log(logfile, text):
    logfile.write('%s\n'%(text))
    logfile.flush()
    
G, C, R = 0, 1, 2

def distDates(a, b):
    A = str2date(a)
    B = str2date(b)
    dist = abs((A - B).days)/365
    return dist

def calcS2(numAtomsMatched, body):
    if numAtomsMatched == 1:
        return 1
    if len(body) == 1 or body[0]['type'] == '' or body[1]['type'] == '':
        return 1
    if body[0]['type'] == 'ts' and body[1]['type'] == 'ts':
        d = (1+distDates(body[0]['ts'], body[1]['ts']))
    elif body[0]['type'] == 'ts' and body[1]['type'] == 'ti':
        d = (distDate(body[0]['ts'], body[0]['ti'][0]) + distDate(body[0]['ts'], body[0]['ti'][1]))/2
    elif body[0]['type'] == 'ti' and body[1]['type'] == 'ts':
        d = (distDate(body[1]['ts'], body[0]['ti'][0]) + distDate(body[1]['ts'], body[0]['ti'][1]))/2
    else:
        d = (distDate(body[1]['ti'][0], body[0]['ti'][0]) + distDate(body[1]['ti'][1], body[0]['ti'][1]))/2

    return 1 / (1+d)

def processNewHeader(metafact, rule, s, o, new_facts, new_MF_gen, new_MF_cons, new_MF_restr,
                     atom1, item=None, query_predicate=None, numAtomsMatched=1):
    p         = rule['ph']
    subject   = idx2o[s] if s in idx2o else s
    predicate = idx2p[p] if p in idx2p else p
    obj       = idx2o[o] if o in idx2o else o
    
    mfsubject   = idx2o[metafact['subject']] if metafact['subject'] in idx2o else metafact['subject']
    mfpredicate = idx2p[metafact['predicate']] if metafact['predicate'] in idx2p else metafact['predicate']
    mfobj       = idx2o[metafact['object']] if metafact['object'] in idx2o else metafact['object']
    
    logtext = '%s %s %s %s\n  %s\n  %s %s %s\n  '%(metafact['id'], mfsubject, mfpredicate, mfobj,
                              rule['Rule'], subject, predicate, obj)
    
    if query_predicate:
        if query_predicate in hastimestamp:
            r2 = getRangeFromItem(item)
            atom2 = {'predicate': query_predicate, 'type': 'ts', 'ts': r2[0]}
        elif query_predicate in hastimeinterval:
            r2 = getRangeFromItem(item)
            if (r2[1] == '-' and r2[0] == '-') or (r2[1] == None and r2[0] == None):
                atom2 = {'predicate': query_predicate, 'type': ''}
            elif r2[1] == '-' or r2[1] == None:
                atom2 = {'predicate': query_predicate, 'type': 'ts', 'ts': r2[0]}
            elif r2[0] == '-' or r2[0] == None:
                atom2 = {'predicate': query_predicate, 'type': 'ts', 'ts': r2[1]}
            else:    
                atom2 = {'predicate': query_predicate, 'type': 'ti', 'ti': r2}
        else:
            atom2 = {'predicate': query_predicate, 'type': ''}
        body = [atom1, atom2]
    else:
        body = [atom1]
    logtext += '%s'%(body)

    if len(body) > 1:
        if body[0]['type'] == '' or body[1]['type'] == '':
            return
        
    if body[0]['type'] == '':
        return        
    
    tipo, ts, ti = handleDates(body, predicate, 'conservative')
    
    in_date_time = ts if ts != None and ts != "" else '-'
    after = ti[0] if ti != None and ti[0] != "" else '-'
    before = ti[1] if ti != None and ti[1] != "" else '-'

    if not (isinstance(in_date_time, str) and isinstance(after, str) and isinstance(before, str)):
        print(mfsubject, mfpredicate, mfobj, in_date_time, after, before)
        return
    if not (isValidDate(in_date_time) and isValidDate(after) and isValidDate(before)):
        return
    
    logtext1 = '%s %s %s %s'%(logtext, in_date_time, after, before)
    if [in_date_time, after, before] == ['-']*3:
        return
        
    new_idx = '%s%s%s%s%s%s'%(subject,predicate,obj,in_date_time,after,before)

    # check if new metafact is already present among the metafacts!!
    if not new_idx in allnew_MF_cons and (not predicate in all_metafacts or not new_idx in all_metafacts[predicate].index):
        allnew_MF_cons.add(new_idx)
        new_fact_idx = '%s%s%s'%(subject,predicate,obj)

        if not queryKB(subject, predicate, obj) and not new_fact_idx in new_facts:
            new_facts[new_fact_idx] = {'subject': subject, 'predicate': predicate, 'object': obj,
                                       'mf_id': metafact['id'],
                                       'rule': rule['Rule'],
                                       'Head Coverage': rule['Head Coverage'],
                                       'PCA Confidence': rule['PCA Confidence']}
            Log(factlogfile, 'Saved\t%s\t%s\t%s\t%s\t%s\t%s\t'%(rule['Rule'], rule['PCA Confidence'], rule['Head Coverage'],
                                                                subject, predicate, obj))
        else:
            Log(factlogfile, 'Not saved\t%s\t%s\t%s\t%s\t%s\t%s\t'%(rule['Rule'], rule['PCA Confidence'], rule['Head Coverage'],
                                                                    subject, predicate, obj))
            

        natom = 0
        keep = True
        while keep:
            s = 's%d'%(natom)
            o = 'o%d'%(natom)
            keep = s in rule and rule[s] != None and rule[o] != None
            if keep:
                natom += 1
        s1 = numAtomsMatched/natom
        s2 = calcS2(numAtomsMatched, body)
        # DONE find s1 and s2 
        conf = (rule['Head Coverage']+rule['PCA Confidence']+s1+s2)/4
        if tipo == G:
            new_MF_gen[new_idx] = {'subject': subject, 'predicate': predicate, 'object': obj,
                                   'inDateTime': in_date_time,
                                   'after': after, 'before': before,
                                   'mf_id': metafact['id'],
                                   'rule': rule['Rule'],
                                   'Head Coverage': rule['Head Coverage'],
                                   'PCA Confidence': rule['PCA Confidence'],
                                   'Confidence': conf}
        else:
            new_MF_cons[new_idx] = {'subject': subject, 'predicate': predicate, 'object': obj,
                                    'inDateTime': in_date_time,
                                    'after': after, 'before': before,
                                    'mf_id': metafact['id'],
                                    'rule': rule['Rule'],
                                    'Head Coverage': rule['Head Coverage'],
                                    'PCA Confidence': rule['PCA Confidence'],
                                    'Confidence': conf}
        Log(logfile, logtext1)
        
        # print('>>', new_idx, subject, predicate, obj, in_date_time, after, before)

    if tipo == G:
        return
    
    tipo, ts, ti = handleDates(body, predicate, 'restrictive')
    
    in_date_time = ts if ts != None and ts != "" else '-'
    after = ti[0] if ti != None and ti[0] != "" else '-'
    before = ti[1] if ti != None and ti[1] != "" else '-'
    
    if not (isValidDate(in_date_time) and isValidDate(after) and isValidDate(before)):
        return
    
    logtext2 = '%s %s %s %s'%(logtext, in_date_time, after, before)
    if [in_date_time, after, before] == ['-']*3:
        return
        
    new_idx = '%s%s%s%s%s%s'%(subject,predicate,obj,in_date_time,after,before)

    if not new_idx in allnew_MF_restr and (not predicate in all_metafacts or not new_idx in all_metafacts[predicate].index):
        allnew_MF_restr.add(new_idx)

        new_MF_restr[new_idx] = {'subject': subject, 'predicate': predicate, 'object': obj,
                                 'inDateTime': in_date_time,
                                 'after': after, 'before': before,
                                 'mf_id': metafact['id'],
                                 'rule': rule['Rule'],
                                 'Head Coverage': rule['Head Coverage'],
                                 'PCA Confidence': rule['PCA Confidence'],
                                 'Confidence': conf}
        Log(logfile, logtext2)

# In[12]:


"""
Selection of appropriate anonymous variable
"""
def getSubjNObj(s0, o0, s1, o1, mf):
    # 6 scenarios: abab abba abac abca abbc abcb
    if s0 == s1 and o0 == o1: # abab
        sbj = idx2o[mf['subject']]
        obj = idx2o[mf['object']]
    elif s0 == o1 and o0 == s1: # abba
        sbj = idx2o[mf['object']]
        obj = idx2o[mf['subject']]
    elif s0 == s1: # abac
        sbj = idx2o[mf['subject']]
        obj = None
    elif s0 == o1: # abca
        sbj = None
        obj = idx2o[mf['subject']]
    elif o0 == s1: # abbc
        sbj = idx2o[mf['object']]
        obj = None
    elif o0 == o1: # abcb
        sbj = None
        obj = idx2o[mf['object']]
    
    return sbj, obj


# In[13]:


"""
Select previously anonymous variable obtained from query to KB
Pick the anonymous variable discovered on the query to the KB
"""
def queriedSubjObj(s0, o0, s1, item):
    if s0 == s1 or o0 == s1:
        return item['o']
    else:
        return item['s']


# In[14]:


"""
Validate date predicates based on query predicate
"""
def checkCorrectDatePredicate(datePredicate, predicate):
    if predicate == 'hasChild':
        return datePredicate == 'birthDate'
    if predicate == 'actedIn':
        return datePredicate == 'releaseDate'
    if predicate == 'directed':
        return datePredicate == 'releaseDate'
    if predicate == 'wroteMusicFor':
        return datePredicate == 'releaseDate'
    if predicate == 'created':
        return datePredicate == 'releaseDate'
    if predicate == 'participatedIn':
        return datePredicate == 'releaseDate'
    if predicate == 'edited':
        return datePredicate == 'releaseDate'
    
    return True

"""
Define subject and object and time information to process header
"""
def processPropagation(values, mf, rule, s0, o0, s1, sh, oh, new_facts, new_MF_gen, new_MF_cons, new_MF_restr,
                       matched_predicate, query_predicate, numAtomsMatched):
    r1 = getRangeFromMF(mf)
    if matched_predicate in hastimestamp:
        atom1 = {'predicate': matched_predicate, 'type': 'ts', 'ts': r1[0]}
    elif matched_predicate in hastimeinterval:
        if r1[1] == '-' and r1[0] == '-':
            atom1 = {'predicate': matched_predicate, 'type': ''}
        elif r1[1] == '-':
            atom1 = {'predicate': matched_predicate, 'type': 'ts', 'ts': r1[0]}
        elif r1[0] == '-':
            atom1 = {'predicate': matched_predicate, 'type': 'ts', 'ts': r1[1]}
        else:    
            atom1 = {'predicate': matched_predicate, 'type': 'ti', 'ti': r1}
    else:
        atom1 = {'predicate': matched_predicate, 'type': ''}

    Log(logfile, 'process prop %s %s %s'%(rule['Rule'], matched_predicate, query_predicate))
    if s0 == sh and o0 == oh: # no anonymous variables
        s = mf['subject']
        o = mf['object']
        processNewHeader(mf, rule, s, o, new_facts, new_MF_gen, new_MF_cons, new_MF_restr, atom1, values[0],
                         query_predicate, numAtomsMatched)
    elif s0 == oh and o0 == sh: # no anonymous variables
        s = mf['object']
        o = mf['subject']
        processNewHeader(mf, rule, s, o, new_facts, new_MF_gen, new_MF_cons, new_MF_restr, atom1, values[0],
                         query_predicate, numAtomsMatched)
    elif s0 == sh: # with anonymous variables
        s = mf['subject']
        for item in values:
            Log(logfile, item)
            if checkCorrectDatePredicate(item['tempred'] if 'tempred' in item else '', query_predicate):
                o = queriedSubjObj(s0, o0, s1, item)
                processNewHeader(mf, rule, s, o, new_facts, new_MF_gen, new_MF_cons, new_MF_restr, atom1, item,
                                 query_predicate, numAtomsMatched)
    elif s0 == oh: # with anonymous variables
        o = mf['subject']
        for item in values:
            Log(logfile, item)
            if checkCorrectDatePredicate(item['tempred'] if 'tempred' in item else '', query_predicate):
                s = queriedSubjObj(s0, o0, s1, item)
                processNewHeader(mf, rule, s, o, new_facts, new_MF_gen, new_MF_cons, new_MF_restr, atom1, item,
                                 query_predicate, numAtomsMatched)
    elif o0 == sh: # with anonymous variables
        s = mf['object']
        for item in values:
            Log(logfile, item)
            if checkCorrectDatePredicate(item['tempred'] if 'tempred' in item else '', query_predicate):
                o = queriedSubjObj(s0, o0, s1, item)
                processNewHeader(mf, rule, s, o, new_facts, new_MF_gen, new_MF_cons, new_MF_restr, atom1, item,
                                 query_predicate, numAtomsMatched)
    elif o0 == oh: # with anonymous variables
        o = mf['object']
        for item in values:
            Log(logfile, item)
            if checkCorrectDatePredicate(item['tempred'] if 'tempred' in item else '', query_predicate):
                s = queriedSubjObj(s0, o0, s1, item)
                processNewHeader(mf, rule, s, o, new_facts, new_MF_gen, new_MF_cons, new_MF_restr, atom1, item,
                                 query_predicate, numAtomsMatched)


# In[20]:

def saveFiles(filename, data):
    df = pd.DataFrame.from_dict(data, orient='index')
    df.to_csv("results/%s"%(filename), sep='\t', encoding='utf-8')
    print('saved %s'%(filename), len(data))


def propaga(confidence=0.5, coverage=0.04, lim=10, batchsize=10, startFrom=0, counter=0):
    temp = {}
    new_MF_gen = {}
    new_MF_cons = {}
    new_MF_restr = {}
    new_facts = {}
    #batchsize = 10
    #batchsize = 5000
    procounter = 0

    for _, rule in rules.iterrows():
        # print(rule['Body'], '=>', rule['Header'], rule['Head Coverage'], rule['PCA Confidence'])
        if rule['Head Coverage'] > coverage and rule['PCA Confidence'] > confidence:
            if rule['s1'] == None: # body with only one atom
                if not rule['p0'] in idx2p:
                    continue
                print('Single atom: ', rule['Body'], '=>', rule['Header'])
                metafacts = all_metafacts[idx2p[rule['p0']]]
                c = 0
                for _, mf in metafacts.iterrows():
                    procounter += 1
                    if procounter < startFrom:
                        continue
                    # DONE in case of error continue until C >= last C printed
                    if c == lim:
                        break
                    c += 1
                    temp[rule['s0']] = mf['subject']
                    temp[rule['o0']] = mf['object']
                    s = temp[rule['sh']]
                    o = temp[rule['oh']]
                    r1 = getRangeFromMF(mf)
                    matched_predicate = idx2p[mf['predicate']]
                    if matched_predicate in hastimestamp:
                        atom1 = {'predicate': matched_predicate, 'type': 'ts', 'ts': r1[0]}
                    elif matched_predicate in hastimeinterval:
                        if (r1[1] == '-' and r1[0] == '-') or (r1[1] == None and r1[0] == None):
                            atom1 = {'predicate': matched_predicate, 'type': ''}
                        elif r1[1] == '-' or r1[1] == None:
                            atom1 = {'predicate': matched_predicate, 'type': 'ts', 'ts': r1[0]}
                        elif r1[0] == '-' or r1[0] == None:
                            atom1 = {'predicate': matched_predicate, 'type': 'ts', 'ts': r1[1]}
                        else:    
                            atom1 = {'predicate': matched_predicate, 'type': 'ti', 'ti': r1}
                    else:
                        atom1 = {'predicate': matched_predicate, 'type': ''}
                    processNewHeader(mf, rule, s, o, new_facts, new_MF_gen, new_MF_cons, new_MF_restr, atom1)
                    if len(new_MF_cons) >= batchsize or len(new_MF_gen) >= batchsize:
                        print("last C = %d"%(procounter), 'Single atom: ', rule['Body'], '=>', rule['Header'])
                        saveFiles('newMFgen%d.csv'%(counter), new_MF_gen)
                        saveFiles('newMFcons%d.csv'%(counter), new_MF_cons)
                        saveFiles('newMFrestr%d.csv'%(counter), new_MF_restr)
                        # TODO save each file individually when it hits len == batchsize
                        saveFiles('newFacts%d.csv'%(counter), new_facts)
                        counter += 1
                        new_MF_gen = {}
                        new_MF_cons = {}
                        new_MF_restr = {}
                        new_facts = {}
            else: # multiatom body
                if num_atoms > 2:
                    print(">>> More than 2 atoms!", rule['Body'], rule['Header'])
                    continue
                    
                for i in range(num_atoms):
                    pcol = 'p%d'%(i)
                    if rule[pcol] in idx2p:
                        unmatched_atoms = []
                        for k in range(num_atoms):
                            skey = 's%d'%(k)
                            pkey = 'p%d'%(k)
                            okey = 'o%d'%(k)
                            if k == i:
                                match_sub = rule[skey]
                                match_pre = rule[pkey]
                                match_obj = rule[okey]
                            else:
                                unmatched_atoms.append([rule[skey], rule[pkey], rule[okey]])
                    
                        matched_predicate = idx2p[match_pre]
                        metafacts = all_metafacts[matched_predicate]

                        head_sub = rule['sh']
                        head_pre = rule['ph']
                        head_obj = rule['oh']

                        print('Multi atom: ', rule['Body'], '=>', rule['Header'])
                        c = 0
                        for _, mf in metafacts.iterrows():
                            procounter += 1
                            if procounter < startFrom:
                                continue

                            for atom in unmatched_atoms:
                                qry_sub = atom[0]
                                qry_pre = atom[1]
                                qry_obj = atom[2]

                                query_predicate = idx2p[qry_pre] if qry_pre in idx2p else qry_pre
                                query_subject, query_object = getSubjNObj(match_sub, match_obj, qry_sub, qry_obj, mf)

                                if query_predicate in hastimestamp:
                                    if query_predicate in all_metafacts:
                                        localmfs = all_metafacts[query_predicate]
                                        queryonline = len(localmfs) == 0
                                    else:
                                        queryonline = True
                                    if not queryonline:
                                        if query_subject != None and query_object != None:
                                            localmfs = localmfs[localmfs['subject'] == qry_sub]
                                            if len(localmfs) > 0:
                                                localmfs = localmfs[localmfs['object'] == qry_obj]
                                                if len(localmfs) > 0:
                                                    # construct values
                                                    values = []
                                                    for _, itemf in localmfs.iterrows():
                                                        values.append({'tempred': '',
                                                                       'date': itemf['inDateTime'],
                                                                       'o': query_object,
                                                                       's': query_subject})
                                                else:
                                                    queryonline = True
                                            else:
                                                queryonline = True
                                        elif query_subject != None:
                                            localmfs = localmfs[localmfs['subject'] == qry_sub]
                                            if len(localmfs) > 0:
                                                values = []
                                                for _, itemf in localmfs.iterrows():
                                                    localobj = idx2o[itemf['object']] if itemf['object'] in idx2o else itemf['object']
                                                    values.append({'tempred': '',
                                                                   'date': itemf['inDateTime'],
                                                                   'o': localobj,
                                                                   's': query_subject})
                                            else:
                                                queryonline = True
                                        else:
                                            localmfs = localmfs[localmfs['object'] == qry_obj]
                                            if len(localmfs) > 0:
                                                values = []
                                                for _, itemf in localmfs.iterrows():
                                                    localsub = idx2o[itemf['subject']] if itemf['subject'] in idx2o else itemf['subject']
                                                    values.append({'tempred': '',
                                                                   'date': itemf['inDateTime'],
                                                                   'o': query_object,
                                                                   's': localsub})
                                            else:
                                                queryonline = True
                                    
                                    if queryonline:
                                        result, _, values = timestamp_queryKB(query_subject, query_predicate, query_object)                                       
                                        if not result:
                                            break
                                        # override queried values with known date time from metafacts (matched one)
                                        if matched_predicate in hastimeinterval:
                                            for i in range(len(values)):
                                                values[i]['date'] = mf['after'] if mf['after'] != '-' else mf['before']
                                        else:
                                            for i in range(len(values)):
                                                values[i]['date'] = mf['inDateTime']
                                        numAtomsMatched = 1
                                    else:
                                        numAtomsMatched = 2 
                                    processPropagation(values, mf, rule,
                                                       match_sub, match_obj,
                                                       qry_sub,
                                                       head_sub, head_obj,
                                                       new_facts, new_MF_gen, new_MF_cons, new_MF_restr,
                                                       matched_predicate, query_predicate, numAtomsMatched)
                                elif query_predicate in hastimeinterval:
                                    if query_predicate in all_metafacts:
                                        localmfs = all_metafacts[query_predicate]
                                        queryonline = False
                                    else:
                                        queryonline = True
                                    if not queryonline:
                                        if query_subject != None and query_object != None:
                                            localmfs = localmfs[localmfs['subject'] == qry_sub]
                                            if len(localmfs) > 0:
                                                localmfs = localmfs[localmfs['object'] == qry_obj]
                                                if len(localmfs) > 0:
                                                    # construct values
                                                    values = []
                                                    for _, itemf in localmfs.iterrows():
                                                        values.append({'tempred': '',
                                                                       'born': itemf['after'],
                                                                       'died': itemf['before'],
                                                                       'start': itemf['after'],
                                                                       'end': itemf['before'],
                                                                       'o': query_object,
                                                                       's': query_subject})
                                                else:
                                                    queryonline = True
                                            else:
                                                queryonline = True
                                        elif query_subject != None:
                                            localmfs = localmfs[localmfs['subject'] == qry_sub]
                                            if len(localmfs) > 0:
                                                values = []
                                                for _, itemf in localmfs.iterrows():
                                                    localobj = idx2o[itemf['object']] if itemf['object'] in idx2o else itemf['object']
                                                    values.append({'tempred': '',
                                                                   'born': itemf['after'],
                                                                   'died': itemf['before'],
                                                                   'start': itemf['after'],
                                                                   'end': itemf['before'],
                                                                   'o': localobj,
                                                                   's': query_subject})
                                            else:
                                                queryonline = True
                                        else:
                                            localmfs = localmfs[localmfs['object'] == qry_obj]
                                            if len(localmfs) > 0:
                                                values = []
                                                for _, itemf in localmfs.iterrows():
                                                    localsub = idx2o[itemf['subject']] if itemf['subject'] in idx2o else itemf['subject']
                                                    values.append({'tempred': '',
                                                                   'born': itemf['after'],
                                                                   'died': itemf['before'],
                                                                   'start': itemf['after'],
                                                                   'end': itemf['before'],
                                                                   'o': query_object,
                                                                   's': localsub})
                                            else:
                                                queryonline = True
                                    
                                    if queryonline:
                                        result, _, values = interval_queryKB(query_subject, query_predicate, query_object)
                                        
                                        if not result:
                                            break
                                        
                                        if matched_predicate in hastimeinterval:
                                            for i in range(len(values)):
                                                values[i]['born'] = mf['after']
                                                values[i]['died'] = mf['before']
                                                values[i]['start'] = mf['after']
                                                values[i]['end'] = mf['before']
                                        else:
                                            for i in range(len(values)):
                                                values[i]['born'] = mf['inDateTime']
                                                values[i]['died'] = None
                                                values[i]['start'] = mf['inDateTime']
                                                values[i]['end'] = None
                                            
                                        numAtomsMatched = 1
                                    else:
                                        numAtomsMatched = 2
                                    processPropagation(values, mf, rule,
                                                       match_sub, match_obj,
                                                       qry_sub,
                                                       head_sub, head_obj,
                                                       new_facts, new_MF_gen, new_MF_cons, new_MF_restr,
                                                       matched_predicate, query_predicate, numAtomsMatched)
                                else:
                                    #print(query_predicate)
                                    result, _, values = queryKB2(query_subject, query_predicate, query_object)
                                    if not result:
                                        continue

                                    r1 = getRangeFromMF(mf)
                                    if matched_predicate in hastimestamp:
                                        atom1 = {'predicate': matched_predicate, 'type': 'ts', 'ts': r1[0]}
                                    elif matched_predicate in hastimeinterval:
                                        atom1 = {'predicate': matched_predicate, 'type': 'ti', 'ti': r1}
                                    else:
                                        atom1 = {'predicate': matched_predicate, 'type': ''}

                                    if match_sub == head_sub and match_obj == head_obj:
                                        s = match_sub
                                        o = match_obj
                                        processNewHeader(mf, rule, s, o, new_facts, new_MF_gen, new_MF_cons, new_MF_restr, atom1, None, query_predicate)
                                    elif match_sub == head_obj and match_obj == head_sub:
                                        s = match_obj
                                        o = match_sub
                                        processNewHeader(mf, rule, s, o, new_facts, new_MF_gen, new_MF_cons, new_MF_restr, atom1, None, query_predicate)
                                    elif match_sub == head_sub:
                                        s = match_sub
                                        for o in values:
                                            processNewHeader(mf, rule, s, o, new_facts, new_MF_gen, new_MF_cons, new_MF_restr, atom1, None, query_predicate)
                                    elif match_sub == head_obj:
                                        o = match_sub
                                        for s in values:
                                            processNewHeader(mf, rule, s, o, new_facts, new_MF_gen, new_MF_cons, new_MF_restr, atom1, None, query_predicate)
                                    elif match_obj == head_sub:
                                        s = match_obj
                                        for o in values:
                                            processNewHeader(mf, rule, s, o, new_facts, new_MF_gen, new_MF_cons, new_MF_restr, atom1, None, query_predicate)
                                    elif match_obj == head_obj:
                                        o = match_obj
                                        for s in values:
                                            processNewHeader(mf, rule, s, o, new_facts, new_MF_gen, new_MF_cons, new_MF_restr, atom1, None, query_predicate)

                                if len(new_MF_cons) >= batchsize or len(new_MF_gen) >= batchsize:
                                    print("C = %d"%(procounter),
                                          'Multi: ', rule['Body'], '=>', rule['Header'],
                                          "match: ", matched_predicate)
                                    saveFiles('newMFgen%d.csv'%(counter), new_MF_gen)
                                    saveFiles('newMFcons%d.csv'%(counter), new_MF_cons)
                                    saveFiles('newMFrestr%d.csv'%(counter), new_MF_restr)
                                    saveFiles('newFacts%d.csv'%(counter), new_facts)
                                    counter += 1
                                    new_MF_gen = {}
                                    new_MF_cons = {}
                                    new_MF_restr = {}
                                    new_facts = {}
                            if c == lim:
                                break
                            c += 1

    return new_MF_gen, new_MF_cons, new_MF_restr, new_facts

# In[21]:

logfile = open('superlog-test.csv', 'w')
factlogfile = open('factlog-test.csv', 'w')

"""Comment line 713 if the algorithm stops at some point."""
""" batchsize: number of records to be stored in each file."""
new_MF_gen, new_MF_cons, new_MF_restr, new_facts = propaga(lim=10000000, batchsize=5000)

"""Uncomment these two lines if the algorithm stops at some point."""
"""
Update the parameter "startFrom" with the last value displayed at the terminal: C = XXX
Update the parameter "counter" with the last value + 1 appended to the file name newMFgenXXX.csv 
(XXX refers to a number).
"""
#new_MF_gen, new_MF_cons, new_MF_restr, new_facts = propaga(confidence=0.3, coverage=0.02, lim=10000000, batchsize=5000,
#                                                           startFrom=533151, counter=99)


print(len(new_MF_gen), len(new_facts))

saveFiles('newMFgenLast.csv', new_MF_gen)
saveFiles('newMFconsLast.csv', new_MF_cons)
saveFiles('newMFrestrLast.csv', new_MF_restr)
saveFiles('newFactsLast.csv', new_facts)

logfile.close()
factlogfile.close()