# MFLIB Measurement Framework Library


## Installing via PyPI

MFLib may be installed using pip. 
`pip install --user ???`

## Installing via Source Code
Clone the git repo, then use pip to install.
```
git clone https://github.com/fabric-testbed/mflib.git
cd mflib
pip install --user .
```

## Spinx Documentation
This package is documented using sphinx. The source directories are already created and populated with .ReST files.
The sphinx theme furo is used. This may need to be installed using `pip install furo`  
To parse the markdown files (README.md) sphinx needs myst-parser. `pip install myst-parser` 
Build the documentation by running the following command from the root directory of the repo.
`sphinx-build -b html docs/source/ docs/build/html`  
The completed documentation may be shown by clicking on `/docs/build/html/index.html`
