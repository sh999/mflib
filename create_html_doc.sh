#! /bin/bash

echo "Has the version in mflib/__init__py been correctly increased?"
read -p "WARNING: this script DELETES all files in docs/build/html directories. Do you want to continue? Type Y or y:  " -n 1 -r 
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then

    echo "***** Removing older html doc files... *****"
    rm -rf docs/build/html
    echo ""
    echo "***** Building HTML documentation files... *****"
    sphinx-build -b html docs/source/ docs/build/html
    echo ""
    
else
    echo "Aborting, nothing done."
fi