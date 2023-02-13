# MFLIB Measurement Framework Library
Welcome to the FABRIC Measurement Framework Library. MFLib makes it easy to install monitoring systems to a FABRIC experimenter's slice. The monitoring system makes extensive use of industry standards such as Prometheus, Grafana, Elastic Search and Kibana while adding customized monitoring tools and dashboards for quick setup and visualization.

## Documentation Resources
For more information about FABRIC vist [fabric-testbed.net](https://fabric-testbed.net/)
### Example Jupyter Notebooks
[FABRIC Jupyter Examples](https://github.com/fabric-testbed/jupyter-examples) GitHub repository contains many examples for using FABRIC from simple slice setup to advanced networking setups. Look for the MFLib section. These notebooks are designed to be easily used on the [FABRIC JupyterHub](https://jupyter.fabric-testbed.net/)

### FABRIC Learn Site
[FABRIC Knowledge Base](https://learn.fabric-testbed.net/) 

### MFLib Python Package Documentation
See [MFLib.pdf](https://github.com/fabric-testbed/mflib/blob/main/MFLib.pdf) for package documentation.

## MFLib Installation

MFLib may be installed using PIP and PyPI [fabrictestbed-mflib](https://pypi.org/fabrictestbed-mflib)
`pip install --user fabrictestbed-mflib`

### Installing via Source Code
If you need a development version, clone the git repo, then use pip to install.
```
git clone https://github.com/fabric-testbed/mflib.git
cd mflib
pip install --user .
```
## Building & Deploying
### Spinx Documentation
This package is documented using sphinx. The `source` directories are already created and populated with reStructuredText ( .rst ) files. The `build` directories are deleted and/or are not included in the repository,

#### Build HTML Documents

Install the extra packages required to build API docs: (sphinx, furo
theme, and myst-parser for parsing markdown files):

```console
$ pip install -r docs/requirements.txt
```

Build the documentation by running the following command from the root directory of the repo.
`sphinx-build -b html docs/source/ docs/build/html`  
The completed documentation may be accessed by clicking on `/docs/build/html/index.html`

#### Build PDF Document
Latex must be installed. For Debian use: 
```
sudo apt install texlive-latex-extra 
sudo apt install latexmk
```
Run the bash script to create the MFLIB.pdf documentation. MFLIB.pdf will be placed in the root directory of the repository.
`./create_pdf_doc.sh`
#### Building Distribution Package

To build python package for PyPi run  
`python setup.py sdist`
#### Uploading to PyPI
First test the package by uploading to test.pypi.org then test the install.
`twine upload --repository-url https://test.pypi.org/legacy/ dist/*`
Once install is good, upload to PiPy  
`twine upload dist/*`
