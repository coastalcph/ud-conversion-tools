from __future__ import print_function, division
import networkx as nx


CONLL06_COLUMNS = ['id', 'form', 'lemma', 'cpostag', 'postag', 'feats', 'head', 'deprel', 'phead', 'pdeprel']


def head_of(sent, n):
    for u, v in sent.edges():
         if v == n:
             return u
    return None
    #return sent.predecessors(n)[0]


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



CONLL_U_COLUMNS = [('id', parse_id), ('form', str), ('lemma', str), ('cpostag', str),
                   ('postag', str), ('feats', parse_feats), ('head', parse_id), ('deprel', str),
                   ('deps', parse_deps), ('misc', str)]

CONLL_U_COLUMNS = [('id', parse_id), ('form', str), ('lemma', str), ('cpostag', str),
                   ('postag', str), ('feats', str), ('head', parse_id), ('deprel', str),
                   ('deps', parse_deps), ('misc', str)]


def read_conll_u_file(filename):
    sentences = []
    sent = nx.DiGraph()
    multi_tokens = {}

    for line_no, line in enumerate(open(filename), 1):
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
            sent = nx.DiGraph()
        elif line.startswith("#"):
            if 'comment' not in sent.graph:
                sent.graph['comment'] = [line]
            else:
                sent.graph['comment'].append(line)
        else:
            parts = line.split("\t")
            if len(parts) != len(CONLL_U_COLUMNS):
                error_msg = 'Invalid number of columns in line {} (found {}, expected {})'.format(line_no, len(parts), len(CONLL_U_COLUMNS))
                raise Exception(error_msg)

            token_dict = {key: conv_fn(val) for (key, conv_fn), val in zip(CONLL_U_COLUMNS, parts)}
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


def featstostring(featsdict):
    acc = []
    for featname in sorted(featsdict.keys()):
        acc.append(featname+"="+featsdict[featname])

    if acc:
        return "|".join(acc)
    else:
        return "_"

def write_conll_2006(list_of_graphs, conll_path):
    with open(conll_path,'w') as out:
        for sent_i, sent in enumerate(list_of_graphs):
            if sent_i > 0:
                print("", file=out)
            for token_i in range(1, max(sent.nodes()) + 1):
                token_dict = dict(sent.node[token_i])
                head_i = head_of(sent, token_i)
                token_dict['head'] = head_i
                # print(head_i, token_i)
                token_dict['deprel'] = sent[head_i][token_i]['deprel']
                token_dict['id'] = token_i
                token_dict['feats'] = "_"

                row = [str(token_dict.get(col, '_')) for col in CONLL06_COLUMNS]
                print(u"\t".join(row), file=out)

        # emtpy line afterwards
        print(u"", file=out)


def write_sentence_conll2006(sent):
    if 'comment' in sent.graph:
        for commentline in sent.graph['comment']:
            print(commentline)
    for token_i in range(1, max(sent.nodes()) + 1):
        token_dict = dict(sent.node[token_i])
        head_i = head_of(sent, token_i)
        token_dict['head'] = head_i
        # print(head_i, token_i)
        token_dict['deprel'] = sent[head_i][token_i]['deprel']
        token_dict['id'] = token_i
        #token_dict['feats'] = featstostring(sent.node[token_i]["feats"])
        token_dict['feats'] = sent.node[token_i]["feats"]

        row = [str(token_dict.get(col, '_')) for col in CONLL06_COLUMNS]
        if token_i in sent.graph["multi_tokens"]:
            currentmulti = sent.graph["multi_tokens"][token_i]
            currentmulti["id"]=str(currentmulti["id"][0])+"-"+str(currentmulti["id"][1])
            currentmulti["feats"]="_"
            currentmulti["head"]="_"

            rowmulti = [str(currentmulti.get(col, '_')) for col in CONLL06_COLUMNS]
            print(u"\t".join(rowmulti))
        print(u"\t".join(row))
    print()