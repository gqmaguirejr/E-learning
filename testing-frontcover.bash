#!/bin/bash
# create a directory of samples of covers using frontcover.py
# and sone JSON files
[ -d Some_examples_of_covers ] || mkdir Some_examples_of_covers
#
./frontcover.py --json fordiva-example-högskoleexamen-tekink-swedish.json --pdf Some_examples_of_covers/högskoleexamen-tekink-swedish.pdf
#
./frontcover.py --json fordiva-example-högskoleingenjörsexamen-elektronik_och_datorteknik-swedish.json --pdf Some_examples_of_covers/högskoleingenjörsexamen-elektronik_och_datorteknik-swedish.pdf
#
./frontcover.py --json fordiva-example-kandidate-tekink-swedish.json --pdf Some_examples_of_covers/kandidate-tekink-swedish.pdf
#
./frontcover.py --json fordiva-example-högskoleingenjörsexamen-elektronik_och_datorteknik-swedish.json --pdf Some_examples_of_covers/högskoleingenjörsexamen-elektronik_och_datorteknik-swedish.pdf
#
./frontcover.py --json fordiva-example-civilingenjörsexamen-elektrotekink-swedish.json --pdf Some_examples_of_covers/civilingenjörsexamen-elektrotekink-swedish.pdf
#
./frontcover.py --json fordiva-example-magisterexamen-swedish.json --pdf Some_examples_of_covers/magisterexamen-swedish.pdf
#
./frontcover.py --json fordiva-example-masters-TCOMM.json --pdf Some_examples_of_covers/fordiva-example-masters-TCOMM.pdf
#
./frontcover.py --json fordiva-example-arkitektexamen-swedish.json --pdf Some_examples_of_covers/arkitektexamen-swedish.pdf
#
./frontcover.py --json fordiva-example-ämneslärarexamen-Technology_and_Learning.json --pdf Some_examples_of_covers/ämneslärarexamen-Technology_and_Learning.pdf
#
./frontcover.py --json fordiva-example-CLGYM-Technology_and_Learning.json --pdf Some_examples_of_covers/CLGYM-Technology_and_Learning.pdf
#
./frontcover.py --json fordiva-example-KPULU.json --pdf Some_examples_of_covers/KPULU.pdf
#
./frontcover.py --json fordiva-example-both.json --pdf Some_examples_of_covers/fordiva-example-both.pdf
#
./frontcover.py --json fordiva-example-same.json --pdf Some_examples_of_covers/same.pdf

