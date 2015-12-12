from collections import defaultdict
import networkx as nx
from collections import Counter


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
                out.append(str(token_i)+":"+self.node[token_i]['form'])
            else:
                out.append(self.node[token_i]['form'])
        return u" ".join(out)

    def subsumes(self, head, child):
        if head in self.pathtoroot(self, child):
            return True

    def get_highest_index_of_span(self, span):  # retrieves the node index that is closest to root
        #TODO: CANDIDATE FOR DEPRECATION
        distancestoroot = [len(self.pathtoroot(self, x)) for x in span]
        shortestdistancetoroot = min(distancestoroot)
        spanhead = span[distancestoroot.index(shortestdistancetoroot)]
        return spanhead


    def get_deepest_index_of_span(self, span):  # retrieves the node index that is farthest from root
        #TODO: CANDIDATE FOR DEPRECATION
        distancestoroot = [len(self.pathtoroot(self, x)) for x in span]
        longestdistancetoroot = max(distancestoroot)
        lownode = span[distancestoroot.index(longestdistancetoroot)]
        return lownode

    def get_unique_highest_node(self,span):
        distancestoroot = [len(nx.ancestors(self,x)) for x in span]
        shortestdistancetoroot = min(distancestoroot)
        distance_counter = Counter(distancestoroot)
        if distance_counter[shortestdistancetoroot] == 1:
            spanhead = span[distancestoroot.index(shortestdistancetoroot)]
            return spanhead
        else:
            #there is no clear head candidate and we have to resort to POS heuristics
            return None

    def span_makes_subtree(self, initidx, endidx):
        G = nx.DiGraph()
        span_nodes = list(range(initidx,endidx+1))
        span_words = [self.node[x]["form"] for x in span_nodes]
        G.add_nodes_from(span_nodes)
        for h,d in self.edges():
            if h in span_nodes and d in span_nodes:
                G.add_edge(h,d)
        return nx.is_tree(G)

    def _choose_spanhead_from__heuristics(self,span_nodes,pos_precedence_list):
        #TODO ADD POS heuristics
        #TODO ADD deprel heuristics
        best_rank = len(pos_precedence_list) + 1
        candidate_head = - 1
        span_upos  = [self.node[x]["cpostag"]for x in span_nodes]
        for upos, idx in zip(span_upos,span_nodes):
            if pos_precedence_list.index(upos) < best_rank:
                best_rank = pos_precedence_list.index(upos)
                candidate_head = idx
        return candidate_head


    def _remove_node_properties(self,fields):
        for n in sorted(self.nodes()):
            for fieldname in self.node[n].keys():
                if fieldname in fields:
                    self.node[n][fieldname]="_"

    def _remove_label_suffixes(self):
        for h,d in self.edges():
            if ":" in self[h][d]["deprel"]:
                self[h][d]["deprel"]=self[h][d]["deprel"].split(":")[0]

    def _keep_fused_form(self):


        # For a span A,B  and external tokens C, such as  A > B > C, we have to
        # Make A the head of the span
        # Attach C-level tokens to A
        #Remove B-level tokens, which are the subtokens of the fused form della: de la

        if self.graph["multi_tokens"] == {}:
            return

        changes = False
        for fusedform_idx in sorted(self.graph["multi_tokens"]):
            fusedform = self.graph["multi_tokens"][fusedform_idx]["form"]
            fusedform_start, fusedform_end = self.graph["multi_tokens"][fusedform_idx]["id"]
            fuseform_span = list(range(fusedform_start,fusedform_end+1))
            spanhead = self.get_unique_highest_node(fuseform_span) # N.B. no need for the subspan to be a tree if there is one single highest element
            if not spanhead:
                spanhead = self._choose_spanhead_from_POS_heuristics(fuseform_span)
            if spanhead:
                changes = True
                #print(spanhead, self.node[spanhead]["form"],fusedform,self.get_sentence_as_string())

                #Step 1: Replace form of head span (A)  with fusedtoken form  -- in this way we keep the lemma and features if any
                self.node[spanhead]["form"] = "###"+fusedform
                # 2-  Reattach C-level (external dependents) to A
                #print(fuseform_span,spanhead)

                internal_dependents = set(fuseform_span) - set([spanhead])
                external_dependents = [nx.bfs_successors(self,x) for x in internal_dependents]
                for depdict in external_dependents:
                    for localhead in depdict:
                        for ext_dep in depdict[localhead]:
                            deprel = self[localhead][ext_dep]["deprel"]
                            self.remove_edge(localhead,ext_dep)
                            self.add_edge(spanhead,ext_dep,deprel=deprel)

                #3- Remove B-level tokens
                for int_dep in internal_dependents:
                    self.remove_edge(self.head_of(int_dep),int_dep)
                    self.remove_node(int_dep)
                    #self.node[int_dep]["form"]="REMOVED"
                    #self.add_edge(0,int_dep,deprel="REMOVED")

        #4- reconstruct tree at the very end
        new_index_dict = {}
        for new_node_index, old_node_idex in enumerate(sorted(self.nodes())):
            new_index_dict[old_node_idex] = new_node_index

        T = DependencyTree() # Transfer DiGraph, to replace self

        for n in sorted(self.nodes()):
            T.add_node(new_index_dict[n],self.node[n])

        for h, d in self.edges():
            T.add_edge(new_index_dict[h],new_index_dict[d],deprel=self[h][d]["deprel"])


        #Quick removal of edges and nodes
        self.__init__()

        #Rewriting the Deptree in Self
        #TODO There must a more elegant way to rewrite self -- self= T for instance?
        for n in sorted(T.nodes()):
            self.add_node(n,T.node[n])

        for h,d in T.edges():
            self.add_edge(h,d,T[h][d])

        #5. remove all fused forms form the multi_tokens field
        self.graph["multi_tokens"] = {}
        print(nx.is_tree(self))


    def filter_sentence_content(self,keepFusedForm=False, lang=None, posPreferenceDict=None,node_properties_to_remove=None):
        if keepFusedForm:
            self._keep_fused_form()
        if node_properties_to_remove:
            self._remove_node_properties(node_properties_to_remove)



class CoNLLReader(object):
    """
    conll input/output
    """

    "" "Static properties"""
    CONLL06_COLUMNS = ['id', 'form', 'lemma', 'cpostag', 'postag', 'feats', 'head', 'deprel', 'phead', 'pdeprel']
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
        return sentences


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
