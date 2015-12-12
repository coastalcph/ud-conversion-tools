from collections import defaultdict
from itertools import islice
from pathlib import Path
import argparse
import sys, copy

from lib.conll import CoNLLReader


parser = argparse.ArgumentParser(description="""Convert conllu to conll format""")
parser.add_argument('input', help="conllu file")
parser.add_argument('output', help="target file", type=Path)
parser.add_argument('--keep_fused_forms', help="By default removes fused tokens", default=True, action="store_true")
parser.add_argument('--remove_suffix_from_deprels', help="Restrict deprels to the common universal subset, e.g. nmod:tmod becomes nmod", default=False, action="store_true")
parser.add_argument('--remove_node_properties', help="space-separated list of node properties to remove: form, lemma, cpostag, postag, feats", metavar='prop', type=str, nargs='+')
parser.add_argument('--lang', help="specify a language [de, en, it, fr, sv]", default="default")
args = parser.parse_args()

if sys.version_info < (3,0):
    print("Sorry, requires Python 3.x.") #suggestion: install anaconda python
    sys.exit(1)

POSRANKPRECEDENCEDICT = defaultdict(list)
POSRANKPRECEDENCEDICT["none"] = []
POSRANKPRECEDENCEDICT["default"] = "VERB AUX PRON PROPN NOUN ADJ INT ADV ADP DET NUM PART SCONJ CONJ".split(" ")

POSRANKPRECEDENCEDICT["bg"] = []
POSRANKPRECEDENCEDICT["da"] = []
POSRANKPRECEDENCEDICT["de"] = "PROPN ADP DET ".split(" ")
POSRANKPRECEDENCEDICT["el"] = []
POSRANKPRECEDENCEDICT["en"] = []
POSRANKPRECEDENCEDICT["es"] = "VERB AUX PRON ADP DET".split(" ")
POSRANKPRECEDENCEDICT["fr"] = "VERB AUX PRON NOUN ADJ ADV ADP DET PART SCONJ CONJ".split(" ")
POSRANKPRECEDENCEDICT["it"] = "VERB AUX ADV PRON ADP DET".split(" ")
POSRANKPRECEDENCEDICT["sv"] = []


# Read the treebank sentences

propertiestoremove="form lemma".split(" ")

cio = CoNLLReader()
orig_treebank = cio.read_conll_u(args.input)#, args.keep_fused_forms, args.lang, POSRANKPRECEDENCEDICT)
modif_treebank = copy.copy(orig_treebank)
for s in modif_treebank:
    s.filter_sentence_content(args.keep_fused_forms, args.lang, POSRANKPRECEDENCEDICT,args.remove_node_properties)


cio.write_conll_2006(orig_treebank,args.output)
#TODO decide what to do about the comments