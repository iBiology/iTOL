#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import iTOL
import os
import time

logger = logging.getLogger('[iTOL]')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

logger.setLevel(logging.INFO)

fh = logging.FileHandler('binary.log')
fh.setLevel(logging.INFO), fh.setFormatter(formatter)
logger.addHandler(fh)

warn, info, error = logger.warning, logger.info, logger.error

if __name__ == '__main__':
    uploadID = 'p4Wug0RBrghlsMfh6oXngg'
    data_path = os.path.join(os.path.dirname(iTOL.__file__), 'data')
    tree, notation = os.path.join(data_path, 'fake.tree.newick'), os.path.join(data_path, 'fake.tree.notation.tsv')
    wd = os.getcwd()

    t = iTOL.TOL(tfile=tree, wd=wd)

    """
    * The nested list ``data`` shows a general data structure.
    * The field_shapes define the shape of four fields corresponding to data.
    * The shape_labels define the label of each field.
    * The field_colors define the color of each field.
    """
    
    data = [(8518, '1,0,-1,0'), ('6529', 1, 0, -1, 0), (6321, 0, 1, 0, -1), (2055, 0, 0, 0, -1)]
    filed_shape = '2,4,5,1'
    field_labels = 'f2,f4,f5,f1'
    field_colors = '#ff0000,#00ff00,#ffff00,#ff8000'

    t.binary(data, field_shapes=filed_shape, field_colors=field_colors, field_labels=field_labels)

    t.upload(tn='binary', uid=uploadID, pn='Demo', td='Binary-example', folder=True)

    time.sleep(15)

    # Set datasets_visible='0' to make the binary dataset visible.
    t.download(display_mode=2, datasets_visible='0')
