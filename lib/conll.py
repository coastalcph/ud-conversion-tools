from collections import defaultdict
import networkx as nx



class DependencyTree(nx.DiGraph):
    """
    A DependencyTree as networkx graph:
    nodes store information about tokens
    edges store edge related info, e.g. dependency relations
    """
    def __init__(self):
        nx.DiGraph.__init__(self)

    def pathtoroot(self, child):
        path = []
        newhead = self.head_of(self, child)
        while newhead:
            path.append(newhead)
            newhead = self.head_of(self, newhead)
        return path

    def head_of(self, n):
        for u, v in self.edges():
            if v == n:
                return u
        return None

    def get_sentence_as_string(self,printid=False):
        out = []
        for token_i in range(1, max(self.nodes()) + 1):
            if printid:
                out.append(str(token_i)+":"+self.node[token_i]['word'])
            else:
                out.append(self.node[token_i]['word'])
        return u" ".join(out)

    def subsumes(self, head, child):
        if head in self.pathtoroot(self, child):
            return True

    def get_highest_index_of_span(self, span):  # retrieves the node index that is closest to root
        distancestoroot = [len(self.pathtoroot(self, x)) for x in span]
        shortestdistancetoroot = min(distancestoroot)
        spanhead = span[distancestoroot.index(shortestdistancetoroot)]
        return spanhead


    def get_deepest_index_of_span(self, span):  # retrieves the node index that is farthest from root
        distancestoroot = [len(self.pathtoroot(self, x)) for x in span]
        shortestdistancetoroot = max(distancestoroot)
        lownode = span[distancestoroot.index(shortestdistancetoroot)]
        return lownode



CONLL06_COLUMNS = ['id', 'word', 'lemma', 'cpos', 'pos', 'feats', 'head', 'deprel', 'phead', 'pdeprel']

class CoNLLReader(object):
    """
    conll input/output
    """
    def __init__(self):
        pass


    def read_conll_2006(self, conll_path):
        sent = DependencyTree()

        for conll_line in conll_path.open():
            parts = conll_line.strip().split()
            if len(parts) in (8, 10):
                token = dict(zip(CONLL06_COLUMNS, parts))
                p = ParsedToken(token)
                sent.add_node(p.id, p.to_dict())
                # Remove head information from the node properties to avoid confusion
                 # in case the tree structure changes.
                sent.add_edge(p.head, p.id, deprel=p.deprel)
            elif len(parts) == 0:
                yield sent
                sent = DependencyTree()
            else:
                raise Exception("Invalid input format in line: ", conll_line)

        if len(sent):
            yield sent


    def write_conll_2006(self, list_of_graphs, conll_path):
        with conll_path.open('w') as out:
            for sent_i, sent in enumerate(list_of_graphs):
                if sent_i > 0:
                    print("", file=out)
                for token_i in range(1, max(sent.nodes()) + 1):
                    token_dict = dict(sent.node[token_i])
                    head_i = sent.head_of(token_i)
                    token_dict['head'] = head_i
                    # print(head_i, token_i)
                    token_dict['deprel'] = sent[head_i][token_i]['deprel']
                    token_dict['id'] = token_i
                    row = [str(token_dict.get(col, '_')) for col in CONLL06_COLUMNS]
                    print(u"\t".join(row), file=out)

            # emtpy line afterwards
            print(u"", file=out)



    def read_conll_u(self, conll_path, keepFusedForm=False, lang=None, posPreferenceDict=None):
        """
        default is like Dan Zeman's conllu_to_conll.pl:   (https://github.com/UniversalDependencies/tools/blob/master/conllu_to_conllx.pl)
        - default: remove comments and remove fused forms

        - keepFusedForm=True: apply Hector Martinez Alonso's POS preference rules: cf.
          https://bitbucket.org/emnlp/text2depparse/src/86428c9e61b4e532958f23245060c3203a7a6a02/source/conllu2pos_parse_input.py?at=master&fileviewer=file-view-default
        """

        # read in all data first
        instances = []
        sentence = []
        for conll_line in conll_path.open():
            if conll_line.startswith("#"): #ignore comments
                continue
            parts = conll_line.strip().split()
            if len(parts)>10:
                parts = parts[:11] #ignore additional columns (secondary edges etc)
            if len(parts) in (8, 10):
                token = dict(zip(CONLL06_COLUMNS, parts))
                ptoken = ParsedToken(token)
                sentence.append(ptoken)
            elif len(parts) == 0:
                instances.append(sentence)
                sentence = []
            else:
                raise Exception("Invalid input format in line: ", conll_line)

        if sentence:
            instances.append(sentence)
            sentence = []

        # create graphs
        trees = []

        for instance in instances:
            sent_graph = DependencyTree() #node: node 0 will be root (added by add_edge)

            newTokens=[]
            refTokens=[t for t in instance if not t.fused] # original non-fused token ids (no root!)

            i = 0
            keptindices = []
            skippedindices = {}
            while i < len(instance):
                token = instance[i]

                if not keepFusedForm:
                    i+=1
                    if token.fused:
                        continue
                    sent_graph.add_node(token.id,token.to_dict())
                    sent_graph.add_edge(token.head, token.id, deprel=token.deprel)
                else:
                    # handling of fused forms
                    if token.fused:
                        startpos = refTokens[token.start-1].cpos
                        endpos = refTokens[token.end-1].cpos
                        ## check which has preference

                        try:
                            #print(startpos, endpos, token.start, token.end)
                            if posPreferenceDict[lang].index(startpos) < posPreferenceDict[lang].index(endpos):
                                head_syntax_t = refTokens[token.start-1]
                            else:
                                head_syntax_t = refTokens[token.end-1]
                        except:
                            print("Except",token)

                        # new form and lemma is fused form
                        head_syntax_t.form = token.form
                        head_syntax_t.lemma = token.lemma

                        i = i + 1 + 1 + token.end - token.start  #jump over skipped form
                        newTokens.append(head_syntax_t)
                        keptindices.append(head_syntax_t.id)
                        # store head of skipped tokens
                        for skipped in range(token.start,token.end+1):
                            skippedindices[(str(skipped))]=head_syntax_t.id
                    else:
                        newTokens.append(token)
                        keptindices.append(token.id)
                        i+=1

            if keepFusedForm:
                for t in newTokens:
                    if not skippedindices:
                        sent_graph.add_node(t.id,t.to_dict())
                        sent_graph.add_edge(t.head, t.id, deprel=t.deprel)
                    else:
                        #instance has fused forms
                        t.id = keptindices.index(t.id)+1
                        if t.head == 0:
                            pass
                        elif t.head in skippedindices:
                            t.head = keptindices.index(skippedindices[t.head])+1
                        else:
                            t.head = keptindices.index(t.head)+1
                        sent_graph.add_node(t.id,t.to_dict())
                        sent_graph.add_edge(t.head, t.id, deprel=t.deprel)

            trees.append(sent_graph)

        return trees

class ParsedToken(object):
    """
    class used for reading in data
    """
    def __init__(self,token):
        try:
            self.id = int(token['id'])
            self.head = int(token['head'])
            self.fused = False
        except ValueError:
            self.head = None # fused tokens need to determine head (see read_conll_u)
            self.fused = True
            assert(len(token['id'].split("-"))==2)
            self.start = int(token['id'].split("-")[0])
            self.end = int(token['id'].split("-")[1])
            self.id = self.start
        self.form = token['word']
        self.lemma = token['lemma']
        self.cpos = token['cpos']
        self.pos = token['pos']
        self.feats = token['feats']
        self.deprel = token['deprel']

    def __str__(self):
        return str(self.id)+" "+self.form

    def to_dict(self):
        return {'id': self.id, 'word':self.form, 'lemma': self.lemma, 'cpos': self.cpos, 'pos': self.pos, 'feats': self.feats, 'head': self.head, 'deprel': self.deprel}
