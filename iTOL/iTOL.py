#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Python API for phylogenetic tree visualization in Interactive Tree of Life (`ITOL <http://iTOL.embl.de>`_).

TODO: add method handles data ``get()`` and ``post()`` methods using built-in ``urllib`` instead of ``requests``.
TODO: add support for Python 2. Current codes have only been tested under Python 3.6 (August 17, 2018)
"""

import os
import sys
import shutil
import argparse
import requests
import logging
from zipfile import ZipFile, is_zipfile

LEVEL = logging.INFO
LOGFILE, LOGFILEMODE = '', 'w'

HANDLERS = [logging.StreamHandler(sys.stdout)]
if LOGFILE:
    HANDLERS.append(logging.FileHandler(filename=LOGFILE, mode=LOGFILEMODE))

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(name)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', handlers=HANDLERS, level=LEVEL)

logger = logging.getLogger('[iTOL]')
warn, info, error = logger.warning, logger.info, logger.error


DELIMITER = {'TAB': '\t', 'SPACE': ' ', 'COMMA': ','}
UPLOAD_URL = "https://itol.embl.de/batch_uploader.cgi"
DOWNLOAD_URL = "http://itol.embl.de/batch_downloader.cgi"
s1 = 'A=#d2d0c9,M=#d2d0c9,I=#d2d0c9,L=#d2d0c9,V=#d2d0c9,P=#746f69,G=#746f69,C=#746f69,F=#d0ad16,Y=#d0ad16'
s2 = 'W=#d0ad16,S=#34acfb,T=#34acfb,N=#34acfb,Q=#34acfb,R=#34fb54,K=#34fb54,H=#34fb54,D=#fb4034,E=#fb4034'
COLOR_SCHEME = 'CUSTOM_COLOR_SCHEME,COLOR_SCHEME,{},{}'.format(s1, s2)


def _sd(data, separator):
    """
    Private function for handles separator and data block (user should not use this functionary directly).
    
    :param data: nested tuple or list. Each inner element should have at least 3 elements which define the node,
                 type and color.
    :param separator: the separator which is used to delimit the setting text (tab, space or comma), default: comma.
    
    .. note::
    
        Unlike writing iTOL setting file manually, the name of the separator here is case insensitive. However, you
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
    Private function handles arguments parse and writing config file (user should not use this functionary directly).
    
    :param args: dict, all local keyword arguments.
    :param data: nested tuple or a list. Each inner element should have at least 3 elements which define the node,
                 type and color.
    :param separator: the separator which is used to delimit the setting text (tab, space or comma), default: comma.
    
        .. note::
            Not like writing iTOL setting file, the name of separator here is case insensitive. You should always keep
            in mind that depend on your data, separator does matter.
        
    :param outfile: str, path of the output file.
    :param tag: string, name tag of the config file.
    :param wd: str, path of the work directory.
    :return: str, formatted text.
    """

    for arg in ('self', 'data', 'separator', 'outfile'):
        args.pop(arg)

    data_block, sep, delimiter = _sd(data, separator)
    setting_block = '\n'.join([DELIMITER[delimiter].join([k.upper(), str(v)]) for k, v in args.items() if v and k!='kwargs'])
    if 'kwargs' in args:
    	setting_block2 = '\n'.join([DELIMITER[delimiter].join([k.upper(), str(v)]) for k, v in args['kwargs'].items() if v])
    	setting_block = setting_block + '\n' + setting_block2

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
    Base class Handles tree visualization in Interactive Tree of Life (`ITOL <http://iTOL.embl.de>`_).
    
    Method upload handles upload tree to iTOL and download handles image download (or export). All other methods are
    designed to generate annotation files.
    
    Except upload and download methods, all methods have a positional argument ``data`` which is a nested list
    consisting of tuples or lists. Elements in each inner tuple or list are described within each method. All these
    methods also have two common optional arguments: ``separator`` and ``outfile``. The former was set to comma as its
    default value and the later joins method name and text file extension (.txt) as the default name of the notation
    file. Users are strongly encouraged to modify these two arguments according to their datasets. For each method,
    all keywords in mandatory and optional settings that only can be set within annotation file are elaborated
    listed as keyword argument (lower case) along with their default values. Keywords for optional settings can be
    set or changed later in the web interface are not listed, if user need to pass them to concerned method,
    they can be passed as additional keyword arguments (use lower cases argument name). Each method will generate an
    annotation file in specified work directory if the method call did not fail. The doc string for each method only
    listed information about the positional argument and some keyword arguments, for information about the rest of
    arguments and details can be found in `ITOL help page <http://itol.embl.de/help.cgi>`_ or annotation template files.
    """

    def __init__(self, tfile='', zfile='', wd='iTOL', leave=True):
        """
        Initialize the class, check the treefile and set the work directory.

        :param tfile: str, path of a tree file, in one of the supported formats (Newick, Nexus, PhyloXML or Jplace).
        :param zfile: str, path of a ZIP file contains a tree file and other datasets or notation files.
        :param wd: str, path of the work directory, without setting, a directory named iTOL in current work directory
                   will be created and used.
        """
        
        if tfile:
            if not isinstance(tfile, str):
                raise TypeError('Invalid tfile {}, argument tfile should be a string.'.format(tfile))
            
            if not os.path.isfile(tfile):
                raise ValueError('Invalid tfile {} (not a file or does not exist).'.format(tfile))

            tree = os.path.abspath(tfile)
        elif zfile:
            if not isinstance(zfile, str):
                raise TypeError('Invalid zfile {}, argument zfile should be a string.'.format(zfile))
    
            if not os.path.isfile(zfile):
                raise ValueError('Invalid zfile {} (not a file or does not exist).'.format(zfile))
            
            if not is_zipfile(zfile):
                raise ValueError('Invalid zfile {} (not a ZIP file).'.format(zfile))
            tree = os.path.abspath(zfile)
        else:
            tree = None
            if leave:
                error('ValueError: Neither tree file nor ZIP file was provided.')
                sys.exit(1)
        
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
        
        if tree:
            if wd != os.path.dirname(tree):
                if is_zipfile(tree):
                    tree = shutil.copy(tree, os.path.join(wd, os.path.basename(tree)))
                else:
                    name = os.path.join(wd, 'iTOL.tree.txt')
                    tree = name if os.path.isfile(name) else shutil.copy(tree, name)
            
        self.wd, self.tree = wd, tree
        self.treeID, self.url = None, None
        
    def color(self, data, separator='comma', outfile='color.txt', **kwargs):
        """
        Handles branch colors, styles, colored ranges and label colors/front style (TREE_COLORS annotation file).
        
        :param data: list, a nested list consisting of tuples or lists.
        
        Each inner tuple or list should have at least 3 elements which define the node, type and color in order.
        Possible types are range, clade, branch, and label, an additional element may be optional or required.
        See `colors_styles_template.txt <http://itol.embl.de/help/colors_styles_template.txt>`_ for more details.
        
        The nested list ``colors`` shows a general data structure and these data will set:
            * Leaf label for node 8518 will be displayed in purple
            * Leaf label for node 6529 will be displayed in green, bold and twice the regular font size
            * Leaf label for node 6321 will be displayed in orange, bold italic and half the regular font size
            * Internal clade with solid branches and colored in purple
            * Internal clade with dashed branches and colored in yellow
            * Internal branch with dashed branches and colored in green
            * Colored range in red
            * Colored range in green
            * Colored range in purple
            
        Example::
        
            colors = [(8518, 'label', '#0000ff'),
                      ('6529', 'label', '#00ff00', 'bold', '2'),
                      (6321, 'label', '#ff8000', 'bold-italic', 0.5),
                      ('6529|8463', 'clade', '#0000ff', 'normal', 3),
                      ('8090|8033', 'clade', '#ff0000', 'dashed', 0.5),
                      ('7539|1744', 'branch', '#00ff00', 'dashed', 5),
                      ('5784|7550', 'range', '#ff0000', 'Group A'),
                      ('7396|2154', 'range', '#aaffaa', 'Group B'),
                      ('2055|539', 'range', '#aaaaff', 'Group C')]
        """

        _args(locals(), data, separator, outfile, 'TREE_COLORS', self.wd)

    def label(self, data, separator='comma', outfile='label.txt', **kwargs):
        """
        Handling the text assigned to leaf nodes, or changing the internal node names (displayed in mouse-over popups).

        :param data: list, a nested list consisting of tuples or lists.
        
        Each inner tuple or lists should have 2 elements which define node id and label. Internal tree nodes can be
        specified using IDs directly, or using the 'last common ancestor' method described in iTOL help pages.
        See `labels_template.txt <http://itol.embl.de/help/labels_template.txt>`_ for more details.

        The nested list ``colors`` shows a general data structure and these data will set:
            * Leaf label for node 8518 will be renamed to Baq hxzgs
            * Leaf label for node 6529 will be renamed to Wjk nduvpbl
            * Leaf label for node 6321 will be renamed to Zbumxj osiapem
            * A internal branch will be renamed to Clade A (clade name displayed in mouseover popups)
            * A internal branch will be renamed to Clade B (clade name displayed in mouseover popups)
            * A internal branch will be renamed to Clade C (clade name displayed in mouseover popups)

        Example::
            
            labels = [(8518, 'Baq hxzgs'),
                      ('6529', 'Wjk nduvpbl'),
                      (6321, 'Zbumxj osiapem'),
                      ('5784|7550', 'Clade A'),
                      ('7396|2154', 'Clade B'),
                      ('2055|539', 'Clade C')]
        """

        _args(locals(), data, separator, outfile, 'LABELS', self.wd)

    def popup(self, data, separator='comma', outfile='popup.txt', **kwargs):
        """
        Handles custom text/html which will be displayed in mouse-over popups for nodes/leaves.

        :param data: list, a nested list consisting of tuples or lists.
        
        Each inner tuple should have 2 elements which define node id and label content. Content can be plain text or any
        valid HTML (including links to external web sites, or IMG tags pointing to external images). Internal tree
        nodes can be specified using IDs directly, or using the 'last common ancestor' method described in `ITOL
        help page <http://itol.embl.de/help.cgi>`_. See `popup_info_template.txt
        <http://itol.embl.de/help/popup_info_template.txt>`_ for more details.

        The nested list ``popups`` shows a general data structure and these
        data will set two popup items::
        
            s1 = 'This is the popup title,<h1>Some header</h1><p>Information comes here</p>'
            s2 = '<img src="https://images-na.ssl-images-amazon.com/images/I/91gyeWnRc2L._SL1500_.jpg"/>'
            n1 = 'Zbumxj osiapem, info popup,<h1>Homo sapiens</h1><p style="color:blue">More info at'
            n2 = '<a target="_blank" href="https://en.wikipedia.org/wiki/Binomial_nomenclature"> WiKi</a></p>'
            
            popups = [('6304|7550', s1 + s2), (6321, n1 + n2)]
        """

        _args(locals(), data, separator, outfile, 'POPUP_INFO', self.wd)

    def binary(self, data, separator='comma', dataset_label='binary', color='#ff0000', field_shapes='1',
               field_labels='f1', field_colors='#ff0000', outfile='binary.txt', **kwargs):
        
        """
        Handles binary datasets visualization.
        
        :param data: list, a nested list consisting of tuples or lists.
        
        Each inner tuple or list should have at least 2 elements which define node id and one shape or combined shapes.
        If use combined shapes, the delimiter between different shapes should be consisted with the argument separator.
        See `dataset_binary_template.txt <http://itol.embl.de/help/dataset_binary_template.txt>`_ for more details.
        
        
        * The nested list ``data`` shows a general data structure.
        * The field_shapes define the shape of four fields corresponding to data.
        * The shape_labels define the label of each field.
        * The field_colors define the color of each field.
        
        Example::
        
            data = [(8518, '1,0,-1,0'), ('6529', 1, 0, -1, 0),
                    (6321, 0, 1, 0, -1), (2055, 0, 0, 0, -1)]
            filed_shape = '2,4,5,1'
            field_labels = 'f2,f4,f5,f1'
            field_colors = '#ff0000,#00ff00,#ffff00,#ff8000'
        """

        _args(locals(), data, separator, outfile, 'DATASET_BINARY', self.wd)

    def sbar(self, data, separator='comma', dataset_label='sbar', color='#ff0000',
             dataset_scale='', legend_title='', legend_shapes='', legend_colors='', legend_labels='',
             outfile='sbar.txt', **kwargs):

        """
        Handles simple bar chart.

        :param data: list, a nested list consisting of tuples or lists.
        
        Each inner tuple or list should have 2 elements which define node id and a single numeric value which is
        displayed as a bar outside the tree. Internal tree nodes can be specified using IDs directly, or using the
        'last common ancestor' method described in `ITOL help page <http://itol.embl.de/help.cgi>`_. See
        `dataset_simplebar_template.txt <http://itol.embl.de/help/dataset_simplebar_template.txt>`_ for more details.

        The nested list ``data`` shows a general data structure::
    
            data = [(8518, 200), ('6529', 330), (6321, 180),
                    (2055, 403), ('9151', 500), ('1921', 360)]
        """

        _args(locals(), data, separator, outfile, 'DATASET_SIMPLEBAR', self.wd)

    def mbar(self, data, separator='comma', dataset_label='mbar', color='#ff0000',
             field_colors='#ff0000,#00ff00,#0000ff', field_labels='f1,f2,f3',
             dataset_scale='', legend_title='', legend_shapes='', legend_colors='', legend_labels='',
             outfile='mbar.txt', **kwargs):
        

        """
        Handles multi-value bar chart.

        :param data: list, a nested list consisting of tuples or lists.
        
        Each inner tuple or list should have at least 3 elements which define node id and multiple numeric value which
        are displayed as stocked or aligned bar chart. See `dataset_multibar_template.txt
        <http://itol.embl.de/help/dataset_multibar_template.txt>`_ for more details.
        
        The nested list ``data`` shows a general data structure::
        
            data = [(8518, 200, 320), ('6529', 330, 230),
                    (6321, 180, 400), (2055, 403, 500),
                    ('9151', 500, 350)]
        """

        _args(locals(), data, separator, outfile, 'DATASET_MULTIBAR', self.wd)

    def pie(self, data, separator='comma', dataset_label='pie', color='#ff0000',
            field_colors='#ff0000,#00ff00,#0000ff', field_labels='f1,f2,f3',
            legend_title='', legend_shapes='', legend_colors='', legend_labels='',
            outfile='pie.txt', **kwargs):

        """
        Handles pie chart.

        :param data: list, a nested list consisting of tuples or lists.
        
        Each tuples or list should have at least 5 elements which define node id, position, radius, and multiple numeric
        value (at least 2 values) which are displayed as a pie chart directly on the branch, or outside the tree.
        See `dataset_piechart_template.txt <http://itol.embl.de/help/dataset_piechart_template.txt>`_ for more details.
        
        * The nested list ``data`` shows a general data structure (ID, position, radius, value1, value2, value3...).
        * The field_labels define label name of each field
        * The filed_colors define label color of each field
    
        Example::
        
            data = [(8518, -1, 30, 20, 32, 50),
                    ('6529', 0.5, 20, 33, 23, 46),
                    (6321, 1, 15, 18, 40, 35)]
            field_labels = 'A,B,C'
            field_colors = '#ff0000,#00ff00,#ffff00'
        """

        _args(locals(), data, separator, outfile, 'DATASET_PIECHART', self.wd)

    def text(self, data, separator='comma', dataset_label='text', color='#ff0000', outfile='text.txt', **kwargs):

        """
        Handles text labels.

        :param data: list, a nested list consisting of tuples or lists.
        
        Each inner tuple or list should have at least 2 elements which define node id and a label, possible additional
        elements can be tailed in the order of position, color, style, size factor, and rotation.
        See `dataset_text_template.txt <http://itol.embl.de/help/dataset_text_template.txt>`_ for more details.
        
        The nested list ``data`` shows a general data structure (ID, label,
        position, color, style, size_factor, rotation)::
        
            data = [(8518, 'Baq hxzgs', '-1', '#0000ff', 'bold', 2, 0),
                    ('6529', 'Wjk nduvpbl', 0, '#00ff00', 'italic', 1),
                    (6321, 'Zbumxj osiapem', 1, '#ff8000', 'bold-italic', 1)]
        """

        _args(locals(), data, separator, outfile, 'DATASET_TEXT', self.wd)

    def strip(self, data, separator='comma', dataset_label='strip', color='#ff0000',
            color_branch=0, legend_title='', legend_shapes=0, legend_colors=0, legend_labels=0,
            outfile='strip.txt', **kwargs):

        """
        Handles colored strips.

        :param data: list, a nested list consisting of tuples or lists.
        
        Each inner tuple or list should have at least 2 elements which define node id(s) and color, possible third
        element should be a string (string is displayed in the mouse-over popups).
        Internal tree nodes can be specified using IDs directly, or using the 'last common ancestor' method described in
        `ITOL help page <http://itol.embl.de/help.cgi>`_. See
        `dataset_color_strip_template.txt <http://itol.embl.de/help/dataset_color_strip_template.txt>`_ for details.

        The nested list ``data`` shows a general data structure (ID, color,
        <label>)::
            
            data = [(8518, '#0000ff', 'Baq hxzgs'),
                    ('6529', '#00ff00'),
                    (6321, '#ff8000', 'Zbumxj osiapem')]
        """

        _args(locals(), data, separator, outfile, 'DATASET_COLORSTRIP', self.wd)

    def gradient(self, data, separator='comma', dataset_label='gradient', color='#ff0000',
                 legend_title='', legend_shapes='', legend_colors='', legend_labels='',
                 outfile='gradient.txt', **kwargs):

        """
        Handles colored gradients

        :param data: list, a nested list consisting of tuples or list.
        
        Each inner tuple or list should have 2 elements which define node id(s) and a value. Internal tree nodes can be
        specified using IDs, or using the 'last common ancestor' method described in
        `ITOL help page <http://itol.embl.de/help.cgi>`. See
        `dataset_gradient_template.txt <http://itol.embl.de/help/dataset_gradient_template.txt>`_ for more details.

        The nested list ``data`` shows a general data structure (ID and and a value)::
            
            data = [(8518, 200), ('6529', 330), (6321, 180),
                    (2055, 403), ('9151', 500), ('1921', 360)]
        """

        _args(locals(), data, separator, outfile, 'DATASET_GRADIENT', self.wd)

    def connection(self, data, separator='comma', dataset_label='connection', color='#ff0000',
            legend_title='', legend_shapes=0, legend_colors=0, legend_labels=0,
            outfile='connection.txt', **kwargs):

        """
        Handles connections visualization.

        :param data: list, a nested list consisting of tuples or lists.
        
        Each inner tuple or list should have 5 elements which define a single connection between 2 nodes and consists
        of the following format: NODE1, NODE2, WIDTH, COLOR, LABEL. Color can be specified in hexadecimal string. See
        `dataset_connections_template.txt <http://itol.embl.de/help/dataset_connections_template.txt>`_ for details.

        The nested list ``data`` shows a general data structure (NODE1,
        NODE2, WIDTH, COLOR, LABEL)::
    
            data = [(8518, 2055, 4, '#ff0000', 'Con-A'),
                    ('7396', 7102, 2, '#ffff00', 'Con-B')]
        """

        _args(locals(), data, separator, outfile, 'DATASET_CONNECTION', self.wd)

    def heatmap(self, data, separator='comma', dataset_label='heatmap', color='#ff0000',
                field_labels='f1 f2 f3 f4 f5 f6', field_tree='',
                legend_title='', legend_shapes='', legend_colors='', legend_labels='', outfile='heatmap.txt', **kwargs):

        """
        Handles heatmap visualization.

        :param data: list, a nested list consisting of tuples or lists.
        
        Each inner tuple or list should have at least 2 elements which define node id(s) and multiple values.
        See `dataset_heatmap_template.txt <http://itol.embl.de/help/dataset_heatmap_template.txt>`_ for more details.

        The nested list ``data`` shows a general data structure (ID, value1,
        value2, value3...)::
    
            data = [(8518, 30, 20, 32, 50),
                    ('6529', 20, 33, 23, 46),
                    (6321, 15, 18, 40, 35)]
        
        The field_labels define name of four fields::
        
            field_labels = 'A,B,C,D'
        """

        _args(locals(), data, separator, outfile, 'DATASET_HEATMAP', self.wd)

    def boxplot(self, data, separator='comma', dataset_label='boxplot', color='#ff0000',dataset_scale='',
            outfile='boxplot.txt', **kwargs):

        """
        Handles boxplot visualization.

        :param data: list, a nested list consisting of tuples or lists.
        
        Each inner tuple or list should have at least 2 elements which define node id(s) and multiple values. See
        `dataset_boxplot_template.txt <http://itol.embl.de/help/dataset_boxplot_template.txt>`_ for more details.

        The nested list ``data`` shows a general data structure (ID1,
        minimum, q1, median, q3, maximum, value1, ...)::
    
            data = [(8518, 20, 25, 32, 44, 55, 60),
                    ('6529', 20, 23, 30, 46, 58, 18),
                    (6321, 15, 18, 29, 35, 45, 40)]
        """

        _args(locals(), data, separator, outfile, 'DATASET_BOXPLOT', self.wd)

    def domain(self, data, separator='comma', dataset_label='domain', color='#ff0000', width=1000,
            dataset_scale=0, legend_title='', legend_shapes='', legend_colors='', legend_labels='',
            outfile='domain.txt', **kwargs):

        """
        Handles protein domains visualization.

        :param data: list, a nested list consisting of tuples or lists.
        
        Each inner tuple or list should have at least 3 elements which define node id(s), total protein length (an
        integer) and unlimited number of domain definition strings.
        Each domain definition string consists of 5 parts, separated with vertical lines: shape|start|end|color|label
        See http://itol.embl.de/help/dataset_boxplot_template.txt for more details.

        The nested list ``data`` shows a general data structure (ID1, length, D1, D2, D3, ...)::
    
            data = [(8518, 1200, 'RE|100|150|#ff0000|SH2', 'EL|400|500|#0000ff|SH3', 'OC|700|900|#00ff00|PH')]
        """

        _args(locals(), data, separator, outfile, 'DATASET_DOMAINS', self.wd)

    def shape(self, data, separator='comma', dataset_label='shape', color='#ff0000',
            field_colors='#ff0000,#00ff00,#0000ff', field_labels='f1,f2,f3', outfile='shape.txt', **kwargs):

        """
        Handles external shapes visualization.

        :param data: list, a nested list consisting of tuples or lists.
            Each inner tuple or list should have at least 2 elements which define node id and multiple values. See
            `dataset_external_shapes_template.txt <http://itol.embl.de/help/dataset_external_shapes_template.txt>`_.

        The nested list ``data`` shows a general data structure (ID1, length, D1, D2, D3, ...)::

            data = [(8518, 20, 25, 32, 44, 55, 60),
                    ('6529', 20, 23, 30, 46, 58, 18),
                    (6321, 15, 18, 29, 35, 45, 40)]
        """

        _args(locals(), data, separator, outfile, 'DATASET_EXTERNALSHAPE', self.wd)

    def symbol(self, data, separator='comma', dataset_label='symbol', color='#ff0000',
               legend_title='', legend_shapes=0, legend_colors=0, legend_labels=0, outfile='symbol.txt', **kwargs):

        """
        Handling external shapes.

        :param data: list, a nested list consisting of tuples.
            Each inner tuple or list should have at least 6 elements which define node id, symbol, size, color, fill,
            position, may or may not followed by an additional element label.
            See `dataset_symbols_template.txt <http://itol.embl.de/help/dataset_symbols_template.txt>`_ for more details.
        
        The nested list ``data`` shows a general data structure (ID, symbol,
        size, color, fill, position, label)::
            
            data = [(8518, 1, 20, '#ff0000', 1, 0, 'A'),
                    ('6529', 2, 40, '#00ff00', 0, 0.5, 'B'),
                    (6321, 3, 60, '#ffff00', 1, 1, 'C')]
        """
        _args(locals(), data, separator, outfile, 'DATASET_SYMBOL', self.wd)
    
    def alignment(self, data, separator='comma', dataset_label='alignment', color='#ff0000',
                  custom_color_scheme=COLOR_SCHEME, outfile='alignment.txt', **kwargs):
        """
        Handles multiple sequence alignments visualization.
        
        :param data: str, path of an alignment file (in FASTA format). See
            `help/dataset_alignment_template.txt <http://itol.embl.de/help/dataset_alignment_template.txt>`_ for details.
        
        TODO: add support for handling alignment files in different formats (i.e. phylip, clustal, ...)
        """
        
        args = locals()
        for arg in ('self', 'data', 'separator', 'outfile'):
            args.pop(arg)

        if isinstance(separator, str):
            s = separator.upper()
            if s in DELIMITER:
                sep = 'SEPARATOR {}'.format(s)
                delimiter = s
            else:
                raise ValueError(
                    'Argument sep should be one of these: {} (case insensitive).'.format(', '.join(DELIMITER)))
        else:
            raise ValueError('Argument sep should be a string, e.g. tab, TAB, comma, COMMA, space or SPACE.')
        
        try:
            with open(data) as f:
                data_block = f.read()
        except IOError:
            raise IOError('File {} may not be a alignment file or does not exist.'.format(data))

        setting_block = '\n'.join([DELIMITER[delimiter].join([k.upper(), str(v)]) for k, v in args.items() if v])

        text = '\n'.join(['DATASET_ALIGNMENT', sep, setting_block, 'DATA', data_block])

        if not isinstance(outfile, str):
            raise ValueError('Argument outfile should be a string!')

        if not outfile.endswith('.txt'):
            outfile = ''.join([outfile, '.txt'])

        with open(os.path.join(self.wd, outfile), 'w') as out:
            out.write(text)

    def line(self, data, separator='comma', dataset_label='line', color='#ff0000', line_colors='', axis_x='', axis_y='',
            outfile='line.txt', **kwargs):
        """
        Handles line chart visualization.

        :param data: list, a nested list consisting of tuples.
        
        Each inner tuple or list should have at least 3 elements which define node id and 2 or more points associated.
        For each individual point, a string consisting of X and Y values separated by a vertical line. See
        `dataset_linechart_template.txt <http://itol.embl.de/help/dataset_linechart_template.txt>`_ for more details.
        
        The nested list ``data`` shows a general data structure (ID, X1|Y1 X2|Y2 X3|Y3, ...).
    
        data = [(8518, '-10|-15', '0|0', '5|3'), ('6529', '0|0', '10|5', '20|10', '30|15')]
        
            .. note::
                DATASET_LINECHART is not supported in batch mode yet, this method can be used to generated the
                data file for line chart. When you try to upload the data file to the ITOL server, a warning will be
                issued. If you try to use the ``.download()`` method to download data, an error (Invalid SVG received from
                headless browser) will be logged. The purpose of this method is mainly for programmatically generating
                the data file for lines. In future, if batch access of DATASET_LINECHART is allowed, then you can feel
                free to use the full function of this method.
                
        """

        _args(locals(), data, separator, outfile, 'DATASET_LINECHART', self.wd)

    def image(self, data, separator='comma', dataset_label='image', color='#ff0000', outfile='image.txt', **kwargs):
        """
        Handling image dataset visualization.

        :param data: list, a nested list consisting of tuples or lists.
        
        Each inner tuple or list should have 7 elements which define node id, position, size_factor, rotation,
        horizontal_shift, vertical_shift, and image_url.
        See `dataset_image_template.txt <https://itol.embl.de/help/dataset_image_template.txt>`_ for more details.

        Example::
        
            data = [('9606', -1, 1, 0, 0, 0, 'http://itol.embl.de/img/species/9606.jpg'),
            ('4530', 1, 1, 0, 0, 0, 'http://itol.embl.de/img/species/4530.jpg'),
            ('6239|6239', 0, 1, 90, 0, 0, 'http://itol.embl.de/img/species/6239.jpg')]
            
        .. note::
        
            DATASET_IMAGE is not supported in batch mode yet, this method can be used to generated the
            data file for image. When you try to upload the data file to the ITOL server, a warning will be
            issued. If you try to use the ``.download()`` method to download data, an error (Invalid SVG received from
            headless browser) will be logged. The purpose of this method is mainly for programmatically generating
            hte data file for image. In future, if batch access of DATASET_IMAGE is allowed, then you can feel free to
            use the full function of this method.
        """

        _args(locals(), data, separator, outfile, 'DATASET_IMAGE', self.wd)

    def upload(self, tn='', uid='', pn='', td='', folder=False):

        """
        Zip tree file and all notation files (text files have .txt extension) inside work directory into a zip file
        and upload the zip file to ITOL server (batch upload).

        :param tn: str, if not provided, the basename of the tree file will be used instead.
        :param uid: str, your upload ID, which is generated when you enable batch uploading in your account. If an
            uploadID is not provided, the tree will not be associated with any account, and will be deleted after 30 days.
        :param pn: str, required if ID is specified, case sensitive, and should be unique in your account.
        :param td: str, description of your tree, ignored if ID is not specified.
        :param folder: bool, whether zip all text files (must have .txt extension) in the work directory or not. If
            set to True, zip all text files in the folder, otherwise only zip and upload the tree file.

        .. note::
        
            A new ZIP archive (named iTOL.tree.zip) will be automatically created in work directory every time you
            call this method if tfile was provided via argument ``tfile``. If a ZIP file was provided via
            argument ``zfile``, the ZIP file will not be touched but directly upload to ITOL server.
        """

        if is_zipfile(self.tree):
            zfile = self.tree
            info('Using existing ZIP file {}.'.format(zfile))
        else:
            zfile = os.path.join(self.wd, 'iTOL.tree.zip')
            info('Creating ZIP file {}.'.format(zfile))
            with ZipFile(zfile, 'w') as zf:
                if folder:
                    basename = os.path.basename(self.tree)
                    files = [name for name in os.listdir(self.wd) if name != basename and name.endswith('.txt')]
                    if files:
                        for fn in files:
                            zf.write(fn, arcname=fn)
                zf.write(self.tree, arcname=os.path.basename(self.tree))

        args = {'treeName': tn if tn else os.path.basename(self.tree)}
        if uid:
            args['uploadID'] = uid
        if pn:
            args['projectName'] = pn
        if td:
            args['treeDescription'] = td

        if not args['uploadID']:
            warn('Warning!!! No upload ID was provided!')
            warn('The tree will not be associated with any account and will be deleted after 30 days!')
        
        info('Uploading ZIP file {} to ITOL server.'.format(zfile))
        respond = requests.post(UPLOAD_URL, data=args, files={'zipFile': open(zfile, 'rb')})
        msg = respond.text.rstrip()
        
        if msg.startswith('SUCCESS'):
            code, treeID = msg.split(': ')
            self.treeID = treeID
            info('Upload successfully. You can access the tree using the following iTOL tree ID: \n\t{}'.format(treeID))
            
            url = 'https://itol.embl.de/tree/{}'.format(treeID)
            self.url = url
            info('You can also view your tree in browser using the following URL: \n\t{}'.format(url))
        elif msg.startswith('WARNING'):
            lines = msg.split('\n')
            warn('Upload successfully, but you get the following warning message: \n\t{}'.format('\n'.join(lines[:-1])))
            code, treeID = lines[-1].split(': ')
            self.treeID = treeID
            info('You can access the tree using the following iTOL tree ID: \n\t{}'.format(treeID))

            url = 'https://itol.embl.de/tree/{}'.format(treeID)
            self.url = url
            info('You can also view your tree in browser using the following URL: \n\t{}'.format(url))
        else:
            error('Upload failed due to the following reason:\n\t{}'.format(msg))
            sys.exit(1)
            
        return treeID, url
    
    def download(self, tid='', fmt='pdf', outfile='', **kwargs):
        """
        Download (or export) data from ITOL server (batch download).
        
        :param tid: str, ITOL tree ID or URL (of the tree) which will be exported.
        :param fmt: str, output file format, supported values are: svg, eps, pdf and png for graphical formats and
            newick, nexus and phyloxml for text formats.
        :param outfile: str, path of the output file.
        :param kwargs: optional parameters see https://itol.embl.de/help.cgi#bExOpt for more details.
        :return: str, path of the output file.
        """
        
        if tid:
            try:
                treeID = str(tid)
            except ValueError:
                error('Invalid treeID, argument treeID accepts a string or numerical format iTOL tree ID.')
                sys.exit(1)
            if treeID.startswith('http'):
                treeID = treeID.split('/')[-1]
                
        elif self.treeID:
            treeID = self.treeID
        else:
            raise ValueError('No treeID provided, please upload a tree first or proved a treeID.')
        
        if isinstance(fmt, str):
            fmt = fmt.lower()
            formats = ['svg', 'eps', 'pdf', 'png', 'newick', 'nexus', 'phyloxml']
            if fmt not in formats:
                raise ValueError("Invalid format. Supported formats: \n\t{}.".format(', '.join(formats)))
        else:
            raise TypeError('Invalid output format, argument format accepts a string representing output format.')

        args = kwargs
        args['tree'] = treeID
        args['format'] = fmt
        
        respond = requests.get(DOWNLOAD_URL, params=args)
        msg = respond.text.rstrip()

        code = msg.split(':')[0]
        if code == 'ERROR':
            error('Download failed due to the following reason:\n\t{}'.format(msg))
            sys.exit(1)
        elif code.startswith('Invalid'):
            error('Download failed due to the following reason:\n\t{}'.format(msg))
            sys.exit(1)
        else:
            outfile = outfile if outfile else os.path.join(self.wd, 'iTOL.download.{}'.format(fmt))
            try:
                with open(outfile, 'wb') as out:
                    out.write(respond.content)
                info('Download successfully and data has been saved to:\n\t{}'.format(os.path.abspath(outfile)))
            except IOError:
                error('Save data to file {} failed, location may not be writable.'.format(outfile))
        return outfile
    
    
def main():
    des = 'Command line tool for ITOL (http://itol.embl.de) bach access.'
    epilog = """Either a tree file (regular text file), a ZIP file, a tree ID or tree URL assigned by ITOL can be
            passed as DATA argument. It will automatically check the type of the data. If a regular text file is provided,
            it assumes the text file is a tree file in Newick, Nexus, PhyloXML or Jplace format. The name of the tree file
            will be automatically renamed to have the extension '.tree' or '.tree.txt', if necessary. The text file will be
            zipped into a temporary ZIP file for uploading and the temporary ZIP file will be deleted upon the process exit.
            If a ZIP file is provided, however, users are responsible for renaming the name of the tree file and make sure
            the file have the extension '.tree' or '.tree.txt'. The user provided ZIP file will not be modified or deleted.
            In case a treefile is in use, the '-f' flag will zip and upload all text files (must have .txt extension) saved
            along with the tree file to ITOL. If a tree ID or URL is provided, it will download data from the ITOL server.
            If no outfile provided, the output will be saved in current work directory and named iTOL.download.[format]. All
            optional parameters for managing the behavior of downloading can also be used by add a '--' prefix before the name
            of the parameter (lower case), and followed by the value of the parameter (the parameter and the value need to be
            separated by a space), all available parameters can be found inside the ITOL help page. Argument not related
            to upload or download will be ignored, i.e. when you are uploading data, the `-o` option for output of the download
            will be ignored, while you are downloading, the '-n' option for a tree name will also be ignored.
            """
    
    parse = argparse.ArgumentParser(description=des, prog='itol',
                                    usage='%(prog)s DATA [OPTIONS]',
                                    epilog=epilog)
    
    parse.add_argument('DATA',
                       help='A tree file name, a ZIP file name, a tree ID or URL.')
    parse.add_argument('-i', help='Your upload ID (ID for batch uploading).',
                       metavar='uploadID')
    parse.add_argument('-n', help='The name you assign to the tree.',
                       metavar='treeName')
    parse.add_argument('-p', help='Project name, required if uploadID is set.',
                       metavar='projectName')
    parse.add_argument('-d', help='Description of your tree.',
                       metavar='treeDescription')
    parse.add_argument('-f',
                       help='Output file format, default: pdf. Graphical formats: svg, eps, pdf and png; '
                            'text formats: newick, nexus and phyloxml',
                       default='pdf')
    parse.add_argument('-o', help='Path of the output file.')
    parse.add_argument('-a',
                       help='Force zip all text files along with the tree file.',
                       action='store_true')
    
    args, unknown = parse.parse_known_args()
    data, uid, tn, pn, td, fmt, outfile, folder = args.DATA, args.i, args.n, args.p, args.d, args.f, args.o, args.a
    
    kwargs = {}
    for i, item in enumerate(unknown):
        if item.startswith('--'):
            try:
                kwargs[item[2:]] = unknown[i + 1]
            except IndexError:
                error('No value provided to optional parameter {}.'.format(
                        item[1:]))
            except KeyError:
                error('Invalid optional parameter {} provided.'.format(
                        item[1:]))
    
    if data.isdigit():
        if os.path.isfile(data):
            tf, zf = (None, data) if is_zipfile(data) else (data, None)
            t = TOL(tfile=tf, zfile=zf, wd=os.getcwd())
            t.upload(tn=tn, uid=uid, pn=pn, td=td, folder=folder)
        else:
            t = TOL(tfile='', zfile='', wd=os.getcwd(), leave=False)
            t.download(data, fmt=fmt, outfile=outfile, **kwargs)
    elif data.startswith('http'):
        t = TOL(tfile='', zfile='', wd=os.getcwd(), leave=False)
        t.download(data, fmt=fmt, outfile=outfile, **kwargs)
    elif os.path.isfile(data):
        tf, zf = (None, data) if is_zipfile(data) else (data, None)
        t = TOL(tfile=tf, zfile=zf, wd=os.getcwd())
        t.upload(tn=tn, uid=uid, pn=pn, td=td, folder=folder)
    else:
        error('Invalid data {}, data accepts a tree file, a ZIP file, a tree ID or URL.')

        
if __name__ == '__main__':
    main()
