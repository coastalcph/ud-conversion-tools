from conll import *

sentences = read_conll_u_file("es-ud-all.conllu")
for s in sentences:
    for n in sorted(s.nodes()):
        if s.node[n]["cpostag"] == "VERB" and not s.node[n]["lemma"].endswith("r"):
            #print(s.node[n]["form"],s.node[n]["lemma"],s.node[n]["cpostag"])
            pass
        elif  s.node[n]["cpostag"] == "ADJ" and (s.node[n]["lemma"].endswith("ar") or s.node[n]["lemma"].endswith("er") or s.node[n]["lemma"].endswith("ir")):
            print(s.node[n]["form"],s.node[n]["lemma"],s.node[n]["cpostag"])
