#!/bin/bash
# create a directory of samples of covers with drop-downs
# it is assumened that the program is add_dropdows_to_DOCX_file.py
# it is assumened that z6.docx contain a saved version of the English covers
# it is assumened that z7.docx contain a saved version of the Swedish covers
mkdir Some_examples
cd Some_examples
cp ../z6.docx .
cp ../z7.docx .
#
../add_dropdows_to_DOCX_file.py --file z6.docx --exam högskoleexamen
../add_dropdows_to_DOCX_file.py --file z7.docx --exam högskoleexamen --language sv
#
../add_dropdows_to_DOCX_file.py --file z6.docx --exam kandidatexamen
../add_dropdows_to_DOCX_file.py --file z7.docx --exam kandidatexamen --language sv
#
../add_dropdows_to_DOCX_file.py --file z6.docx --exam högskoleingenjörsexamen
../add_dropdows_to_DOCX_file.py --file z7.docx --exam högskoleingenjörsexamen --language sv
#
../add_dropdows_to_DOCX_file.py --file z6.docx --exam civilingenjörsexamen
../add_dropdows_to_DOCX_file.py --file z7.docx --exam civilingenjörsexamen --language sv
#
../add_dropdows_to_DOCX_file.py --file z6.docx --exam magisterexamen
../add_dropdows_to_DOCX_file.py --file z7.docx --exam magisterexamen --language sv
#
../add_dropdows_to_DOCX_file.py --file z6.docx --exam masterexamen
../add_dropdows_to_DOCX_file.py --file z7.docx --exam masterexamen --language sv
#
../add_dropdows_to_DOCX_file.py --file z6.docx --exam arkitektexamen
../add_dropdows_to_DOCX_file.py --file z7.docx --exam arkitektexamen --language sv
#
../add_dropdows_to_DOCX_file.py --file z6.docx --exam ämneslärarexamen
../add_dropdows_to_DOCX_file.py --file z7.docx --exam ämneslärarexamen --language sv
#
../add_dropdows_to_DOCX_file.py --file z6.docx --exam CLGYM
../add_dropdows_to_DOCX_file.py --file z7.docx --exam CLGYM --language sv
#
../add_dropdows_to_DOCX_file.py --file z6.docx --exam KPULU
../add_dropdows_to_DOCX_file.py --file z7.docx --exam KPULU --language sv
#
../add_dropdows_to_DOCX_file.py --file z6.docx --exam both
../add_dropdows_to_DOCX_file.py --file z7.docx --exam both  --language sv
#
../add_dropdows_to_DOCX_file.py --file z6.docx --exam same
../add_dropdows_to_DOCX_file.py --file z7.docx --exam same --language sv
