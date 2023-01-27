# MFLIB Measurement Framework Library


## Installing via PyPI & PIP 

MFLib may be installed using pip. 
`pip install --user fabrictestbed-mflib`

## Installing via Source Code
If you need a development version, clone the git repo, then use pip to install.
```
git clone https://github.com/fabric-testbed/mflib.git
cd mflib
pip install --user .
```
### Building Distrubution Package

To build python package for PyPi run  
`python setup.py sdist`

##### Uploading to PyPI
First test the package by uploading to test.pypi.org then test the install.
`twine upload --repository-url https://test.pypi.org/legacy/ dist/*`
Once install is good, upload to PiPy  
`twine upload dist/*`

## Spinx Documentation
This package is documented using sphinx. The source directories are already created and populated with reStructuredText ( .rst ) files.
The sphinx theme furo is used. This may need to be installed using  
`pip install furo`   
To parse the markdown files (README.md) sphinx needs myst-parser.   
`pip install myst-parser`   
Build the documentation by running the following command from the root directory of the repo.
`sphinx-build -b html docs/source/ docs/build/html`  
The completed documentation may be shown by clicking on `/docs/build/html/index.html`


