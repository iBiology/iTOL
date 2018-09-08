====
iTOL
====


    * `About`_
    * `Installation`_
    * `Usage`_
        * `From Shell`_
        * `From Python`_
    * `Bugs and Comments`_
    * `Bugs and Comments`_

About
=====

`iTOL` provides a Python API and a command-line tool for the Tree of Life (`iTOL <http://iTOL.embl.de>`_).

This API is intentionally designed for interacting with iTOL server. The author suggests use this
API to handle big datasets or programmatically manipulated phylogenetic trees and associated
annotation datasets. The API allows users interact with iTOL server using Python or shell. In order
to visualize your data, an active internet connection to iTO server is required.


Installation
============

``iTOL`` has been uploaded to `PyPI <https://pypi.org/>`_, so the easiest way to install it is via ``pip``:

.. code-block:: shell

    pip install iTOL


Usage
=====

From Shell
----------

If you only want to upload/download existing tree file and/or associated dataset files, you are
encouraged to use the command-line tool ``itol`` from a shell.

Check the usage of command-line too ``itol`` first::

    $ itol -h
    usage: itol DATA [OPTIONS]

    Command line tool for ITOL (http://itol.embl.de) bach access.

    positional arguments:
      DATA                A tree file name, a ZIP file name, a tree ID or URL.

    optional arguments:
      -h, --help          show this help message and exit
      -i uploadID         Your upload ID (ID for batch uploading).
      -n treeName         The name you assigned to the tree.
      -p projectName      Project name, required if uploadID is assigned.
      -d treeDescription  Description of your tree.
      -f F                Output file format, default: pdf. Graphical formats:
                          svg, eps, pdf and png; text formats: newick, nexus and
                          phyloxml
      -o O                Path of the output file.
      -a                  Force zip all text files along with the tree file.

Upload a tree file to iTOL server::

    $ itol /path/to/tree_file

Upload a tree file to iTOL server and using a uploadID and project name::

    $ itol /path/to/tree_file -i uploadID -p project_name

Upload a tree file to iTOL server and using a uploadID, project name and assign a tree name::

    $ itol /path/to/tree_file -i uploadID -p project_name -n tree_name

Upload a tree file to iTOL server and using a uploadID, project name and, tree name and a tree
description::

    $ itol /path/to/tree_file -i uploadID -p project_name -n tree_name -d tree_description

Download a image of a tree from iTOL server using treeID::

    $ itol treeID

Download a image of a tree from iTOL server using tree URL::

    $ itol tree_URL

Download a image of a tree from iTOL server using tree URL and save in ``png`` format::

    $ itol tree_URL -f png

Download a image of a tree from iTOL server using tree URL and save in ``png`` format with name of
``iTOL.png``::

    $ itol tree_URL -f png -o iTOL.png

Download a image of a tree from iTOL server and display it in circular mode::

    $ itol tree_URL --display_mode 2

Download a image of a tree from iTOL server, display it in circular mode and make the first dataset
visible::

    $ itol tree_URL --display_mode 2 --datasets_visible 0


From Python
-----------

Using ``iTOL`` module from Python Shell or script is much more flexible than using the command-line
tool from shell and users are able to access all methods for generating annotation files and interact
with iTOL server inside python.

.. code-block:: python

    from iTOL import TOL

    # Initiate the base class by providing a tree file and work directory (not always necessary)
    t = TOL(tfile='path/to/tree_file', wd='path/to/work/directory')

    # Data for coloring the tree
    data = [
            (8518, 'label', '#0000ff'),
            ('6529', 'label', '#00ff00', 'bold', '2'),
            (6321, 'label', '#ff8000', 'bold-italic', 0.5),
            ('6529|8463', 'clade', '#0000ff', 'normal', 3),
            ('8090|8033', 'clade', '#ff0000', 'dashed', 0.5),
            ('7539|1744', 'branch', '#00ff00', 'dashed', 5),
            ('5784|7550', 'range', '#ff0000', 'Group A'),
            ('7396|2154', 'range', '#aaffaa', 'Group B'),
            ('2055|539', 'range', '#aaaaff', 'Group C')
            ]

    # Generating annotation file for color setting
    t.color(data)

    # Data for making pie chart
    data = [(8518, -1, 30, 20, 32, 50), ('6529', 0.5, 20, 33, 23, 46), (6321, 1, 15, 18, 40, 35)]

    # Generating annotation file for pie char
    t.pie(data)

    # Upload the tree and the generated annotation files to iTOL server
    t.upload(uid='You upload ID', tn='tree Name', pn='project name', td='tree description')

    # Download the tree image (using default name and default format)
    t.download()

    # Download the tree image in png format and save it to iTOL.png
    t.download(fmt='png', outfile='iTOL.png')

    # Download the tree image display in circular mode, both datasets visible,and save it to
    # iTOL.png file in png format
    t.download(fmt='png', outfile='iTOL_visible.png', display_mode=2, datasets_visible='0,1')

Since using ``iTOL`` module in Python is more flexible, users are strongly encouraged to check
out the ``examples``
directory for more examples.


Bugs and Comments
=================

Please send bugs and comments as issues to the `Github <https://github.com/iBiology/iTOL>`_
repository of this module.


Development
===========

Users or developers are **NOT** encouraged to directly run the example code stored in the
``examples`` directory. If you want to run these codes to test `iTOL`, the author **STRONGLY**
suggest that you create an account on iTOL website, and replace the upload ID in these examples.
Without replacing the upload ID, you may upload all your data into a Demo or Program project
set by the author and mess up the whole project.
