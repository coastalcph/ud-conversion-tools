from pathlib import Path
import argparse
import sys
import random

from lib.conll import CoNLLReader

def main():
    parser = argparse.ArgumentParser(description="""Convert conllu to conll format""")
    parser.add_argument('input', help="conllu file")
    parser.add_argument('output', help="target file", type=Path)
    parser.add_argument('--output_format', choices=['conll2006', 'conll2009', 'conllu'], default="conll2006")

    parser.add_argument('--k',default=None,help="randomly sample k instances from file", type=int, required=True)
    parser.add_argument('--seed',default=None,help="seed to use")

    args = parser.parse_args()

    cio = CoNLLReader()
    orig_treebank = cio.read_conll_u(args.input)
    num_trees = len(orig_treebank)


    if args.seed:
        random.seed(args.seed)
    print("Loaded treebank with {} sentences".format(num_trees), file=sys.stderr)
    if args.k and args.k > num_trees:
        print("k cannot be larger than {} trees. abort. ".format(num_trees))
        exit()

    random.shuffle(orig_treebank)
    sample = orig_treebank[0:args.k]
    print("sampled {} trees. seed: {}".format(len(sample), args.seed))
    cio.write_conll(sample, args.output, args.output_format)

if __name__ == "__main__":
    main()