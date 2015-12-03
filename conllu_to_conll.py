from collections import defaultdict
from itertools import islice
from pathlib import Path
import argparse
import sys

from lib.conll import CoNLLReader


parser = argparse.ArgumentParser(description="""Convert conllu to conll format""")
parser.add_argument('input', help="conllu file", type=Path)
parser.add_argument('output', help="target file", type=Path)
parser.add_argument('--keep_fused_forms', help="By default removes fused tokens", default=False, action="store_true")
parser.add_argument('--lang', help="specify a language [de, en, it, fr, sv]", default=None, required=True)
args = parser.parse_args()

if sys.version_info < (3,0):
    print("Sorry, requires Python 3.x.") #suggestion: install anaconda python
    sys.exit(1)

POSRANKPRECEDENCEDICT = defaultdict(list)
POSRANKPRECEDENCEDICT["none"] = []
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

cio = CoNLLReader()
orig_treebank = cio.read_conll_u(args.input, args.keep_fused_forms, args.lang, POSRANKPRECEDENCEDICT)
cio.write_conll_2006(orig_treebank,args.output)
