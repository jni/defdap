# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import shutil
sys.path.insert(0, os.path.abspath('../../')) 	# Reference the root directory so autodocs can find the python modules

# Copy the example notebook, change %matplotlib to inline and change directory so that paths still work
shutil.copyfile('../../notebooks/example_notebook.ipynb', 'howtouse.ipynb')
with open('howtouse.ipynb') as f:
    newText=f.read().replace('%matplotlib tk', r'%matplotlib inline\n%cd -q ../../')
newText=newText.replace('DefDAP Example notebook', r'How to use')
newText=newText.replace('This notebook', r'These pages')
with open('howtouse.ipynb', "w") as f:
    f.write(newText)

# -- Project information -----------------------------------------------------

project = 'DefDAP'
copyright = '2020, Mechanics of Microstructures Group at The University of Manchester'
author = 'Michael D. Atkinson, Rhys Thomas, João Quinta da Fonseca'


def get_version():
    ver_path = '../../defdap/_version.py'
    main_ns = {}
    with open(ver_path) as ver_file:
        exec(ver_file.read(), main_ns)

    return main_ns['__version__']


# The full version, including alpha/beta/rc tags
release = get_version()
# The short X.Y version
version = '.'.join(release.split('.')[:2])

# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx_autodoc_typehints',
    'sphinx_rtd_theme',
    'nbsphinx'
]

nbsphinx_allow_errors = True
nbsphinx_execute = 'always'
nbsphinx_prolog = """
This page was built from the example_notebook Jupyter notebook available on `Github <https://github.com/MechMicroMan/DefDAP>`_

.. image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/MechMicroMan/DefDAP/master?filepath=example_notebook.ipynb

----
"""

napoleon_use_param = True
#set_type_checking_flag = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = 'en'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'defdap/defdap.rst']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
  }

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'DefDAPdoc'


# -- Generate API docs during sphinx-build (for readthedocs) ------------------

# Determine if on RTD
ON_RTD = (os.environ.get('READTHEDOCS') == 'True')

def run_apidoc(_):

    from sphinx.ext import apidoc

    api_args = [
            '--force',
            '--separate',                   # Put each module on seperate page
            '--no-toc',                     # No table of contents
            '../../defdap',                 # Module path
            '-o',                           # Directory to output..
            '../source/defdap'              # here
            ]

    # Invoke apidoc
    apidoc.main(api_args)  

def setup(app):
    if ON_RTD:
        app.connect('builder-inited', run_apidoc)

# -- Extension configuration -------------------------------------------------

autodoc_member_order = 'bysource'
intersphinx_mapping = {'python': ('https://docs.python.org/3.7/', None),
                       'numpy': ('https://numpy.org/doc/stable/', None),
                       'scipy': ('https://docs.scipy.org/doc/scipy/reference/', None),
                       'matplotlib': ('https://matplotlib.org/', None),
                       'skimage': ('https://scikit-image.org/docs/dev/', None)}