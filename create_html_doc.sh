#! /bin/bash

echo "Has the version in mflib/__init__py been correctly increased?"
read -p "WARNING: this script DELETES all files in docs/build/html directories. Do you want to continue? [yN]:  " -n 1 -r 
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then

    echo "***** Removing older html doc files... *****"
    rm -rf docs/build/html
    echo ""
    echo "***** Building HTML documentation files... *****"
    sphinx-build -b html docs/source/ docs/build/html
    echo ""

    # Make a copy to include in git repo
    # echo "***** Removing older copy of html doc files... *****"
    # rm -rf docs/html/*
    # echo "Copying HTML to main directory."
    # cp docs/build/html/*.html docs/html
    # cp docs/build/html/*.js docs/html
    # cp -R docs/build/html/_static docs/html


else
    echo "Aborting, nothing done."
fi