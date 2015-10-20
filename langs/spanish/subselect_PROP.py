
import nltk, re

stoplist = list(nltk.corpus.stopwords.words())+ "& bajo al".split(" ")
romans = re.compile("^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")

for line in open("PROPNlist").readlines():
    line = line.strip()
    freq, word, POS, underscore = line.split()
    newPOS = "PROPN"
    newfeats = "_"
    newlabel = "_"
    if word.lower() in stoplist:
        #print(word)
        newPOS = "STOP"
    elif "'" in word and len(word) < 4:
        #print(word)
        newPOS = "STOP"

    #  elif set(word).intersection(set(["0","1","2","3","4","5","6","7","8","9"])):
   #      print(word)
   #  elif romans.search(word):
   #      print(word)

    if newPOS != POS:
        outline = "\t".join([freq, word, POS, underscore, newPOS, newfeats, newlabel])
        print(outline)