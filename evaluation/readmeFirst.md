To run the file 'compMFvsWikidata.ipynb', first it is necessary to link a Wikidata identifier to each meta-fact that was generated. This is done to avoid ambiguity of the data (subject and object) that will be compare against the ground-truth data.
To link the Wikidata identifier, follow these steps:

1. Into the 'results' folder, create a folder 'wikID'.
2. Run the file 'linkWD_ID.py'. Verify that the paths to the input file are correct.
3. Generate a single file from the files produced. To help you to merge the files, you can use the 'mergerFiles.ipynb' (setup the path to save the file inside wikID).
4. Unzip the file 'groundTruthData.tar.xz' located inside  wikidata folder.

*Important*
- Queries used to obtain the ground-truth data from Wikidata are stored in the 'wikidata/wid_sparql.txt'.
- We merge data from playsFor.csv into isAffiliatedTo.csv.
