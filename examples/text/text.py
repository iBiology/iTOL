#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import iTOL
import os
import time

logger = logging.getLogger('[iTOL]')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

logger.setLevel(logging.INFO)

fh = logging.FileHandler('text.log')
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
    The nested list ``data`` shows a general data structure (ID, label, position, color, style, size_factor, rotation)
    """
    
    data = [
        (8518, 'Baq hxzgs', '-1', '#0000ff', 'bold', 2, 0),
        ('6529', 'Wjk nduvpbl', 0, '#00ff00', 'italic', 1),
        (6321, 'Zbumxj osiapem', 1, '#ff8000', 'bold-italic', 1),
      ]

    t.text(data)

    t.upload(tn='text', uid=uploadID, pn='Demo', td='Text-example', folder=True)

    time.sleep(15)
    
    t.download(display_mode=2, datasets_visible=0)
