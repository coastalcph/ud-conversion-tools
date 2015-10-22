from conll import *
import copy
from collections import Counter, defaultdict
import os, sys, argparse



def pathtoroot(sent, child):
    path = []
    newhead = head_of(sent, child)
    while newhead:
        path.append(newhead)
        newhead = head_of(sent, newhead)
    return path

def get_highest_index_of_span(sent, span):  # retrieves the node index that is closest to root
    distancestoroot = [len(pathtoroot(sent, x)) for x in span]
    shortestdistancetoroot = min(distancestoroot)
    spanhead = span[distancestoroot.index(shortestdistancetoroot)]
    return spanhead


def get_deepest_index_of_span(sent, span):  # retrieves the node index that is farthest from root
    distancestoroot = [len(pathtoroot(sent, x)) for x in span]
    shortestdistancetoroot = max(distancestoroot)
    lownode = span[distancestoroot.index(shortestdistancetoroot)]
    return lownode


def subsumes(sent, head, child):
    if head in pathtoroot(sent, child):
        return True


def get_sentence_as_string(sent,printid=False):
    out = []
    for token_i in range(1, max(sent.nodes()) + 1):
        if printid:
            out.append(str(token_i)+":"+sent.node[token_i]['form'])
        else:
            out.append(sent.node[token_i]['form'])
    return u" ".join(out)

def POS_type_constrains(sent,posdict):
    for n in sent.nodes():
        form = sent.node[n]["form"]
        POS = sent.node[n]["cpostag"]
        if (form,POS) in posdict:
            newpos, newfeats,newlabel = posdict[(form,POS)]
            sent.node[n]["cpostag"] = newpos
            sent.node[n]["feats"] = parse_feats(newfeats)
            if newlabel != "_":
                sent[head_of(sent,n)][n]["deprel"] = newlabel
    return sent


def PROPN_functionwords(sent):
    for n in sorted(sent.nodes())[1:]:
        newpos = "PROPN"
        label = sent[head_of(sent,n)][n]["deprel"]
        cpostag = sent.node[n]["cpostag"]
        if cpostag == "PROPN":
            if label == "case":
                sent.node[n]["cpostag"]="ADP"
                sent.node[n]["feats"]= "_"

            if label == "cc":
                sent.node[n]["cpostag"]="CONJ"
                sent.node[n]["feats"]= "_"
    return sent


def mwe_ADP(sent):
    for h,d in sent.edges():
        try:
            if sent[h][d]["deprel"] == "mwe":
                if sent.node[h]["cpostag"] == "PROPN" and sent.node[d]["cpostag"] == "DET":
                    sent[h][d]["deprel"] = "det"
                elif sent.node[h]["cpostag"] == "PROPN" and sent.node[d]["cpostag"] == "ADP":
                    sent[h][d]["deprel"] = "case"
        except:
            print(h,d, sent.edges())
    return sent


def make_chain_left_headed(sent,triggerlabel):
    sentenceanalysis = []
    name_dependents = []
    name_heads = []
    lengt2rootcounter = Counter()
    for h,d in sent.edges():
        if sent[h][d]["deprel"] == triggerlabel : #and h < d:
            step="("+",".join(map(str,[h,d,sent.node[h]["form"],sent.node[d]["form"]]))+")"
            sentenceanalysis.append(step)
            name_dependents.append(d)
            name_heads.append(h)
            lengt2rootcounter[h] = len(pathtoroot(sent,h))
    #and now we identify mew chains
    name_chains = []
    alreadyvisited = []

    namespans = defaultdict(set)

    for head, length in reversed(lengt2rootcounter.most_common()): #we start from the closest to root
            current = head
            currentset = set([current])
            prevset = set()
            namespans[head] = set()
            while currentset != prevset:
                prevset = copy.copy(currentset)
                namespans[head] = namespans[head].union(set(sent.successors(current)).intersection(set(name_dependents)))
                currentset = currentset.union(set(sent.successors(current)).intersection(set(name_dependents)))
            name_chains.append(currentset)

    for oldhead in lengt2rootcounter.keys():
        current_namespan = namespans[oldhead].union([oldhead])
        newhead = min(current_namespan) #retrieve the leftmost element
        new_external_head = head_of(sent,oldhead) #the head of the old head

        if not new_external_head:
            new_external_head = 0

        newdeps = current_namespan.difference(set([newhead]))
        #print(current_namespan,newdeps,newhead,oldhead,new_external_head)
        if newhead != oldhead or len(current_namespan) > 2:
            #if the chain is more than 2 tokens long, or the head needs to be rearranged, then go through rearrangement
            oldlabel = sent[new_external_head][oldhead]["deprel"]
            sent.remove_edge(head_of(sent,newhead),newhead)
            sent.add_edge(new_external_head,newhead,attr_dict={"deprel":oldlabel})
            for d in newdeps:
                sent.remove_edge(head_of(sent,d),d)
                sent.add_edge(newhead,d,attr_dict={"deprel":triggerlabel})

    return sent





def read_formposdict(infolder):
    D = {}
    for file in os.listdir(infolder):
        print(file, file=sys.stderr)
        for line in open(infolder+file):
            try:
                freq, word, POS, feats, newpos, newfeats, newlabel = line.strip().split("\t")
                word = word.lower()
                if POS != newpos:
                    D[(word,POS)] = [newpos,newfeats,newlabel]
            except:
                pass
    return D

def main():
    parser = argparse.ArgumentParser(description="""UD_Spanish v1.1 to v1.2 """)
    parser.add_argument('infile')
    args = parser.parse_args()


    posdict = read_formposdict("posdicts/")
    #PROPN_fx_dict = read_formposdict("PROPNfx/")


    sentences = read_conll_u_file(args.infile)
    for s in sentences:
        s = PROPN_functionwords(s)
        s = mwe_ADP(s)
        #s = POS_type_constrains(s,posdict)
        s = make_chain_left_headed(s,"name")
        s = make_chain_left_headed(s,"mwe")
        write_sentence_conll2006(s)



if __name__ == "__main__":
    main()


#sentences = read_conll_u_file("es-ud-all.conllu")
#for s in sentences:
#    for n in sorted(s.nodes()):
#        if s.node[n]["cpostag"] == "VERB" and not s.node[n]["lemma"].endswith("r"):
#            form = s.node[n]["form"]
#            newlemma = s.node[n]["lemma"]
#            if form.endswith("ados") or form.endswith("adas"):
#                  newlemma = form[:-4]+"ar"
#             elif form.endswith("ado") or form.endswith("ada"):
#                  newlemma = form[:-3]+"ar"
#             elif form.endswith("a") or form.endswith("o"):
#                  newlemma = form[:-1]+"ar"
#             print(s.node[n]["form"],s.node[n]["lemma"],s.node[n]["cpostag"],newlemma,newlemma == s.node[n]["lemma"])
        # elif  s.node[n]["cpostag"] == "ADJ" and (s.node[n]["lemma"].endswith("ar") or s.node[n]["lemma"].endswith("er") or s.node[n]["lemma"].endswith("ir")) and not s.node[n]["form"].endswith("r"):
        #     newlemma = s.node[n]["lemma"]
        #     form = s.node[n]["form"]
        #     if form.endswith("a") or form.endswith("o"):
        #         newlemma = form[:-1]+"o"
        #     if form.endswith("as") or form.endswith("os"):
        #         newlemma = form[:-2]+"o"
        #     if form.endswith("e"):
        #         newlemma = form
        #     print(s.node[n]["form"],s.node[n]["lemma"],s.node[n]["cpostag"],newlemma,newlemma == s.node[n]["lemma"])
