# ud-conversion-tools
Conversion tools for UD treebanks

conllu_to_conll.py: convert conllu to conll format (with the option to choose whether to keep the fused wordforms, e.g. 'della' in Italian, or 'im'  in German

Requires:
 python3
 networkx
 pathlib

Anaconda python can keep different python versions. For install, to get python3 after installing anaconda:
conda create -n p3k python=3.3 
Now you can activate the python3 environment with
source activate p3k
And install the missing packages (with pip or conda)

