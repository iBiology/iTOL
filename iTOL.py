#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Python API for phylogenetic tree visualization in Interactive Tree of Life (`ITOL <http://iTOL.embl.de>`_).
"""

import os
import sys
import shutil
from zipfile import ZipFile, is_zipfile
import requests
import logging

logger = logging.getLogger('[iTOL]')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# fh = logging.FileHandler('iTOL.log')
# fh.setLevel(logging.INFO), fh.setFormatter(formatter)
# logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO), ch.setFormatter(formatter)
logger.addHandler(ch)

warn, info, error = logger.warning, logger.info, logger.error


DELIMITER = {'TAB': '\t', 'SPACE': ' ', 'COMMA': ','}
UPLOAD_URL = "http://itol.embl.de/batch_uploader.cgi"
DOWNLOAD_URL = "http://itol.embl.de/batch_downloader.cgi"


def _sd(data, separator):
    """
    Private function for handles separator and data block (user should not use this functionary directly).
    
    :param data: nested tuple or list. Each inner element should have at least 3 elements which define the node,
                 type and color.
    :param separator: the separator which is used to delimit the setting text (tab, space or comma), default: comma.
    
    .. Note::
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
    
    .. Note::
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

    def __init__(self, tfile='', zfile='', wd='iTOL'):
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
            raise ValueError('Neither tree file nor ZIP file was provided.')
        
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
            
        .. code-block:: python
        
            colors = [
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

        .. code-block:: python
            
            labels = [
                (8518, 'Baq hxzgs'),
                ('6529', 'Wjk nduvpbl'),
                (6321, 'Zbumxj osiapem'),
                ('5784|7550', 'Clade A'),
                ('7396|2154', 'Clade B'),
                ('2055|539', 'Clade C')
                ]
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

        The nested list ``popups`` shows a general data structure and these data will set two popup items:

        .. code-block:: python
        
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
        
        .. code-block:: python
        
            data = [(8518, '1,0,-1,0'), ('6529', 1, 0, -1, 0), (6321, 0, 1, 0, -1), (2055, 0, 0, 0, -1)]
            
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

        The nested list ``data`` shows a general data structure:
    
            data = [(8518, 200), ('6529', 330), (6321, 180), (2055, 403), ('9151', 500), ('1921', 360)]
        """

        _args(locals(), data, separator, outfile, 'DATASET_SIMPLEBAR', self.wd)

    def mbar(self, data, separator='comma', dataset_label='mbar', color='#ff0000',
             field_colors='#ff0000,#00ff00,#0000ff', field_labels='f1,f2,f3',
             dataset_scale='', legend_title='', legend_shapes='', legend_colors='', legend_labels='',
             outfile='mbar.txt'):
        

        """
        Handles multi-value bar chart.

        :param data: list, a nested list consisting of tuples or lists.
        
        Each inner tuple or list should have at least 3 elements which define node id and multiple numeric value which
        are displayed as stocked or aligned bar chart. See `dataset_multibar_template.txt
        <http://itol.embl.de/help/dataset_multibar_template.txt>`_ for more details.
        
        The nested list ``data`` shows a general data structure:
        
            data = [(8518, 200, 320), ('6529', 330, 230), (6321, 180, 400), (2055, 403, 500), ('9151', 500, 350)]
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
    
        ..code-block:: python
        
            data = [(8518, -1, 30, 20, 32, 50), ('6529', 0.5, 20, 33, 23, 46), (6321, 1, 15, 18, 40, 35)]
            
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
        
        The nested list ``data`` shows a general data structure (ID, label, position, color, style, size_factor, rotation)

        .. code-block:: python
        
                data = [
                    (8518, 'Baq hxzgs', '-1', '#0000ff', 'bold', 2, 0),
                    ('6529', 'Wjk nduvpbl', 0, '#00ff00', 'italic', 1),
                    (6321, 'Zbumxj osiapem', 1, '#ff8000', 'bold-italic', 1),
                    ]
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

        The nested list ``data`` shows a general data structure (ID, color, <label>).
    
        .. code-block:: python
        
            data = [
                (8518, '#0000ff', 'Baq hxzgs'),
                ('6529', '#00ff00'),
                (6321, '#ff8000', 'Zbumxj osiapem'),
                ]
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

        The nested list ``data`` shows a general data structure (ID and and a value)
    
        data = [(8518, 200), ('6529', 330), (6321, 180), (2055, 403), ('9151', 500), ('1921', 360)]
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

        The nested list ``data`` shows a general data structure (NODE1, NODE2, WIDTH, COLOR, LABEL)
    
        data = [(8518, 2055, 4, '#ff0000', 'Con-A'), ('7396', 7102, 2, '#ffff00', 'Con-B')]
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

        The nested list ``data`` shows a general data structure (ID, value1, value2, value3...).
    
        data = [(8518, 30, 20, 32, 50), ('6529', 20, 33, 23, 46), (6321, 15, 18, 40, 35)]
        
        The field_labels define name of four fields.
        
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

        Examples:
            data = [(9606, 10000, 12000, 13000, 10000)]
            
            data = [('ID1', 200, 300, 400, 500), ('ID2', 250, 200, 150, 200, 300)]

        :param dataset_scale: scale can only be set by combined strings (format: VALUE or VALUE-LABEL-COLOR) separated
            by the delimiter which was assigned by argument separator. See http://itol.embl.de/help.cgi#dsScale for more
            details.

        Examples
            dataset_scale = '100,200,300,400,500' or dataset_scale = '100 200 300 400 500'
            
            dataset_scale = '2000-2k-#0000ff,10000-10k-#ff0000' or dataset_scale = '2000-2k-#0000ff 10000-10k-#ff0000'
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

        Example:
            data = [(9606, 1200, 'RE|100|150|#ff0000|SH2', 'EL|400|500|#0000ff|SH3', 'OC|700|900|#00ff00|PH')]

        :param dataset_scale: scale can only be set by combined strings (format: VALUE or VALUE-LABEL-COLOR) separated
            by the delimiter which was assigned by argument separator. See http://itol.embl.de/help.cgi#dsScale for
            more details.

        Examples:
            dataset_scale = '100,200,300,400,500' or dataset_scale = '100 200 300 400 500'

            dataset_scale = '2000-2k-#0000ff,10000-10k-#ff0000' or dataset_scale = '2000-2k-#0000ff\t10000-10k-#ff0000'

        :param legend_shapes: shapes can be set by a single shape string or a combined shape strings separated by the
            delimiter which was assigned by argument separator.

        Examples:
            legend_shapes = 1 or legend_shapes = '1'
            
            legend_shapes = '2,4,5,1' or legend_shapes = '2\t4\t5\t1' or legend_shapes = '2 4 5 1'

        :param legend_labels: labels can be set by a single shape value string or a combined label strings separated by
            the delimiter which was assigned by argument separator.

        Examples:
            legend_labels = 'b1'
            
            legend_labels = 'b2,b4,b5,b1' or legend_labels = 'b2\tb4\tb5\tb1' or legend_labels = 'b2 b4 b5 b1'

        :param legend_colors: colors can be set by a single color value string or a combined color strings separated by
            the delimiter which was assigned by argument separator.

        Examples:
            legend_colors = '#ff0000'
            
            legend_colors = '#ff0000,#00ff00,#ffff00,#0000ff' or legend_colors = '#ff0000 #00ff00 #ffff00 #0000ff'
        """

        _args(locals(), data, separator, outfile, 'DATASET_DOMAINS', self.wd)

    def shape(self, data, separator='comma', dataset_label='shape', color='#ff0000',
            field_colors='#ff0000,#00ff00,#0000ff', field_labels='f1,f2,f3', outfile='shape.txt', **kwargs):

        """
        Handles external shapes visualization.

        :param data: list, a nested list consisting of tuples or lists.
        Each inner tuple or list should have at least 2 elements which define node id and multiple values. See
        `dataset_external_shapes_template.txt <http://itol.embl.de/help/dataset_external_shapes_template.txt>`_.

        Examples:
            data = [(9606, 10, 10, 20, 40)]
            
            data = [('LEAF1|LEAF2', 50, 60, 80, 90)]

        :param field_labels: labels can be set by a single shape value string or a combined label strings separated by
            the delimiter which was assigned by argument separator.

        Examples:
            field_labels = 'f1'
            
            field_labels = 'f2,f4,f5,f1' or field_labels = 'f2\tf4\tf5\tf1' or field_labels = 'f2 f4 f5 f1'

        :param field_colors: colors can be set by a single color value string or a combined color strings separated by
            the delimiter which was assigned by argument separator.

        Examples:
            field_colors = '#ff0000'
            
            field_colors = '#ff0000,#00ff00,#ffff00,#0000ff' or field_colors = '#ff0000 #00ff00 #ffff00 #0000ff'
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
        Handles phylogenetic placements

        :param jplace: string, file name of .jplace files created by pplacer and RAxML.
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
        Handles multiple sequence alignments visualization.
        
        :param data: str, alignment in FASTA format.
        See http://itol.embl.de/help/dataset_alignment_template.txt for more details.
        """
        pass

    def line(self, data, separator='comma', dataset_label='line', color='#ff0000', line_colors='', axis_x='', axis_y='',
            outfile='line.txt', **kwargs):
        """
        Handles line chart visualization.

        :param data: list, a nested list consisting of tuples.
        
        Each inner tuple or list should have at least 3 elements which define node id and 2 or more points associated.
        For each individual point, a string consisting of X and Y values separated by a vertical line. See
        `dataset_linechart_template.txt <http://itol.embl.de/help/dataset_linechart_template.txt>`_ for more details.
        
        Examples:
            data = [('A', 'X1|Y1', 'X2|Y2', 'X3|Y3'), ('9606', '2|6', '0|0', '5|3'),
            ('B|C', '0|0', '10|5', '2|1', '13|15')]
        """
        
        pass

    def image(self, data, separator='comma', dataset_label='image', color='#ff0000', outfile='image.txt', **kwargs):
        """
        Handling image dataset visualization.

        :param data: list, a nested list consisting of tuples or lists.
        
        Each inner tuple or list should have 7 elements which define node id, position, size_factor, rotation,
        horizontal_shift, vertical_shift, and image_url. See `dataset_linechart_template.txt
        <http://itol.embl.de/help/dataset_linechart_template.txt.`_ for more details.

        Examples:
            data = [('9606', -1, 1, 0, 0, 0, 'http://itol.embl.de/img/species/9606.jpg'),
            ('4530', 1, 1, 0, 0, 0, 'http://itol.embl.de/img/species/4530.jpg'),
            ('6239|6239', 0, 1, 90, 0, 0, 'http://itol.embl.de/img/species/6239.jpg')]
        """
    
        pass

    def upload(self, tn='', uid='', pn='', td='', folder=False):

        """
        Zip tree file and all notation files (text files have .txt extension) inside work directory into a zip file
        and upload the zip file to ITOL server (batch upload).

        :param tn: str, if not provided, the tree file name (basename without extension) will be used instead.
        :param uid: str, your upload ID, which is generated when you enable batch uploading in your account. If an
        uploadID is not provided, the tree will not be associated with any account, and will be deleted after 30 days.
        :param pn: str, required if ID is specified, case sensitive, and should be unique in your account.
        :param td: str, description of your tree, ignored if ID is not specified.
        :param folder: bool, bool, whether zip all sister text files (must have .txt extension) saved along with the
        tree file. If set to True, zip all text files in the folder, otherwise only zip and upload the tree file.

        .. Note::
            A new ZIP archive (named iTOL.tree.zip) will be automatically created in work directory every time you
            call this method if tfile was provided. If a ZIP file was provided via zfile, the ZIP will not be modified
            or deleted and the same ZIP file will be uploaded to ITOL server.
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
                    # dn, basename = os.path.dirname(os.path.abspath(self.tree)), os.path.basename(self.tree)
                    # files = [name for name in os.listdir(dn) if name != basename and name.endswith('.txt')]
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
        else:
            error('Upload failed due to the following reason:\n\t{}'.format(msg))
            sys.exit(1)
            
        return treeID, url
    
    def download(self, tid='', fmt='pdf', outfile='', **kwargs):
        """
        Download (or export) a tree from ITOL server (batch download).
        
        :param tid: str, ITOL tree ID which will be exported.
        :param fmt: str, output file format, supported values are: svg, eps, pdf and png for graphical formats and
        newick, nexus and phyloxml for text formats.
        :param outfile: str, path of the output file.
        :param kwargs: optional parameters.
        :return:
        """
        if tid:
            if isinstance(tid, str):
                treeID = tid
            else:
                raise TypeError('Invalid treeID, argument treeID accepts a string pointing to a iTOL tree ID.')
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
        else:
            outfile = outfile if outfile else os.path.join(self.wd, 'iTOL.download.{}'.format(fmt))
            try:
                with open(outfile, 'wb') as out:
                    out.write(respond.content)
                info('Download successfully and data has been saved to:\n\t{}'.format(os.path.abspath(outfile)))
            except IOError:
                error('Save data to file {} failed, location may not be writable.'.format(outfile))
        return outfile

        
if __name__ == '__main__':
    pass
