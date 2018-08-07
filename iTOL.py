#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Python API for phylogenetic tree visualization in Interactive Tree of Life (ITOL, http://iTOL.embl.de).

This API allows user to quickly upload trees to iTOL and export uploaded trees using simple function calls within Python
IDE or script, and the same simple tasks can also be done from command line by invoking the corresponding options. Any
thing more than simply upload and export trees can be done by initializing the TOL class and then call various methods.
"""

import os
import sys
import shutil
from zipfile import ZipFile
import requests


DELIMITER = {'TAB': '\t', 'SPACE': ' ', 'COMMA': ','}
UPLOAD_URL = "http://itol.embl.de/batch_uploader.cgi"
DOWNLOAD_URL = "http://itol.embl.de/batch_downloader.cgi"


def _sd(data, separator):
    """
    Private function for handling separator and data block
    
    :param data: nested tuple or list. Each inner element should have at least 3 elements which define the node,
    type and color.
    :param separator: the separator which is used to delimit the setting text (tab, space or comma), default: comma.
    
    Note: Unlike writing iTOL setting file manually, the name of the separator here is case insensitive. However, you
    should always keep in mind that depend on your data, separator does matter.
    :return: formatted string.
    """

    if isinstance(separator, str):
        s = separator.upper()
        if s in DELIMITER:
            sep = 'SEPARATOR {}'.format(s)
        else:
            raise ValueError('Argument sep should be one of these: {} (case insensitive).'.format(', '.join(DELIMITER)))
    else:
        raise ValueError('Argument sep should be a string, e.g. tab, TAB, comma, COMMA, space or SPACE.')

    if isinstance(data, (list, tuple)):
        if all([1 if isinstance(e, (list, tuple)) else 0 for e in data]):
            data_block = [DELIMITER[s].join([str(e) for e in d]) for d in data]
        else:
            raise ValueError('Argument data should be a nested tuple or list consisting of tuples or lists.')
    else:
        raise ValueError('Argument data should be a nested tuple or list consisting of tuples or lists.')
    return '\n'.join(data_block), sep, s


def _args(args, data, separator, outfile, tag, wd):
    """
    Private function handling arguments parse and writing config file (user should not use this functionary directly).
    
    :param args: dict, all local keyword arguments.
    :param data: nested tuple or a list. Each inner element should have at least 3 elements which define the node,
    type and color.
    :param separator: the separator which is used to delimit the setting text (tab, space or comma), default: comma.
    Note: Not like writing iTOL setting file, the name of separator here is case insensitive. You should always keep
    in mind that depend on your data, separator does matter.
    :param outfile: str, name of the output file.
    :param tag: string, name tag of the config file.
    :param wd:, str, word directory.
    :return str, formatted text.
    """

    for arg in ('self', 'data', 'separator', 'outfile'):
        args.pop(arg)

    data_block, sep, delimiter = _sd(data, separator)
    setting_block = '\n'.join([DELIMITER[delimiter].join([k.upper(), str(v)]) for k, v in args.items() if v])

    if not isinstance(tag, str):
        raise ValueError('Argument tag should be a string!')
    text = '\n'.join([tag, sep, setting_block, 'DATA', data_block])

    if not isinstance(outfile, str):
        raise ValueError('Argument outfile should be a string!')

    if not outfile.endswith('.txt'):
        outfile = ''.join([outfile, '.txt'])

    with open(os.path.join(wd, outfile), 'w') as out:
        out.write(text)
        

class TOL(object):
    """
    Handling tree visualization in Interactive Tree of Life (iTOL, http://iTOL.embl.de).
    
    Method upload handles upload tree to iTOL and download handles figure download (or export). All other methods are
    designed to generate annotation files.
    
    Except upload and download methods, all other methods have a positional argument data which is a nested list
    consisting of tuples or lists. Elements in each inner tuple or list are described within each method. All these
    methods also have two common optional arguments, separator and outfile, the former was set to comma as its
    default value and the later are the filename of the corresponding annotation file and its name are made by
    joining method name and text file extension (.txt). Users are encouraged to modify these two arguments according
    to their datasets. For each method, all keywords in mandatory settings and optional settings which only can be 
    set within annotation file are elaborated listed as keyword argument (lower case) along with default value. 
    Keywords for optional settings can be set or changed later in the web interface are not listed, if user need to 
    pass them to concerned method, they can be passed as additional keyword arguments (use lower cases). Each method 
    will generate an annotation file in specified work directory if the method call did not fail. The doc string for
    each method only listed information about the positional argument and some keyword arguments, for information
    about the rest arguments, more details can be found on iTOL help page or in annotation template files.
    """

    def __init__(self, treefile, wd='iTOL'):
        """
        Initialize the class, check the treefile and set the work directory.

        :param treefile: str, name of a tree file, in one of the supported formats (Newick, Nexus, PhyloXML or Jplace).
        :param wd: str, path of work directory, without setting, a directory named iTOL in current work directory
        will be created and used.
        """
        
        if not isinstance(treefile, str):
            raise TypeError('Invalid treefile {}, argument treefile should be a string.'.format(treefile))
        
        if not os.path.isfile(treefile):
            raise ValueError('Invalid treefile {} (not a file or does not exist).'.format(treefile))

        tree = os.path.abspath(treefile)
        
        if wd:
            if not isinstance(wd, str):
                raise TypeError('Invalid work directory (wd) {}, argument wd should be a string.')
        else:
            wd = os.path.join(os.getcwd(), 'iTOL')
            
        if not os.path.isdir(wd):
            try:
                os.mkdir(wd)
            except OSError:
                raise ValueError('Invalid work directory (wd) {}, directory cannot be created.'.format(wd))
            
        wd = os.path.abspath(wd)
        
        if wd != os.path.dirname(tree):
            name = os.path.join(wd, 'tree.jplace') if tree.endswith('.jplace') else os.path.join(wd, 'iTOL.tree.txt')
            tree = name if os.path.isfile(name) else shutil.copy(tree, name)
            
        self.wd, self.tree = wd, tree
        self.treeID, self.url = None, None
        
    def color(self, data, separator='comma', outfile='color.txt', **kwargs):
        """
        Handling branch colors and styles, colored ranges and label colors/front style (TREE_COLORS annotation file).

        :param data: list, a nested list consisting of tuples or lists.
        Each inner tuple or list should have at least 3 elements which define the node, type and color in order.
        Possible types are range, clade, branch, and label, an additional element may be optional or required.
        See http://itol.embl.de/help/colors_styles_template.txt for more details.

        Examples:
        Leaf label for node 8015 will be displayed in blue
        data = [(8015, 'label', '#0000ff')]

        Leaf label for node 9606 will be displayed in green, bold and twice the regular font size
        data = [(9606, 'label', '#00ff00', 'bold', '2')]

        Leaf label for node 9031 will be displayed in yellow, bold italic and half the regular font size
        data = [(9031, 'label', '#ffff00', 'bold-italic', 0.5)]

        Internal node with solid branches colored blue and twice the standard width
        data = [('9031|9606', 'clade', '#0000ff', 'normal', 2)]
        
        Internal node with dashed branches colored red and one half the standard width as well as a single internal
        branch colored green, dashed and 5 times the normal width (a list with 2 tuples)
        data = [('601|340', 'clade', '#ff0000', 'dashed', 0.5), ('915|777', 'branch', '#00ff00', 'dashed', 5)]

        Colored range covering all leaves of an internal node, colored and with labels
        data = [('184922|9606', 'range', '#ff0000', 'Eukaryota'),
                ('2190|2287', 'range', '#aaffaa', 'Archaea'),
                ('623|1502', 'range', '#aaaaff', 'Bacteria')]

        """

        _args(locals(), data, separator, outfile, 'TREE_COLORS', self.wd)

    def label(self, data, separator='comma', outfile='label.txt', **kwargs):
        """
        Handling the text assigned to leaf nodes, or changing the internal node names (displayed in mouse-over popups).

        :param data: list, a nested list consisting of tuples or lists.
        Each inner tuple or lists should have 2 elements which define node id and label. Internal tree nodes can be
        specified using IDs directly, or using the 'last common ancestor' method described in iTOL help pages.
        See http://itol.embl.de/help/labels_template.txt for more details.

        Examples:
        Define a name for an internal node
        data = [('9031|9606', 'Metazoa')]

        Change the name (or label) for a leaf node
        data = [(9606, 'Homo sapiens')]
        """

        _args(locals(), data, separator, outfile, 'LABELS', self.wd)

    def popup(self, data, separator='comma', outfile='popup.txt', **kwargs):
        """
        Handling custom text/html which will be displayed in mouse-over popups for nodes/leaves.

        :param data: list, a nested list consisting of tuples or lists.
        Each inner tuple should have 2 elements which define node id and label content. Content can be plain text or any
        valid HTML (including links to external web sites, or IMG tags pointing to external images).
        Internal tree nodes can be specified using IDs directly, or using the 'last common ancestor' method described in
        iTOL help pages.
        See http://itol.embl.de/help/popup_info_template.txt for more details.

        Examples
        Internal node with simple HTML in its popup
        data = [('9031|9606', "This is the popup title,<h1>Some header</h1><p>Information comes here</p>
        <img src='http://website.com/images/image.jpg'/>")]

        Popup for leaf node 9606
        data = [(9606, "Homo sapiens info popup,<h1>Homo sapiens</h1><p style='color:blue'>More info
        at <a target='_blank' href='http://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=9606'> NCBI </a></p>")]
        """

        _args(locals(), data, separator, outfile, 'POPUP_INFO', self.wd)

    def binary(self, data, separator='comma', dataset_label='binary', color='#ff0000', field_shapes=1,
               field_labels='f1', field_colors='#ff0000', outfile='binary.txt', **kwargs):
        """
        Handling binary datasets visualization.

        :param data: list, a nested list consisting of tuples or lists.
        Each inner tuple or list should have at least 2 elements which define node id and one shape or combined shapes.
        If use combined shapes, the delimiter between different shapes should be consisted with the argument separator.
        See http://itol.embl.de/help/dataset_binary_template.txt for more details.
        
        Examples
        Node 9606 will have a filled circle, empty left triangle, nothing in the 3rd column and an empty rectangle
        data = [('9606', '1,0,-1,0')]
        data = [('9606', 1, 0, -1, 0)] have same effect (on if separator was set to comma).

        :param field_shapes: shapes can be set by a single shape value (string or integer) or a combined shape value
        strings separated by the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples:
        field_shapes = 1 or field_shapes = '1'
        field_shapes = '2,4,5,1' or '2\t4\t5\t1' or '2 4 5 1', (for comma, tab, or space)

        :param field_labels: labels can be set by a single shape value string or a combined label strings separated
        by the delimiter which was assigned by argument separator (keep separator consist).
        Examples
        field_labels = 'f1'
        field_labels = 'f2,f4,f5,f1' or 'f2\tf4\tf5\tf1' or 'f2 f4 f5 f1', (for comma, tab, or space)
        
        :param field_colors: colors can be set by a single color value string or a combined color strings separated
        by the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        field_colors = '#ff0000'
        field_colors = '#ff0000,#00ff00,#ffff00' or '#ff0000\t#00ff00\t#ffff00' or '#ff0000 #00ff00 #ffff00'
        """

        _args(locals(), data, separator, outfile, 'DATASET_BINARY', self.wd)

    def sbar(self, data, separator='comma', dataset_label='sbar', color='#ff0000',
             dataset_scale='', legend_title='', legend_shapes='', legend_colors='', legend_labels='',
             outfile='sbar.txt', **kwargs):

        """
        Handling simple bar charts

        :param data: list, a nested list consisting of tuples or lists.
        Each inner tuple or list should have 2 elements which define node id and a single numeric value which is
        displayed as a bar outside the tree.
        Internal tree nodes can be specified using IDs directly, or using the 'last common ancestor' method described in
        iTOL help pages.
        See http://itol.embl.de/help/dataset_simplebar_template.txt for more details.

        Examples
        data = [(9606,10000)]
        data = [('LEAF1|LEAF2', 11000)]
        data = [('ID1', 200), ('ID2', 250)]

        :param dataset_scale: scale can only be set by combined strings (format: VALUE or VALUE-LABEL-COLOR)
        separated by the delimiter which was assigned by argument separator (keep separator consist).
        
        See http://itol.embl.de/help.cgi#dsScale for more details.
        Examples
        dataset_scale = '100,200,300,400,500' or '100 200 300 400 500' or '100\t200\t300\t400\t500'
        dataset_scale = '2000-2k-#0000ff,10000-10k-#ff0000' or '2000-2k-#0000ff\t10000-10k-#ff0000'
        or '2000-2k-#0000ff 10000-10k-#ff0000'

        :param legend_shapes: shapes can be set by a single shape value (string or integer) or a combined shape value
        strings separated by the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_shapes = 1 or legend_shapes = '1'
        legend_shapes = '2,4,5,1' or '2\t4\t5\t1' or '2 4 5 1'

        :param legend_labels: labels can be set by a single shape value string or a combined label strings separated by
        the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_labels = 'b1'
        legend_labels = 'b2,b4,b5,b1' or 'b2\tb4\tb5\tb1' or 'b2 b4 b5 b1'

        :param legend_colors: colors can be set by a single color value string or a combined color strings separated by
        the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_colors = '#ff0000'
        legend_colors = '#ff0000,#00ff00,#ffff00,#0000ff' or '#ff0000\t#00ff00\t#ffff00\t#0000ff'
        or '#ff0000 #00ff00 #ffff00 #0000ff'
        """

        _args(locals(), data, separator, outfile, 'DATASET_SIMPLEBAR', self.wd)

    def mbar(self, data, separator='comma', dataset_label='mbar', color='#ff0000',
             field_colors='#ff0000,#00ff00,#0000ff', field_labels='f1,f2,f3',
             dataset_scale='', legend_title='', legend_shapes='', legend_colors='', legend_labels='',
             outfile='mbar.txt'):

        """
        Handling multi-value bar charts

        :param data: list, a nested list consisting of tuples or lists.
        Each inner tuple or list should have at least 3 elements which define node id and multiple numeric value which
        are displayed as stocked or aligned bar chart.
        See http://itol.embl.de/help/dataset_multibar_template.txt for more details.
        
        Examples
        data = [(9606,10000,800)]
        data = [('LEAF1|LEAF2', 11000, 6000)]
        data = [('ID1', value1, value2), ('ID2', value3, value4)]

        dataset_scale = '100,200,300,400,500' or '100 200 300 400 500' or '100\t200\t300\t400\t500'
        dataset_scale = '2000-2k-#0000ff,10000-10k-#ff0000' or '2000-2k-#0000ff\t10000-10k-#ff0000'
        or '2000-2k-#0000ff 10000-10k-#ff0000'

        :param legend_shapes: shapes can be set by a single shape value (string or integer) or a combined shape value
        strings separated by the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_shapes = 1 or legend_shapes = '1'
        legend_shapes = '2,4,5,1' or '2\t4\t5\t1' or '2 4 5 1'

        :param legend_labels: labels can be set by a single shape value string or a combined label strings separated by
        the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_labels = 'b1'
        legend_labels = 'b2,b4,b5,b1' or 'b2\tb4\tb5\tb1' or 'b2 b4 b5 b1'

        :param legend_colors: colors can be set by a single color value string or a combined color strings separated by
        the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_colors = '#ff0000'
        legend_colors = '#ff0000,#00ff00,#ffff00,#0000ff' or '#ff0000\t#00ff00\t#ffff00\t#0000ff'
        or '#ff0000 #00ff00 #ffff00 #0000ff'
        """

        _args(locals(), data, separator, outfile, 'DATASET_MULTIBAR', self.wd)

    def pie(self, data, separator='comma', dataset_label='pie', color='#ff0000',
            field_colors='#ff0000,#00ff00,#0000ff', field_labels='f1,f2,f3',
            legend_title='', legend_shapes='', legend_colors='', legend_labels='',
            outfile='pie.txt', **kwargs):

        """
        Handling pie charts

        :param data: list, a nested list consisting of tuples or lists.
        Each tuples or list should have at least 5 elements which define node id, position, radius, and multiple numeric
        value (at least 2 values) which are displayed as a pie chart directly on the branch, or outside the tree.
        See http://itol.embl.de/help/dataset_piechart_template.txt for more details.
        
        Examples:
        data = [(9606, 0, 10, 4, 2, 4)]
        data = [('LEAF1|LEAF2', 1, 5, 0.1, 0.3, 0.6)]
        data = [('ID1', 0, 20, 0.02, 0.18, 0.8), ('ID2', 1, 3, 0.11, 0.41, 0.48)]

        :param legend_shapes: shapes can be set by a single shape value (string or integer) or a combined shape value
        strings separated by the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_shapes = 1 or legend_shapes = '1'
        legend_shapes = '2,4,5,1' or '2\t4\t5\t1' or '2 4 5 1'

        :param legend_labels: labels can be set by a single shape value string or a combined label strings separated by
        the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_labels = 'b1'
        legend_labels = 'b2,b4,b5,b1' or 'b2\tb4\tb5\tb1' or 'b2 b4 b5 b1'

        :param legend_colors: colors can be set by a single color value string or a combined color strings separated by
        the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_colors = '#ff0000'
        legend_colors = '#ff0000,#00ff00,#ffff00,#0000ff' or '#ff0000\t#00ff00\t#ffff00\t#0000ff'
        or '#ff0000 #00ff00 #ffff00 #0000ff'
        """

        _args(locals(), data, separator, outfile, 'DATASET_PIECHART', self.wd)

    def text(self, data, separator='comma', dataset_label='text', color='#ff0000', outfile='text.txt', **kwargs):

        """
        Handling text labels.

        :param data: list, a nested list consisting of tuples or lists.
        Each inner tuple or list should have at least 2 elements which define node id and a label, possible additional
        elements can be tailed in the order of position, color, style, size factor, and rotation.
        See http://itol.embl.de/help/dataset_text_template.txt for more details.
        
        Examples:
        node 9606 will have an external label 'Homo sapiens' in bold red and twice the size of standard labels
        data = [(9606, 'Homo sapiens', '-1', '#ff0000', 'bold', 2, 0)]
        
        node 4530 will have an internal label 'Oryza sativa' in bold italic blue, starting directly over the node
        data = [(4530, 'Oryza sativa', 0, '#0000ff', 'bold-italic', 1)]
        """

        _args(locals(), data, separator, outfile, 'DATASET_TEXT', self.wd)

    def strip(self, data, separator='comma', dataset_label='strip', color='#ff0000',
            color_branch=0, legend_title='', legend_shapes=0, legend_colors=0, legend_labels=0,
            outfile='strip.txt', **kwargs):

        """
        Handling colored strips.

        :param data: list, a nested list consisting of tuples or lists.
        Each inner tuple or list should have at least 2 elements which define node id(s) and color, possible third
        element should be a string (string is displayed in the mouse-over popups).
        Internal tree nodes can be specified using IDs directly, or using the 'last common ancestor' method described in
        iTOL help pages.
        See http://itol.embl.de/help/dataset_color_strip_template.txt for more details.

        Examples:
        data = [(9606, '#ff0000')]
        data = [(9606, '#ff0000', 'Human')]
        data = [('LEAF1|LEAF2', '#ffff00')]

        :param legend_shapes: shapes can be set by a single shape value (string or integer) or a combined shape value
        strings separated by the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_shapes = 1 or legend_shapes = '1'
        legend_shapes = '2,4,5,1' or '2\t4\t5\t1' or '2 4 5 1'

        :param legend_labels: labels can be set by a single shape value string or a combined label strings separated by
        the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_labels = 'b1'
        legend_labels = 'b2,b4,b5,b1' or 'b2\tb4\tb5\tb1' or 'b2 b4 b5 b1'

        :param legend_colors: colors can be set by a single color value string or a combined color strings separated by
        the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_colors = '#ff0000'
        legend_colors = '#ff0000,#00ff00,#ffff00,#0000ff' or '#ff0000\t#00ff00\t#ffff00\t#0000ff'
        or '#ff0000 #00ff00 #ffff00 #0000ff'
        """

        _args(locals(), data, separator, outfile, 'DATASET_COLORSTRIP', self.wd)

    def gradient(self, data, separator='comma', dataset_label='gradient', color='#ff0000',
            legend_title='', legend_shapes='', legend_colors='', legend_labels='',
            outfile='gradient.txt', **kwargs):

        """
        Handling colored gradients

        :param data: list, a nested list consisting of tuples or list.
        Each inner tuple or list should have 2 elements which define node id(s) and a value. Internal tree nodes can be
        specified using IDs, or using the 'last common ancestor' method described in iTOL help pages.
        See http://itol.embl.de/help/dataset_gradient_template.txt for more details.

        Example:
            data = [(9606, 100)]
            data = [('LEAF1|LEAF2', 2000)]

        :param legend_shapes: shapes can be set by a single shape value (string or integer) or a combined shape value
        strings separated by the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_shapes = 1 or legend_shapes = '1'
        legend_shapes = '2,4,5,1' or '2\t4\t5\t1' or '2 4 5 1'

        :param legend_labels: labels can be set by a single shape value string or a combined label strings separated by
        the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_labels = 'b1'
        legend_labels = 'b2,b4,b5,b1' or 'b2\tb4\tb5\tb1' or 'b2 b4 b5 b1'

        :param legend_colors: colors can be set by a single color value string or a combined color strings separated by
        the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_colors = '#ff0000'
        legend_colors = '#ff0000,#00ff00,#ffff00,#0000ff' or '#ff0000\t#00ff00\t#ffff00\t#0000ff'
        or '#ff0000 #00ff00 #ffff00 #0000ff'
        """

        _args(locals(), data, separator, outfile, 'DATASET_GRADIENT', self.wd)

    def connection(self, data, separator='comma', dataset_label='connection', color='#ff0000',
            legend_title='', legend_shapes=0, legend_colors=0, legend_labels=0,
            outfile='connection.txt', **kwargs):

        """
        Handling connections visualization.

        :param data: list, a nested list consisting of tuples or lists.
        Each inner tuple or list should have 5 elements which define a single connection between 2 nodes and consists
        of the following format: NODE1, NODE2, WIDTH, COLOR, LABEL. Color can be specified in hexadecimal string.
        See http://itol.embl.de/help/dataset_connections_template.txt for more details.

        Example:
            data = [('LEAF1', 'LEAF2', 10, '#ff0000', 'label')]

        :param legend_shapes: shapes can be set by a single shape value (string or integer) or a combined shape value
        strings separated by the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_shapes = 1 or legend_shapes = '1'
        legend_shapes = '2,4,5,1' or '2\t4\t5\t1' or '2 4 5 1'

        :param legend_labels: labels can be set by a single shape value string or a combined label strings separated by
        the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_labels = 'b1'
        legend_labels = 'b2,b4,b5,b1' or 'b2\tb4\tb5\tb1' or 'b2 b4 b5 b1'

        :param legend_colors: colors can be set by a single color value string or a combined color strings separated by
        the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_colors = '#ff0000'
        legend_colors = '#ff0000,#00ff00,#ffff00,#0000ff' or '#ff0000\t#00ff00\t#ffff00\t#0000ff'
        or '#ff0000 #00ff00 #ffff00 #0000ff'
        """

        _args(locals(), data, separator, outfile, 'DATASET_CONNECTION', self.wd)

    def heatmap(self, data, separator='space', dataset_label='heatmap', color='#ff0000',
            field_labels='f1 f2 f3 f4 f5 f6', field_tree='',
            legend_title='', legend_shapes='', legend_colors='', legend_labels='', outfile='heatmap.txt', **kwargs):

        """
        Handling heatmap visualization.

        :param data: list, a nested list consisting of tuples or lists.
        Each inner tuple or list should have at least 2 elements which define node id(s) and multiple values.
        See http://itol.embl.de/help/dataset_heatmap_template.txt for more details.

        Example:
            data = [(9606, 10, 15, 20, 25, 30)]

        :param legend_shapes: shapes can be set by a single shape value (string or integer) or a combined shape value
        strings separated by the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_shapes = 1 or legend_shapes = '1'
        legend_shapes = '2,4,5,1' or '2\t4\t5\t1' or '2 4 5 1'

        :param legend_labels: labels can be set by a single shape value string or a combined label strings separated by
        the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_labels = 'b1'
        legend_labels = 'b2,b4,b5,b1' or 'b2\tb4\tb5\tb1' or 'b2 b4 b5 b1'

        :param legend_colors: colors can be set by a single color value string or a combined color strings separated by
        the delimiter which was assigned by argument separator (keep separator consist).
        
        Examples
        legend_colors = '#ff0000'
        legend_colors = '#ff0000,#00ff00,#ffff00,#0000ff' or '#ff0000\t#00ff00\t#ffff00\t#0000ff'
        or '#ff0000 #00ff00 #ffff00 #0000ff'
        """

        _args(locals(), data, separator, outfile, 'DATASET_HEATMAP', self.wd)

    def boxplot(self, data, separator='comma', dataset_label='boxplot', color='#ff0000',dataset_scale='',
            outfile='boxplot.txt', **kwargs):

        """
        Handling boxplot visualization.

        :param data: list, a nested list consisting of tuples or lists.
        Each inner tuple or list should have at least 2 elements which define node id(s) and multiple values.
        See http://itol.embl.de/help/dataset_boxplot_template.txt for more details.

        Examples:
            data = [(9606, 10000, 12000, 13000, 10000)]
            data = [('ID1', 200, 300, 400, 500), ('ID2', 250, 200, 150, 200, 300)]

        :param dataset_scale: scale can only be set by combined strings (format: VALUE or VALUE-LABEL-COLOR) separated
        by the delimiter which was assigned by argument separator.
        See http://itol.embl.de/help.cgi#dsScale for more details.

        Examples
            dataset_scale = '100,200,300,400,500' (only works when separator is comma)
            dataset_scale = '100 200 300 400 500' (only works when separator is space)
            dataset_scale = '100\t200\t300\t400\t500' (only works when separator is tab)
            dataset_scale = '2000-2k-#0000ff,10000-10k-#ff0000' (only works when separator is comma)
            dataset_scale = '2000-2k-#0000ff\t10000-10k-#ff0000' (only works when separator is tab)
            dataset_scale = '2000-2k-#0000ff 10000-10k-#ff0000' (only works when separator is space)
        """

        _args(locals(), data, separator, outfile, 'DATASET_BOXPLOT', self.wd)

    def domain(self, data, separator='comma', dataset_label='domain', color='#ff0000', width=1000,
            dataset_scale=0, legend_title='', legend_shapes='', legend_colors='', legend_labels='',
            outfile='domain.txt', **kwargs):

        """
        Handling protein domains visualization.

        :param data: list, a nested list consisting of tuples or lists.
        Each inner tuple or list should have at least 3 elements which define node id(s), total protein length (an
        integer) and unlimited number of domain definition strings.
        Each domain definition string consists of 5 parts, separated with vertical lines: shape|start|end|color|label
        See http://itol.embl.de/help/dataset_boxplot_template.txt for more details.

        Example:
            data = [(9606, 1200, 'RE|100|150|#ff0000|SH2', 'EL|400|500|#0000ff|SH3', 'OC|700|900|#00ff00|PH')]

        :param dataset_scale: scale can only be set by combined strings (format: VALUE or VALUE-LABEL-COLOR) separated
        by the delimiter which was assigned by argument separator.
        See http://itol.embl.de/help.cgi#dsScale for more details.

        Examples:
            dataset_scale = '100,200,300,400,500' (only works when separator is comma)
            dataset_scale = '100 200 300 400 500' (only works when separator is space)
            dataset_scale = '100\t200\t300\t400\t500' (only works when separator is tab)
            dataset_scale = '2000-2k-#0000ff,10000-10k-#ff0000' (only works when separator is comma)
            dataset_scale = '2000-2k-#0000ff\t10000-10k-#ff0000' (only works when separator is tab)
            dataset_scale = '2000-2k-#0000ff 10000-10k-#ff0000' (only works when separator is space)

        :param legend_shapes: shapes can be set by a single shape string or a combined shape strings separated by the
        delimiter which was assigned by argument separator.

        Examples:
            legend_shapes = 1
            legend_shapes = '1'
            legend_shapes = '2,4,5,1' (only works when separator is comma)
            legend_shapes = '2\t4\t5\t1' (only works when separator is tab)
            legend_shapes = '2 4 5 1' (only works when separator is space)

        :param legend_labels: labels can be set by a single shape value string or a combined label strings separated by
        the delimiter which was assigned by argument separator.

        Examples:
            legend_labels = 'b1'
            legend_labels = 'b2,b4,b5,b1' (only works when separator is comma)
            legend_labels = 'b2\tb4\tb5\tb1' (only works when separator is tab)
            legend_labels = 'b2 b4 b5 b1' (only works when separator is space)

        :param legend_colors: colors can be set by a single color value string or a combined color strings separated by
        the delimiter which was assigned by argument separator.

        Examples:
            legend_colors = '#ff0000'
            legend_colors = '#ff0000,#00ff00,#ffff00,#0000ff' (only works when separator is comma)
            legend_colors = '#ff0000\t#00ff00\t#ffff00\t#0000ff' (only works when separator is tab)
            legend_colors = '#ff0000 #00ff00 #ffff00 #0000ff' (only works when separator is space)
        """

        _args(locals(), data, separator, outfile, 'DATASET_DOMAINS', self.wd)

    def shape(self, data, separator='comma', dataset_label='shape', color='#ff0000',
            field_colors='#ff0000,#00ff00,#0000ff', field_labels='f1,f2,f3', outfile='shape.txt', **kwargs):

        """
        Handling external shapes visualization.

        :param data: list, a nested list consisting of tuples or lists.
        Each inner tuple or list should have at least 2 elements which define node id and multiple values.
        See http://itol.embl.de/help/dataset_external_shapes_template.txt for more details.

        Examples:
            data = [(9606, 10, 10, 20, 40)]
            data = [('LEAF1|LEAF2', 50, 60, 80, 90)]

        :param field_labels: labels can be set by a single shape value string or a combined label strings separated by
        the delimiter which was assigned by argument separator.

        Examples:
            field_labels = 'f1'
            field_labels = 'f2,f4,f5,f1' (only works when separator is comma)
            field_labels = 'f2\tf4\tf5\tf1' (only works when separator is tab)
            field_labels = 'f2 f4 f5 f1' (only works when separator is space)

        :param field_colors: colors can be set by a single color value string or a combined color strings separated by
        the delimiter which was assigned by argument separator.

        Examples:
            field_colors = '#ff0000'
            field_colors = '#ff0000,#00ff00,#ffff00,#0000ff' (only works when separator is comma)
            field_colors = '#ff0000\t#00ff00\t#ffff00\t#0000ff' (only works when separator is tab)
            field_colors = '#ff0000 #00ff00 #ffff00 #0000ff' (only works when separator is space)

        :param legend_shapes: shapes can be set by a single shape value (string or integer) or a combined shape value
        strings separated by the delimiter which was assigned by argument separator.

        Examples:
            legend_shapes = 1
            legend_shapes = '1'
            legend_shapes = '2,4,5,1' (only works when separator is comma)
            legend_shapes = '2\t4\t5\t1' (only works when separator is tab)
            legend_shapes = '2 4 5 1' (only works when separator is space)

        :param legend_labels: labels can be set by a single shape value string or a combined label strings separated by
        the delimiter which was assigned by argument separator.

        Example:
            legend_labels = 'b1'
            legend_labels = 'b2,b4,b5,b1' (only works when separator is comma)
            legend_labels = 'b2\tb4\tb5\tb1' (only works when separator is tab)
            legend_labels = 'b2 b4 b5 b1' (only works when separator is space)

        :param legend_colors: colors can be set by a single color value string or a combined color strings separated by
        the delimiter which was assigned by argument separator.

        Example:
            legend_colors = '#ff0000'
            legend_colors = '#ff0000,#00ff00,#ffff00,#0000ff' (only works when separator is comma)
            legend_colors = '#ff0000\t#00ff00\t#ffff00\t#0000ff' (only works when separator is tab)
            legend_colors = '#ff0000 #00ff00 #ffff00 #0000ff' (only works when separator is space)
        """

        _args(locals(), data, separator, outfile, 'DATASET_EXTERNALSHAPE', self.wd)

    def symbol(self, data, separator='comma', dataset_label='symbol', color='#ff0000',
               legend_title='', legend_shapes=0, legend_colors=0, legend_labels=0, outfile='symbol.txt', **kwargs):

        """
        Handling external shapes.

        :param data: list, a nested list consisting of tuples.
        Each inner tuple or list should have at least 6 elements which define node id, symbol, size, color, fill,
        position, may or may not followed by an additional element label.
        See http://itol.embl.de/help/dataset_external_shapes_template.txt for more details.
        
        Examples:
            data = [(9606, 2, 10, '#ff0000', 1, 0.5)]
            data = [('LEAF1|LEAF2', 2, 10, '#ff0000', 1, 0.5)]

        :param legend_shapes: shapes can be set by a single shape value (string or integer) or a combined shape value
        strings separated by the delimiter which was assigned by argument separator.
        
        Examples:
            legend_shapes = 1
            legend_shapes = '1'
            legend_shapes = '2,4,5,1' (only works when separator is comma)
            legend_shapes = '2\t4\t5\t1' (only works when separator is tab)
            legend_shapes = '2 4 5 1' (only works when separator is space)

        :param legend_labels: labels can be set by a single shape value string or a combined label strings separated by
        the delimiter which was assigned by argument separator.
        
        Examples:
            legend_labels = 'b1'
            legend_labels = 'b2,b4,b5,b1' (only works when separator is comma)
            legend_labels = 'b2\tb4\tb5\tb1' (only works when separator is tab)
            legend_labels = 'b2 b4 b5 b1' (only works when separator is space)

        :param legend_colors: colors can be set by a single color value string or a combined color strings separated by
        the delimiter which was assigned by argument separator.

        Examples:
            legend_colors = '#ff0000'
            legend_colors = '#ff0000,#00ff00,#ffff00,#0000ff' (only works when separator is comma)
            legend_colors = '#ff0000\t#00ff00\t#ffff00\t#0000ff' (only works when separator is tab)
            legend_colors = '#ff0000 #00ff00 #ffff00 #0000ff' (only works when separator is space)
        """
        _args(locals(), data, separator, outfile, 'DATASET_SYMBOL', self.wd)

    def placement(self, jplace):
        """
        Handling phylogenetic placements

        :param jplace: string, file name of .jplace files created by pplacer and RAxML
        """
        if isinstance(jplace, str):
            if os.path.isfile(jplace):
                if jplace.endswith('.jplace'):
                    name = os.path.abspath(jplace)
                else:
                    name = os.path.abspath(''.join([jplace, '.jplace']))
                directory = os.path.dirname(name)
                if directory != self.wd:
                    shutil.copy(name, os.path.join(self.wd, os.path.basename(name)))
                    name = os.path.join(self.wd, os.path.basename(name))
            else:
                raise ValueError('jplace file {} does not exist!'.format(jplace))
        else:
            raise ValueError('Argument jplace should be a string representing a jplace file name!')
        return name
    
    def msa(self, data, separator='comma', dataset_label='msa', color='#ff0000', custom_color_scheme='',
            outfile='msa.txt', **kwargs):
        """
        Handling multiple sequence alignments visualization.
        
        :param data: str, alignment in FASTA format.
        See http://itol.embl.de/help/dataset_alignment_template.txt for more details.
        """
        pass

    def line(self, data, separator='comma', dataset_label='line', color='#ff0000', line_colors='', axis_x='', axis_y='',
            outfile='line.txt', **kwargs):
        """
        Handling line chart visualization.

        :param data: list, a nested list consisting of tuples.
        Each inner tuple or list should have at least 3 elements which define node id and 2 or more points associated.
        For each individual point, a string consisting of X and Y values separated by a vertical line.
        See http://itol.embl.de/help/dataset_linechart_template.txt for more details.
        
        Examples:
        data = [('A', 'X1|Y1', 'X2|Y2', 'X3|Y3'), ('9606', '2|6', '0|0', '5|3'), ('B|C', '0|0', '10|5', '2|1', '13|15')]
        """
        
        pass

    def image(self, data, separator='comma', dataset_label='image', color='#ff0000', outfile='image.txt', **kwargs):
        """
        Handling image dataset visualization.

        :param data: list, a nested list consisting of tuples or lists.
        Each inner tuple or list should have 7 elements which define node id, position, size_factor, rotation,
        horizontal_shift, vertical_shift, and image_url.
        See http://itol.embl.de/help/dataset_linechart_template.txt for more details.

        Examples:
        data = [('9606', -1, 1, 0, 0, 0, 'http://itol.embl.de/img/species/9606.jpg'),
                ('4530', 1, 1, 0, 0, 0, 'http://itol.embl.de/img/species/4530.jpg'),
                ('6239|6239', 0, 1, 90, 0, 0, 'http://itol.embl.de/img/species/6239.jpg')]
        """
    
        pass

    def upload(self, treename='', uploadID='', projectname='', treedescription=''):

        """
        Pack tree file and all notation files (text files ending in .txt) inside work directory into a zip file
        and upload the zip file to ITOL server (batch upload).

        :param treename: str, if not provided, the tree file name (basename without extension) will be used instead.
        :param uploadID: str, your upload ID, which is generated when you enable batch uploading in your account. If an
        uploadID is not provided, the tree will not be associated with any account, and will be deleted after 30 days.
        :param projectname: str, required if ID is specified, case sensitive, and should be unique in your account.
        :param treedescription: str, description of your treee, ignored if ID is not specified.

        Note: A new ZIP archive (named iTOL.tree.zip) will be automatically generated in work directory every time you
        call this method.
        """

        args = {}
        zfile = os.path.join(self.wd, 'iTOL.tree.zip')
        with ZipFile(zfile, 'w') as zf:
            for f in os.listdir(self.wd):
                if f.endswith('.txt') or f.endswith('.tree') or f.endswith('.jplace'):
                    zf.write(os.path.join(self.wd, f), arcname=f)

        args['treeName'] = treename if treename else os.path.basename(self.tree)
        if uploadID:
            args['uploadID'] = uploadID
        if projectname:
            args['projectName'] = projectname
        if treedescription:
            args['treeDescription'] = treedescription

        if not args['uploadID']:
            print('Warning!!! No ID was provided!')
            print('The tree will not be associated with any account and will be deleted after 30 days!')
        
        respond = requests.post(UPLOAD_URL, data=args, files={'zipFile': open(zfile, 'rb')})
        info = respond.text
        print(info)
        
        if info.startswith('SUCCESS'):
            code, treeID = info.split(': ')
            self.treeID = treeID
            print('Tree upload successfully and you can access your tree using the following iTOL tree ID:')
            print('\t{}'.format(treeID))
            
            url = 'https://itol.embl.de/tree/{}'.format(treeID)
            self.url = url
            print('You can also view your tree in browser using the following URL: \n\t{}'.format(url))
        else:
            print('Tree upload failed due to the following reason:\n\t{}'.format(info))
            sys.exit(1)
            
        return treeID, url
    
    def download(self, treeID='', outfile='', format='pdf', **kwargs):
        """
        Download (or export) a tree from ITOL server (batch download).
        
        :param treeID: str, ITOL tree ID which will be exported.
        :param format: str, output file format, supported values are: svg, eps, pdf and png for graphical formats and
        newick, nexus and phyloxml for text formats.
        :param outfile: str, path of the output file.
        :param kwargs: optional parameters.
        :return:
        """
        if treeID:
            if isinstance(treeID, str):
                treeID = str(treeID)
            else:
                raise TypeError('Invalid treeID, argument treeID accepts a string pointing to a iTOL tree ID.')
        elif self.treeID:
            treeID = self.treeID
        else:
            raise ValueError('No treeID provided, please upload a tree first or proved a treeID.')
        
        if isinstance(format, str):
            format = format.lower()
            formats = ['svg', 'eps', 'pdf', 'png', 'newick', 'nexus', 'phyloxml']
            if format not in formats:
                raise ValueError("Invalid format. Supported formats: \n\t{}.".format(', '.join(formats)))
        else:
            raise TypeError('Invalid output format, argument format accepts a string representing output format.')

        args = kwargs
        args['tree'] = treeID
        args['format'] = format
        
        respond = requests.get(DOWNLOAD_URL, params=args)
        info = respond.text
        code = info.split(':')[0]
        if code == 'ERROR':
            print('Tree download failed due to the following reason:\n\t{}'.format(info))
            sys.exit(1)
        else:
            outfile = outfile if outfile else os.path.join(self.wd, 'iTOL.download.{}'.format(format))
            with open(outfile, 'wb') as out:
                out.write(respond.content)
            print('Tree download successfully and data has been saved to:\n\t{}'.format(outfile))
        return outfile
    
        
if __name__ == '__main__':
    pass
