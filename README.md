# Project Title

Linking time to facts: an approach to enrich knowledge bases with temporal meta-facts

## Getting Started

This repository contains the approach we design and developed to generate temporal meta-facts in order to enrich knowledge bases. In addition to enabling the validity of the facts, we consider that enriching KBs with valid temporal information can make possible to extract richer information from these sources. For example, to generate a timeline of events related to an entity of interest (e.g: what happened in Paris from 1995 to 2000?). 

### Prerequisites

* The algorithm that implements our approach is in the file: alg_generateMF.py

* The libraries needed to run the algorithm are:
** datehandler.py: this file contains the temporal constraints we use to generate temporal information. Moreover, it also contains methods to deal with date formats.
** dboqueries.py: this file contains SPARQL queries which are send to DBpedia endpoint.

* rules.csv: This files contains AMIE+ logical rules.

* metafacts.pkl.gz: This file contains the input data. It was created from the files stored in csv_files folder.

* Create a folder 'results'. In this folder will be saved the outputs produced by the algorithm.

* To run the alg_generateMF.py, open a terminal, go to the folder that contains the algorithm, the libraries, and all the necessary files informed previously, and write the command: python alg_generateMF.py

### Important

* Since we are using the DBpedia endpoint, and we don't have any control of it, to avoid losing the results generated at some point in the execution, we save the results in partial files, which are stored in the 'results' folder. Then these files can be merged into one single file, and use it in order to perform the analyzes of the generated data. You can use mergerFiles.ipynb (located in the folder utils) to help you to merge the files.

* If at any point the algorithm stops because of a problem in the DBpedia endpoint, comment the line 713, and uncomment lines 721--722. Furthermore, in the *propaga* method, update the parameters 'startFrom' and 'counter' with the values (see comments) ​​that appear at the terminal where the algorithm is running.

### Results
The file containing all generated meta-facts (obtained after merger of the partial files) is in the 'results' folder under the name 'allnewMFgen.csv', 'allnewMFcons.csv', and 'allnewMFrestr.csv'. We have generated three files since we can have 3 possibles scenarios based on the temporal constraints applied. However, for the data input we use in this work, we only generated results for the generic scenario, which are stored in the file 'allnewMFgen.csv'.


## Useful links

* The YAGO files we used to collect the input meta-facts are available in: [Download](https://www.mpi-inf.mpg.de/departments/databases-and-information-systems/research/yago-naga/yago/downloads/). A database script to load YAGO into a Postgres database is also provided in the download link. In this work, we only use some YAGO (.tsv) themes to recreate a portion of the YAGO database, which are: 
```
- Taxonomy: yagoSchema, yagoTaxonomy, and yagoTypes.
- CORE: yagoFacts, yagoLiteralFacts, and yagoDateFacts.
- Meta: yagoMetaFacts -- temporal and geospatial meta facts of yagoFacts
```

* Dbpedia [endpoint](https://dbpedia.org/sparql)

* Wikidata [service](https://query.wikidata.org/)


## Acknowledgements

* We would like to thank to Labex DigiCosme, VASTE (Veracity Assesment in Spatio-TEmporal heterogeneous data) project for the financial support for the development of this work.

This work can only exist thanks to the other sources and efforts publicaly available. In particular, we would like to thank:
* The creators of YAGO, DBpedia, and Wikidata. Thank you for providing to the research community such a wonderful base and for making your work available for free.
* The creators of AMIE+ [rules](https://www.mpi-inf.mpg.de/departments/databases-and-information-systems/research/yago-naga/amie/). Thank you for the tool, files, and detailed information you made publicly available.

* Thanks to all people working to maintain the endpoints to query YAGO, DBpedia, and Wikidata.