#! /bin/bash

echo "Has the version in mflib/__init__py been correctly increased?"
read -p "WARNING: this script DELETES all files in dist directory. Do you want to continue? Type Y or y:  " -n 1 -r 
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then

    echo "***** Removing older dist files... *****"
    rm dist/mflib*
    echo ""
    echo "***** Building mflib package dist tar file. *****"
    python setup.py sdist
    echo "***** Done *****"

    echo "***** To test PyPi release upload use 'flit publish --repository testpypi' *****"
    echo "***** To push the release to PyPi use: 'flit publish --repository pypi' "
else
    echo "Aborting, nothing done."
fi