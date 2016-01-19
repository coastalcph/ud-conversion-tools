from pathlib import Path
import argparse
import sys
import random

from lib.conll import CoNLLReader

def main():
    parser = argparse.ArgumentParser(description="""Sample k trees from a dependency tree file (w/o replacement)""")
    parser.add_argument('input', help="conllu file")
    parser.add_argument('output', help="target file", type=Path)
    parser.add_argument('--input-format', choices=['conll2006', 'conll2006dense', 'conllu'], default="conllu")

    parser.add_argument('--k',default=None,help="randomly sample k instances from file", type=int, required=True)
    parser.add_argument('--ignore-first-n',default=0,help="ignore first n sentences in the file", type=int, required=False)
    parser.add_argument('--seed',default=None,help="seed to use")
    parser.add_argument('--ignore-warning', help="if k > size, ignore warning and select all", default=False, action="store_true")

    args = parser.parse_args()

    cio = CoNLLReader()
    if args.input_format == "conllu":
        orig_treebank = cio.read_conll_u(args.input)
    elif args.input_format == "conll2006":
        orig_treebank = cio.read_conll_2006(args.input)
    elif args.input_format == "conll2006dense":
        orig_treebank = cio.read_conll_2006_dense(args.input)
    num_trees = len(orig_treebank)

    if args.seed:
        random.seed(args.seed)
    print("Loaded treebank {} with {} sentences".format(args.input,num_trees), file=sys.stderr)

    if args.k > num_trees:
        if args.ignore_warning:
            print("ignore-warning={}".format(args.ignore_warning),file=sys.stderr)
        else:
            print("k cannot be larger than {} trees. abort. ".format(num_trees))
            exit()
    if args.ignore_first_n >= max(num_trees-args.k,num_trees):
        print("--ignore-first-n cannot be larger than {} trees. abort. ".format(max(num_trees-args.k,num_trees)))
        exit()
        
    if args.ignore_first_n:
        print("ignoring first {} trees in file".format(args.ignore_first_n), file=sys.stderr)
        orig_treebank = orig_treebank[args.ignore_first_n+1:]

    random.shuffle(orig_treebank)
    sample = orig_treebank[0:args.k]
    print("sampled {} trees. seed: {}".format(len(sample), args.seed))
    cio.write_conll(sample, args.output, "conll2006")

if __name__ == "__main__":
    main()
