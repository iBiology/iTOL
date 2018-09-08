#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import iTOL
import os
import time

logger = logging.getLogger('[iTOL]')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

logger.setLevel(logging.INFO)

fh = logging.FileHandler('color.log')
fh.setLevel(logging.INFO), fh.setFormatter(formatter)
logger.addHandler(fh)

warn, info, error = logger.warning, logger.info, logger.error

if __name__ == '__main__':
    uploadID = 'p4Wug0RBrghlsMfh6oXngg'
    data_path = os.path.join(os.path.dirname(iTOL.__file__), 'data')
    tree, data = os.path.join(data_path, 'fake.tree.newick'), os.path.join(data_path, 'fake.tree.notation.tsv')
    wd = os.getcwd()

    t = iTOL.TOL(tfile=tree, wd=wd)

    """
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
    """
    
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

    t.color(colors)

    t.upload(tn='color', uid=uploadID, pn='Demo', td='Color-example', folder=True)

    time.sleep(15)
    
    # Display range legend using include_ranges_legend=1
    t.download(display_mode=2, include_ranges_legend=1)
