from conll import *
import copy
from collections import Counter, defaultdict




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





def getproperties(propertyname,sent):
    return [sent.node[n][propertyname] for n in sorted(sent.nodes()) ]


relemmatizer = {}
for line in open("relemmatize_lexicon.tsv"):
    form, lemmaorig, pos, newlemma = line.strip().split(" ")
    form = form.lower()
    relemmatizer[(form,pos)]=newlemma.lower()

repostagger = {}
for line in open("repos_particles.txt"):

    form, lemma, oldpos, newpos, feats = line.strip().split()
    form = form.lower()
    repostagger[(form,oldpos)]=(newpos,feats)




def retag(sent):
    changes = False
    for n in sorted(sent.nodes()):
        form = sent.node[n]["form"].lower()
        upos = sent.node[n]["cpostag"]
        if (form,upos) in repostagger:
            sent.node[n]["cpostag"] = repostagger[(form,upos)][0]
            sent.node[n]["feats"] = parse_feats(repostagger[(form,upos)][1])
    return sent


def relemmatize(sent):
    changes = False
    for n in sorted(sent.nodes()):
        form = sent.node[n]["form"].lower()
        upos = sent.node[n]["cpostag"]
        if (form,upos) in relemmatizer:
            sent.node[n]["lemma"] = relemmatizer[(form,upos)]
    return sent






def mew_make_leftheaded2(sent):
    sentenceanalysis = []
    mwe_dependents = []
    for h,d in sent.edges():
        if sent[h][d]["deprel"] == "mwe" and h > d:
            step="("+",".join(map(str,[h,d,sent.node[h]["form"],sent.node[d]["form"]]))+")"
            sentenceanalysis.append(step)
            mwe_dependents.append(d)
    #and now we identify mew chains

    mwe_chains = []
    if mwe_dependents:
        dependent_stack = set(copy.copy(mwe_dependents))
        current = min(dependent_stack)
        currentchain = [current]

        mwe_chains = []
        while dependent_stack:
            current = max(dependent_stack)
            currentset = set([current])
            prevset = set()
            while currentset != prevset:
                prevset = copy.copy(currentset)
                currentset = currentset.union(set(sent.successors(current)).intersection(set(mwe_dependents)))
            mwe_chains.append(currentset)
            dependent_stack = dependent_stack.difference(currentset)






    if len(mwe_dependents) > 1:
            print(mwe_chains,mwe_dependents,sentenceanalysis)
    #    print(sentenceanalysis,getproperties("form",sent))
    return sent


def POS_type_constrains(sent,D):
    return sent


def mew_make_leftheaded(sent):
    sentenceanalysis = []
    name_dependents = []
    name_heads = []
    lengt2rootcounter = Counter()
    for h,d in sent.edges():
        if sent[h][d]["deprel"] == "mwe" : #and h < d:
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
        print(current_namespan,newdeps,newhead,oldhead,new_external_head)
        if newhead != oldhead or len(current_namespan) > 2:
            #if the chain is more than 2 tokens long, or the head needs to be rearranged, then go through rearrangement
            oldlabel = sent[new_external_head][oldhead]["deprel"]
            sent.remove_edge(head_of(sent,newhead),newhead)
            sent.add_edge(new_external_head,newhead,attr_dict={"deprel":oldlabel})
            for d in newdeps:
                sent.remove_edge(head_of(sent,d),d)
                sent.add_edge(newhead,d,attr_dict={"deprel":"mwe"})

    return sent


def propernames_make_leftheaded(sent):
    sentenceanalysis = []
    name_dependents = []
    name_heads = []
    lengt2rootcounter = Counter()
    for h,d in sent.edges():
        if sent[h][d]["deprel"] == "name" : #and h < d:
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
        print(current_namespan,newdeps,newhead,oldhead,new_external_head)
        if newhead != oldhead or len(current_namespan) > 2:
            #if the chain is more than 2 tokens long, or the head needs to be rearranged, then go through rearrangement
            oldlabel = sent[new_external_head][oldhead]["deprel"]
            sent.remove_edge(head_of(sent,newhead),newhead)
            sent.add_edge(new_external_head,newhead,attr_dict={"deprel":oldlabel})
            for d in newdeps:
                sent.remove_edge(head_of(sent,d),d)
                sent.add_edge(newhead,d,attr_dict={"deprel":"name"})

    return sent


def repair_single_root(sent):
    return sent


sentences = read_conll_u_file("es-ud-all.conllu")
for s in sentences:
    #s = retag(s)
    #s = relemmatize(s)
    s = POS_type_constrains(s,posdict)
    s = mew_make_leftheaded(s)
    s = propernames_make_leftheaded(s)

write_conll_2006(sentences,"outfile.conllu")






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
