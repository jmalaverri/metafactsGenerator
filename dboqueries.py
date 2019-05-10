from datehandler import parse_date
import requests
import re

maping = {'dbo': {'marriedTo': 'spouse'}}

dbo = "<http://dbpedia.org/ontology/>"
dbp = "<http://dbpedia.org/property/>"
res = "<http://dbpedia.org/resource/>"

url = "http://dbpedia.org/sparql"
#url = "http://live.dbpedia.org/sparql"

yago2dbpedia = {'actedIn': 'starring',
                'directed': 'director',
                'edited': 'editing',
                'created': 'notableWork',
                'participatedIn': 'place', 
                'hasChild': 'child',
                'worksAt': 'employer',
                'graduatedFrom': 'almaMater',
                'isMarriedTo': 'spouse',
                'playsFor': 'currentMember',
                'isLocatedIn': 'location',
                'happenedIn': 'place',
                'isCitizenOf': 'nationality',
                'livesIn': 'residence',
                'wasBornIn': 'birthPlace',
                'diedIn': 'deathPlace',
                'hasAcademicAdvisor': 'doctoralAdvisor',
                'influences': 'influenced',
                'isAffiliatedTo': 'party',
                'hasCapital': 'capital',
                'hasWonPrize': 'award',
                'isKnownFor': 'knownFor',
                'hasOfficialLanguage': 'officialLanguage',
                'wasBornOnDate': 'birthDate',
                'diedOnDate': 'deathDate'}

invertAtom = {"starring", "director", "place", "currentMember", "editing"}


"""#### Query KB when both subject and object are known"""
def queryKB(subject, predicate, obj):
    if not predicate in yago2dbpedia:
        return False, '', []
    predicate = yago2dbpedia[predicate]
    inverted = predicate in invertAtom
    if inverted:
        query = """
        PREFIX dbo: %s
        PREFIX dbp: %s
        PREFIX res: %s
        
        SELECT 
            ?r
        WHERE {
                <http://dbpedia.org/resource/%s> dbo:%s <http://dbpedia.org/resource/%s> .
                <http://dbpedia.org/resource/%s> rdf:type ?r .
           }
        """%(dbo, dbp, res, obj, predicate, subject, obj)
    else:
        query = """
        PREFIX dbo: %s
        PREFIX dbp: %s
        PREFIX res: %s
        
        SELECT 
            ?r
        WHERE {
                <http://dbpedia.org/resource/%s> dbo:%s <http://dbpedia.org/resource/%s> .
                <http://dbpedia.org/resource/%s> rdf:type ?r .
           }
        """%(dbo, dbp, res, subject, predicate, obj, obj)
    r = requests.get(url, params = {'format': 'json', 'query': query})
    try:
        data = r.json()
    except ValueError as e:
        print("error", subject, predicate, obj)
        return False
    
    values = []
    for item in data['results']['bindings']:
        values.append({'element': item['r']['value']})

    return len(values) > 0



"""#### Query KB when either subject or object is unknown"""
def queryKB2(subject, predicate, obj):
    if not predicate in yago2dbpedia:
        return False, '', []
    predicate = yago2dbpedia[predicate]
    inverted = predicate in invertAtom
    if subject == None:
        if inverted:
            query = """
            PREFIX dbo: %s
            PREFIX dbp: %s
            PREFIX res: %s

            SELECT 
                ?s
            WHERE {
                    <http://dbpedia.org/resource/%s> dbo:%s ?s .
               }
            """%(dbo, dbp, res, obj, predicate)
        else:
            query = """
            PREFIX dbo: %s
            PREFIX dbp: %s
            PREFIX res: %s

            SELECT 
                ?s
            WHERE {
                    ?s dbo:%s <http://dbpedia.org/resource/%s> .
               }
            """%(dbo, dbp, res, predicate, obj)
        flag = 's'
    elif obj == None:
        if inverted:
            query = """
            PREFIX dbo: %s
            PREFIX dbp: %s
            PREFIX res: %s

            SELECT 
                ?o
            WHERE {
                    ?o dbo:%s <http://dbpedia.org/resource/%s> .
               }
            """%(dbo, dbp, res, predicate, subject)
        else:
            query = """
            PREFIX dbo: %s
            PREFIX dbp: %s
            PREFIX res: %s

            SELECT 
                ?o
            WHERE {
                    <http://dbpedia.org/resource/%s> dbo:%s ?o .
               }
            """%(dbo, dbp, res, subject, predicate)
        flag = 'o'
    else:
        if inverted:
            query = """
            PREFIX dbo: %s
            PREFIX dbp: %s
            PREFIX res: %s

            SELECT 
                ?r
            WHERE {
                    <http://dbpedia.org/resource/%s> dbo:%s <http://dbpedia.org/resource/%s> .
                    <http://dbpedia.org/resource/%s> rdf:type ?r .
               }
            """%(dbo, dbp, res, obj, predicate, subject, obj)
        else:
            query = """
            PREFIX dbo: %s
            PREFIX dbp: %s
            PREFIX res: %s

            SELECT 
                ?r
            WHERE {
                    <http://dbpedia.org/resource/%s> dbo:%s <http://dbpedia.org/resource/%s> .
                    <http://dbpedia.org/resource/%s> rdf:type ?r .
               }
            """%(dbo, dbp, res, subject, predicate, obj, obj)
        flag = ''
        
    r = requests.get(url, params = {'format': 'json', 'query': query})
    try:
        data = r.json()
    except ValueError as e:
        print("error", subject, predicate, obj)
        return False, '', []
    
    if flag == '':
        return len(data['results']['bindings']) > 0, flag, []
    
    values = []
    for item in data['results']['bindings']:
        values.append(item[flag]['value'].rsplit('/', 1)[-1])
    
    return len(values) > 0, flag, values

"""Query KB for timestamp"""
def timestamp_queryKB(subject, predicate, obj):
    # yago atom Brad actedIn Troy turns in dbpedia to Troy starring Brad

    if not predicate in yago2dbpedia:
        return False, '', []
    predicate = yago2dbpedia[predicate]
    inverted = predicate in invertAtom
    if subject == None:
        if inverted:
            query = """
            PREFIX dbo: %s
            PREFIX dbp: %s
            PREFIX res: %s

            SELECT ?s ?date ?tempred
            WHERE {
                <http://dbpedia.org/resource/%s> dbo:%s ?s .
                ?s ?tempred ?date .
                FILTER (REGEX(STR(?tempred),"[dD]ate")) .
                FILTER (REGEX(STR(?date),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
            }
            """%(dbo, dbp, res, obj, predicate)
        else:
            query = """
            PREFIX dbo: %s
            PREFIX dbp: %s
            PREFIX res: %s

            SELECT ?s ?date ?tempred
            WHERE {
                ?s dbo:%s <http://dbpedia.org/resource/%s> .
                ?s ?tempred ?date .
                FILTER (REGEX(STR(?tempred),"[dD]ate")) .
                FILTER (REGEX(STR(?date),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
            }
            """%(dbo, dbp, res, predicate, obj)
        flag = 's'
    elif obj == None:
        if inverted:
            query = """
            PREFIX dbo: %s
            PREFIX dbp: %s
            PREFIX res: %s

            SELECT ?o ?date ?tempred
            WHERE {
                ?o dbo:%s <http://dbpedia.org/resource/%s> .
                ?o ?tempred ?date .
                FILTER (REGEX(STR(?tempred),"[dD]ate")) .
                FILTER (REGEX(STR(?date),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
            }
            """%(dbo, dbp, res, predicate, subject)
        else:
            query = """
            PREFIX dbo: %s
            PREFIX dbp: %s
            PREFIX res: %s

            SELECT ?o ?date ?tempred
            WHERE {
                <http://dbpedia.org/resource/%s> dbo:%s ?o .
                ?o ?tempred ?date .
                FILTER (REGEX(STR(?tempred),"[dD]ate")) .
                FILTER (REGEX(STR(?date),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
            }
            """%(dbo, dbp, res, subject, predicate)

        flag = 'o'
    else: 
        if inverted:
            query = """
            PREFIX dbo: %s
            PREFIX dbp: %s
            PREFIX res: %s

            SELECT ?tempred ?date 
            WHERE {
                <http://dbpedia.org/resource/%s> dbo:%s <http://dbpedia.org/resource/%s> .
                <http://dbpedia.org/resource/%s> ?tempred ?date .
                FILTER (REGEX(STR(?tempred),"[dD]ate")) .
                FILTER (REGEX(STR(?date),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
            }
            """%(dbo, dbp, res, obj, predicate, subject, obj)
        else:
            query = """
            PREFIX dbo: %s
            PREFIX dbp: %s
            PREFIX res: %s

            SELECT ?tempred ?date 
            WHERE {
                <http://dbpedia.org/resource/%s> dbo:%s <http://dbpedia.org/resource/%s> .
                <http://dbpedia.org/resource/%s> ?tempred ?date .
                FILTER (REGEX(STR(?tempred),"[dD]ate")) .
                FILTER (REGEX(STR(?date),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
            }
            """%(dbo, dbp, res, subject, predicate, obj, obj)
        flag = ''

    # print(query)
    r = requests.get(url, params = {'format': 'json', 'query': query})
    try:
        data = r.json()
    except ValueError as e:
        print("error", subject, predicate, obj)
        return False, '', []

    values = []
    for item in data['results']['bindings']:
        values.append({'tempred': item['tempred']['value'].rsplit('/', 1)[-1],
                       'date':  parse_date(item['date']['value']),
                       'o': item['o']['value'].rsplit('/', 1)[-1] if 'o' in item else None,
                       's': item['s']['value'].rsplit('/', 1)[-1] if 's' in item else None})

    return len(values) > 0, flag, values



"""Query KB with a time interval"""
# TODO Evaluar la posibilidad de realizar mutiples consultas sparql (en batch)
# TODO to figure out about null born date or creation date
def interval_queryKB(subject, predicate, obj):
    
    if not predicate in yago2dbpedia:
        return False, '', []
    predicate = yago2dbpedia[predicate]
    inverted = predicate in invertAtom

    query = """
    PREFIX dbo: %s
    PREFIX dbp: %s
    PREFIX res: %s
    SELECT ?range
    WHERE {
        dbo:%s rdfs:range ?range .
    }
    """%(dbo, dbp, res, predicate)
    
    #if predicate == 'knownFor':
    #    print(query)
    r = requests.get(url, params = {'format': 'json', 'query': query})
    try:
        data = r.json()
    except ValueError as e:
        print("error range", subject, predicate, obj)
        return False, '', []


    if len(data['results']['bindings']) == 0:
        m = None
    else:
        m = re.search('Person', data['results']['bindings'][0]['range']['value'])
    
    if m is None:
        # query for non person
        if subject == None:
            query = """
            PREFIX dbo: %s
            PREFIX dbp: %s
            PREFIX res: %s
        
            SELECT ?s SAMPLE(?born) AS ?born SAMPLE(?died) as ?died SAMPLE(?cd) as ?cd SAMPLE(?dd) as ?dd {
            {
              SELECT ?s ?born ?died ?cd ?dd
              WHERE {
              ?s
                dbo:birthDate ?born ;
                dbo:deathDate ?died ;
                dbo:%s <http://dbpedia.org/resource/%s> .
              <http://dbpedia.org/resource/%s>
                dbo:foundingDate ?cd ;
                dbo:extinctionDate ?dd . 
                FILTER (REGEX(STR(?born),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?died),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?cd),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?dd),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }
            UNION
            {
              SELECT ?s ?born ?died ?cd
              WHERE {
              ?s
                dbo:birthDate ?born ;
                dbo:deathDate ?died ;
                dbo:%s <http://dbpedia.org/resource/%s> .
              <http://dbpedia.org/resource/%s>
                dbo:foundingDate ?cd . 
                FILTER (REGEX(STR(?born),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?died),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?cd),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }
            UNION
            {
              SELECT ?s ?born ?cd ?dd
              WHERE {
              ?s
                dbo:birthDate ?born ;
                dbo:%s <http://dbpedia.org/resource/%s> .
              <http://dbpedia.org/resource/%s>
                dbo:foundingDate ?cd ;
                dbo:extinctionDate ?dd . 
                FILTER (REGEX(STR(?born),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?cd),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?dd),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }
            UNION
            {
              SELECT ?s ?born ?cd
              WHERE {
              ?s
                dbo:birthDate ?born ;
                dbo:%s <http://dbpedia.org/resource/%s> .
              <http://dbpedia.org/resource/%s>
                dbo:foundingDate ?cd . 
                FILTER (REGEX(STR(?born),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?cd),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }

            }
            GROUP BY ?s
            """%(dbo, dbp, res, predicate, obj, obj, predicate, obj, obj, predicate, obj, obj, predicate, obj, obj)
            flag = 's'
        elif obj == None:
            query = """
            PREFIX dbo: %s
            PREFIX dbp: %s
            PREFIX res: %s
        
            SELECT ?o SAMPLE(?born) AS ?born SAMPLE(?died) as ?died SAMPLE(?cd) as ?cd SAMPLE(?dd) as ?dd {
            {
              SELECT ?o ?born ?died ?cd ?dd
              WHERE {
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?born ;
                dbo:deathDate ?died ;
                dbo:%s ?o.
              ?o
                dbo:foundingDate ?cd ;
                dbo:extintionDate ?dd . 
                FILTER (REGEX(STR(?born),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?died),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?cd),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?dd),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }
            UNION
            {
              SELECT ?o ?born ?died ?cd
              WHERE {
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?born ;
                dbo:deathDate ?died ;
                dbo:%s ?o.
              ?o
                dbo:foundingDate ?cd . 
                FILTER (REGEX(STR(?born),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?died),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?cd),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }
            UNION
            {
              SELECT ?o ?born ?cd ?dd
              WHERE {
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?born ;
                dbo:%s ?o.
              ?o
                dbo:foundingDate ?cd ;
                dbo:extintionDate ?dd . 
                FILTER (REGEX(STR(?born),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?cd),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?dd),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }
            UNION
            {
              SELECT ?o ?born ?cd
              WHERE {
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?born ;
                dbo:%s ?o.
              ?o
                dbo:foundingDate ?cd . 
                FILTER (REGEX(STR(?born),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?cd),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }

            }
            GROUP BY ?o
            """%(dbo, dbp, res, subject, predicate, subject, predicate, subject, predicate, subject, predicate)
            flag = 'o'
        else: 
            query = """
            PREFIX dbo: %s
            PREFIX dbp: %s
            PREFIX res: %s
        
            SELECT SAMPLE(?born) AS ?born SAMPLE(?died) as ?died SAMPLE(?cd) as ?cd SAMPLE(?dd) as ?dd {
            {
              SELECT ?born ?died ?cd ?dd
              WHERE {
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?born ;
                dbo:deathDate ?died ;
                dbo:%s <http://dbpedia.org/resource/%s> .
              <http://dbpedia.org/resource/%s>
                dbo:foundingDate ?cd ;
                dbo:extintionDate ?dd . 
                FILTER (REGEX(STR(?born),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?died),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?cd),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?dd),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }
            UNION
            {
              SELECT ?born ?died ?cd
              WHERE {
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?born ;
                dbo:deathDate ?died ;
                dbo:%s <http://dbpedia.org/resource/%s>.
              <http://dbpedia.org/resource/%s>
                dbo:foundingDate ?cd . 
                FILTER (REGEX(STR(?born),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?died),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?cd),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }
            UNION
            {
              SELECT ?born ?cd ?dd
              WHERE {
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?born ;
                dbo:%s <http://dbpedia.org/resource/%s> .
              <http://dbpedia.org/resource/%s>
                dbo:foundingDate ?cd ;
                dbo:extintionDate ?dd . 
                FILTER (REGEX(STR(?born),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?cd),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?dd),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }
            UNION
            {
              SELECT ?born ?cd
              WHERE {
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?born ;
                dbo:%s <http://dbpedia.org/resource/%s>.
              <http://dbpedia.org/resource/%s>
                dbo:foundingDate ?cd .
                FILTER (REGEX(STR(?born),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?cd),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }

            }
            """%(dbo, dbp, res, subject, predicate, obj, obj, subject, predicate, obj, obj,
                 subject, predicate, obj, obj, subject, predicate, obj, obj)
            flag = ''


        #print("non person", query)
        r = requests.get(url, params = {'format': 'json', 'query': query})
        try:
            data = r.json()
        except ValueError as e:
            print("error", subject, predicate, obj)
            return False, '', []
        values = []
        for item in data['results']['bindings']:
            values.append({'born': parse_date(item['born']['value']) if 'born' in item else None,
                           'died': parse_date(item['died']['value']) if 'died' in item else None,
                           'start': parse_date(item['cd']['value']) if 'cd' in item else None,
                           'end': parse_date(item['dd']['value']) if 'dd' in item else None,
                           'o': item['o']['value'].rsplit('/', 1)[-1] if 'o' in item else None,
                           's': item['s']['value'].rsplit('/', 1)[-1] if 's' in item else None})

    else:
        # is a person
        # query for non person
        if subject == None:
            query = """
            PREFIX dbo: %s
            PREFIX dbp: %s
            PREFIX res: %s
        
            SELECT ?s SAMPLE(?sborn) as ?sborn SAMPLE(?sdied) as ?sdied SAMPLE(?oborn) as ?oborn SAMPLE(?odied) as ?odied { 
            {
              SELECT ?s ?sborn ?sdied ?oborn ?odied
              WHERE {
              ?s
                dbo:birthDate ?sborn ;
                dbo:deathDate ?sdied ;
                dbo:%s <http://dbpedia.org/resource/%s> .
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?oborn ;
                dbo:deathDate ?odied .
                FILTER (REGEX(STR(?sborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?sdied),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?oborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?odied),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }
            UNION
            {
              SELECT ?s ?sborn ?sdied ?oborn
              WHERE {
              ?s
                dbo:birthDate ?sborn ;
                dbo:deathDate ?sdied ;
                dbo:%s <http://dbpedia.org/resource/%s> .
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?oborn .
                FILTER (REGEX(STR(?sborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?sdied),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?oborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }
            UNION
            {
              SELECT ?s ?sborn ?oborn ?odied
              WHERE {
              ?s
                dbo:birthDate ?sborn ;
                dbo:%s <http://dbpedia.org/resource/%s> .
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?oborn ;
                dbo:deathDate ?odied .
                FILTER (REGEX(STR(?sborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?oborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?odied),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }
            UNION
            {
              SELECT ?s ?sborn ?oborn
              WHERE {
              ?s
                dbo:birthDate ?sborn ;
                dbo:%s <http://dbpedia.org/resource/%s> .
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?oborn .
                FILTER (REGEX(STR(?sborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?oborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }

            }
            GROUP BY ?s
            """%(dbo, dbp, res, predicate, obj, obj, predicate, obj, obj, predicate, obj, obj, predicate, obj, obj)
            flag = 's'
        elif obj == None:
            query = """
            PREFIX dbo: %s
            PREFIX dbp: %s
            PREFIX res: %s
        
            SELECT ?o SAMPLE(?sborn) as ?sborn SAMPLE(?sdied) as ?sdied SAMPLE(?oborn) as ?oborn SAMPLE(?odied) as ?odied {
            {
              SELECT ?o ?sborn ?sdied ?oborn ?odied
              WHERE {
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?sborn ;
                dbo:deathDate ?sdied ;
                dbo:%s ?o .
              ?o
                dbo:birthDate ?oborn ;
                dbo:deathDate ?odied .
                FILTER (REGEX(STR(?sborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?sdied),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?oborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?odied),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }
            UNION
            {
              SELECT ?o ?sborn ?sdied ?oborn
              WHERE {
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?sborn ;
                dbo:deathDate ?sdied ;
                dbo:%s ?o .
              ?o
                dbo:birthDate ?oborn .
                FILTER (REGEX(STR(?sborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?sdied),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?oborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }
            UNION
            {
              SELECT ?o ?sborn ?oborn ?odied
              WHERE {
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?sborn ;
                dbo:%s ?o .
              ?o
                dbo:birthDate ?oborn ;
                dbo:deathDate ?odied .
                FILTER (REGEX(STR(?sborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?oborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?odied),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }
            UNION
            {
              SELECT ?o ?sborn ?oborn
              WHERE {
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?sborn ;
                dbo:%s ?o .
              ?o
                dbo:birthDate ?oborn .
                FILTER (REGEX(STR(?sborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?oborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }

            }
            GROUP BY ?o
            """%(dbo, dbp, res, subject, predicate, subject, predicate, subject, predicate, subject, predicate)
            flag = 'o'
        else: 
            query = """
            PREFIX dbo: %s
            PREFIX dbp: %s
            PREFIX res: %s
        
            SELECT SAMPLE(?sborn) as ?sborn SAMPLE(?sdied) as ?sdied SAMPLE(?oborn) as ?oborn SAMPLE(?odied) as ?odied {
            {
              SELECT ?sborn ?sdied ?oborn ?odied
              WHERE {
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?sborn ;
                dbo:deathDate ?sdied ;
                dbo:%s <http://dbpedia.org/resource/%s> .
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?oborn ;
                dbo:deathDate ?odied .
                FILTER (REGEX(STR(?sborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?sdied),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?oborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?odied),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }
            UNION
            {
              SELECT ?sborn ?sdied ?oborn
              WHERE {
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?sborn ;
                dbo:deathDate ?sdied ;
                dbo:%s <http://dbpedia.org/resource/%s> .
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?oborn .
                FILTER (REGEX(STR(?sborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?sdied),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?oborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }
            UNION
            {
              SELECT ?sborn ?oborn ?odied
              WHERE {
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?sborn ;
                dbo:%s <http://dbpedia.org/resource/%s> .
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?oborn ;
                dbo:deathDate ?odied .
                FILTER (REGEX(STR(?sborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?oborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?odied),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }
            UNION
            {
              SELECT ?sborn ?oborn
              WHERE {
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?sborn ;
                dbo:%s <http://dbpedia.org/resource/%s> .
              <http://dbpedia.org/resource/%s>
                dbo:birthDate ?oborn .
                FILTER (REGEX(STR(?sborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}")) .
                FILTER (REGEX(STR(?oborn),"[0-9]{4}-[0-9]{2}-[0-9]{2}"))
              }
            }

            }
            """%(dbo, dbp, res, subject, predicate, obj, obj, subject, predicate, obj, obj,
                 subject, predicate, obj, obj, subject, predicate, obj, obj)
            flag = ''
        
        #print(query)
        
        r = requests.get(url, params = {'format': 'json', 'query': query})
        try:
            data = r.json()
        except ValueError as e:
            print("error", subject, predicate, obj)
            return False, '', []

        values = []
        for item in data['results']['bindings']:
            values.append({'born': parse_date(item['sborn']['value']) if 'sborn' in item else None,
                           'died': parse_date(item['sdied']['value']) if 'sdied' in item else None,
                           'start': parse_date(item['oborn']['value']) if 'oborn' in item else None,
                           'end': parse_date(item['odied']['value']) if 'odied' in item else None,
                           'o': item['o']['value'].rsplit('/', 1)[-1] if 'o' in item else None,
                           's': item['s']['value'].rsplit('/', 1)[-1] if 's' in item else None})

    return len(values) > 0, flag, values

"""Get wikidata ID sameAs link"""
def queryWdID(sub, obj):
    query = """        
        SELECT (SAMPLE(?subid) AS ?subID)  (SAMPLE(?objid) AS ?objID)      
            {
             {
                SELECT ?id AS ?subid
                WHERE {
                        <http://dbpedia.org/resource/%s> (owl:sameAs|^owl:sameAs) ?obj .
                            FILTER (STRSTARTS(STR(?obj), "http://www.wikidata.org"))
                            BIND(strafter(str(?obj), "entity/" ) as ?id )
                       }
             }
                    UNION
             {
                SELECT ?yid AS ?objid
                WHERE {
                        <http://dbpedia.org/resource/%s> (owl:sameAs|^owl:sameAs) ?obj .
                            FILTER (STRSTARTS(STR(?obj), "http://www.wikidata.org"))
                            BIND(strafter(str(?obj), "entity/" ) as ?yid )
                       }
             }
            }
        """%(sub,obj)
    
    r = requests.get(url, params = {'format': 'json', 'query': query})
    try:
        data = r.json()
    except ValueError as e:
        print("error", sub, obj)
        return False, []
    
    values = []
    for item in data['results']['bindings']:
        values.append({'subID': item['subID']['value'] if 'subID' in item else None,
                       'objID':item['objID']['value'] if 'objID' in item else None})
    
    return len(values) > 0, values

