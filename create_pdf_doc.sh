#! /bin/bash

echo "Has the version in mflib/__init__py been correctly increased?"
read -p "WARNING: this script DELETES all files in docs/build/pdf directories. Do you want to continue? [yN]:  " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "***** Removing older pdf doc files... *****"
    rm -rf docs/build/latex
    echo ""
    echo "***** Building PDF documentation files... *****"
    # Note: Have to run make twice to generate the table of contents and index.
    make -C docs/ latexpdf
    make -C docs/ latexpdf
    echo "Copying PDF to main directory."
    cp docs/build/latex/mflib.pdf MFLib.pdf
    echo "***** Done *****"
else
    echo "Aborting, nothing done."
fi