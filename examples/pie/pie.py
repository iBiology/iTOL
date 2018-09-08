#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import iTOL
import os
import time

logger = logging.getLogger('[iTOL]')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

logger.setLevel(logging.INFO)

fh = logging.FileHandler('pie.log')
fh.setLevel(logging.INFO), fh.setFormatter(formatter)
logger.addHandler(fh)

warn, info, error = logger.warning, logger.info, logger.error

if __name__ == '__main__':
    uploadID = 'p4Wug0RBrghlsMfh6oXngg'
    data_path = os.path.join(os.path.dirname(iTOL.__file__), 'data')
    tree, notation = os.path.join(data_path, 'fake.tree.newick'), os.path.join(data_path, 'fake.tree.notation.tsv')
    wd = os.getcwd()

    t = iTOL.TOL(tfile=tree, wd=wd)

    # The nested list ``data`` shows a general data structure (ID, position, radius, value1, value2, value3, ...).
    
    data = [(8518, -1, 30, 20, 32, 50), ('6529', 0.5, 20, 33, 23, 46), (6321, 1, 15, 18, 40, 35)]
    field_labels = 'A,B,C'
    field_colors = '#ff0000,#00ff00,#ffff00'

    t.pie(data, field_labels=field_labels, field_colors=field_colors)

    t.upload(tn='pie', uid=uploadID, pn='Demo', td='Pie-example', folder=True)

    time.sleep(15)

    # Set datasets_visible='0' to make the pie dataset visible.
    t.download(display_mode=2, datasets_visible='0')
