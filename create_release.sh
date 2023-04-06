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
    flit build
    echo "***** Done *****"

    echo "***** To test PyPi release upload to twine using: twine upload --repository-url https://test.pypi.org/legacy/ dist/*"
    echo "***** To push the release to PyPi use: twine upload dist/*"
else
    echo "Aborting, nothing done."
fi