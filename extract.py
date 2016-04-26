from pathlib import Path
import argparse
import sys
import random

from lib.conll import CoNLLReader

def main():
    parser = argparse.ArgumentParser(description="""Extract data based on comments info""")
    parser.add_argument('input', help="conllu file")
    parser.add_argument('output', help="target file", type=Path)
    parser.add_argument('--input-format', choices=['conll2006', 'conll2006dense', 'conllu'], default="conllu")
    parser.add_argument('--mapping', help="mapping file", required=True)

    args = parser.parse_args()

    lines=[line.strip() for line in open(args.mapping)]
    mapping={}
    for line in lines:
        commentpart, target = line.split()
        mapping[commentpart] = target
    
    print("loaded mapping:", mapping, file=sys.stderr)

    cio = CoNLLReader()
    if args.input_format == "conllu":
        orig_treebank = cio.read_conll_u(args.input)
    elif args.input_format == "conll2006":
        orig_treebank = cio.read_conll_2006(args.input)
    elif args.input_format == "conll2006dense":
        orig_treebank = cio.read_conll_2006_dense(args.input)
    num_trees = len(orig_treebank)

    print("Loaded treebank {} with {} sentences".format(args.input,num_trees), file=sys.stderr)
    
    split = {mapping[k] : [] for k in mapping.keys()}
    default = "various"
    split[default] = []

    for tree in orig_treebank:
        found_mapping=False
        for token in " ".join(tree.graph['comment']).strip().split():
            if token in mapping:
                split[mapping[token]].append(tree)
                found_mapping=True
                continue
        if not found_mapping:
            split[default].append(tree)

    for key in split:
        print(key, len(split[key]), file=sys.stderr)
        cio.write_conll(split[key], Path(args.output.name + "_" + key), "conll2006")
    #sample = orig_treebank[0:args.k]
    #print("sampled {} trees. seed: {}".format(len(sample), args.seed))
    #cio.write_conll(sample, args.output, "conll2006")

if __name__ == "__main__":
    main()
