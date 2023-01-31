
#! /bin/bash

echo "Has the version in mflib/__init__py been correctly increased?"
read -p "WARNING: this script DELETES all files in docs/build/pdf directories. Do you want to continue? Type Y or y:  " -n 1 -r 
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "***** Removing older pdf doc files... *****"
    rm -rf docs/build/latex
    echo ""
    echo "***** Building PDF documentation files... *****"
    make -C docs/ latexpdf
    echo "Copying PDF to main directory."
    cp docs/build/latex/mflib.pdf MFLIB.pdf
    echo "***** Done *****"
else
    echo "Aborting, nothing done."
fi