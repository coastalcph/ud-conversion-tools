from collections import defaultdict
import networkx as nx


def parse_id(id_str):
    if id_str == '_':
        return None
    ids = tuple(map(int, id_str.split("-")))
    if len(ids) == 1:
        return ids[0]
    else:
        return ids

def parse_feats(feats_str):
    if feats_str == '_':
        return {}
    feat_pairs = [pair.split("=") for pair in feats_str.split("|")]
    return {k: v for k, v in feat_pairs}

def parse_deps(dep_str):
    if dep_str == '_':
        return []
    dep_pairs = [pair.split(":") for pair in dep_str.split("|")]
    return [(int(pair[0]), pair[1]) for pair in dep_pairs]




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




class CoNLLReader(object):
    """
    conll input/output
    """

    "" "Static properties"""
    CONLL06_COLUMNS = ['id', 'form', 'lemma', 'cpos', 'pos', 'feats', 'head', 'deprel', 'phead', 'pdeprel']
    CONLL_U_COLUMNS = [('id', parse_id), ('form', str), ('lemma', str), ('cpostag', str),
                   ('postag', str), ('feats', str), ('head', parse_id), ('deprel', str),
                   ('deps', parse_deps), ('misc', str)]

    def __init__(self):
        pass


    def read_conll_2006(self, conll_path):
        sent = DependencyTree()

        for conll_line in conll_path.open():
            parts = conll_line.strip().split()
            if len(parts) in (8, 10):
                token = dict(zip(self.CONLL06_COLUMNS, parts))
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
                    row = [str(token_dict.get(col, '_')) for col in self.CONLL06_COLUMNS]
                    print(u"\t".join(row), file=out)
                    #TODO the write method ONLY has to write, not to modify the trees. We will this in _filter_sentence_content
                    if token_i in sent.graph["multi_tokens"]:
                        currentmulti = sent.graph["multi_tokens"][token_i]
                        currentmulti["id"]=str(currentmulti["id"][0])+"-"+str(currentmulti["id"][1])
                        currentmulti["feats"]="_"
                        currentmulti["head"]="_"
                        rowmulti = [str(currentmulti.get(col, '_')) for col in self.CONLL06_COLUMNS]
                        print(u"\t".join(rowmulti),file=out)
            print(u"\t".join(row),file=out)
            # emtpy line afterwards
            print(u"", file=out)

    def _remove_fields(self,sent,fields):
        #TODO remove fx "form" and "label"

        return sent

    def _keep_label_prefixes(self,sent):
        #TODO nmod:tmod --> nmod

        return sent

    def _keep_fused_form(self,sent):
        for fusedform in sent.graph["multi_tokens"]:
                print(sent.graph["multi_tokens"][fusedform])
        return sent


    def _filter_sentence_content(self,sent_deptree,keepFusedForm=False, lang=None, posPreferenceDict=None):
        if keepFusedForm:
            sent = self._keep_fused_form(sent_deptree)
        return sent_deptree

    def read_conll_u(self,filename,keepFusedForm=False, lang=None, posPreferenceDict=None):
        sentences = []
        sent = DependencyTree()
        multi_tokens = {}

        for line_no, line in enumerate(open(filename).readlines()):
            line = line.strip("\n")
            if not line:
                # Add extra properties to ROOT node if exists
                if 0 in sent:
                    for key in ('form', 'lemma', 'cpostag', 'postag'):
                        sent.node[0][key] = 'ROOT'

                # Handle multi-tokens
                sent.graph['multi_tokens'] = multi_tokens
                multi_tokens = {}
                sentences.append(sent)
                sent = DependencyTree()
            elif line.startswith("#"):
                if 'comment' not in sent.graph:
                    sent.graph['comment'] = [line]
                else:
                    sent.graph['comment'].append(line)
            else:
                parts = line.split("\t")
                if len(parts) != len(self.CONLL_U_COLUMNS):
                    error_msg = 'Invalid number of columns in line {} (found {}, expected {})'.format(line_no, len(parts), len(CONLL_U_COLUMNS))
                    raise Exception(error_msg)

                token_dict = {key: conv_fn(val) for (key, conv_fn), val in zip(self.CONLL_U_COLUMNS, parts)}
                if isinstance(token_dict['id'], int):
                    sent.add_edge(token_dict['head'], token_dict['id'], deprel=token_dict['deprel'])
                    sent.node[token_dict['id']].update({k: v for (k, v) in token_dict.items()
                                                        if k not in ('head', 'id', 'deprel', 'deps')})
                    for head, deprel in token_dict['deps']:
                        sent.add_edge(head, token_dict['id'], deprel=deprel, secondary=True)
                else:
                    #print(token_dict['id'])
                    first_token_id = int(token_dict['id'][0])
                    multi_tokens[first_token_id] = token_dict
        return [self._filter_sentence_content(s,keepFusedForm,lang,posPreferenceDict) for s in sentences]


    def read_conll_u_old(self, conll_path, keepFusedForm=False, lang=None, posPreferenceDict=None):
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
                token = dict(zip(self.CONLL06_COLUMNS, parts))
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

                        print(span_makes_subtree(instance,token.start,token.end))

                        try:
                            #print(startpos, endpos, token.start, token.end)
                            if posPreferenceDict[lang].index(startpos) < posPreferenceDict[lang].index(endpos):
                                head_syntax_t = refTokens[token.start-1]
                            else:
                                head_syntax_t = refTokens[token.end-1]
                        except:
                            print("Except",token)
                            head_syntax_t= refTokens[token.start-1] #Patch

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
                            try:
                                t.head = keptindices.index(t.head)+1
                            except:
                                print(t, token, keptindices)
                        sent_graph.add_node(t.id,t.to_dict())
                        sent_graph.add_edge(t.head, t.id, deprel=t.deprel)

            trees.append(sent_graph)

        return trees


def span_makes_subtree(sent_graph, initidx, endidx):
    G = nx.Graph()
    try:
        span_nodes = list(range(initidx,endidx+1))
        span_words = [sent_graph.node[x]["form"] for x in span_nodes]
        print(sent_graph,span_nodes)
    except:
        print(sent_graph.nodes())

    G.add_nodes_from(span_nodes)
    for h,d in sent_graph.edges():
        if h in span_nodes and d in span_nodes:
            G.add_edge(h,d)
    return span_words,span_nodes,nx.is_tree(G)


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
