mkdir italian_split
python ../extract.py --mapping ITALIAN-mapping.txt ~/corpora/parse/universal-dependencies-1.2/UD_Italian/it-ud-test.conllu it-ud-test 2> italian.log
mv it-ud-test_* italian_split/

mkdir bulgarian_split
python ../extract.py --mapping BULGARIAN-mapping.txt ~/corpora/parse/universal-dependencies-1.2/UD_Bulgarian/bg-ud-test.conllu bg-ud-test 2> bulgarian.log
mv bg-ud-test_* bulgarian_split
