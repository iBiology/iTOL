#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import iTOL
import os
import time

logger = logging.getLogger('[iTOL]')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

logger.setLevel(logging.INFO)

fh = logging.FileHandler('label.log')
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
        * Leaf label for node 8518 will be renamed to Baq hxzgs
        * Leaf label for node 6529 will be renamed to Wjk nduvpbl
        * Leaf label for node 6321 will be renamed to Zbumxj osiapem
        * A internal branch will be renamed to Clade A (clade name displayed in mouseover popups)
        * A internal branch will be renamed to Clade B (clade name displayed in mouseover popups)
        * A internal branch will be renamed to Clade C (clade name displayed in mouseover popups)
    """
    
    labels = [
        (8518, 'Baq hxzgs'),
        ('6529', 'Wjk nduvpbl'),
        (6321, 'Zbumxj osiapem'),
        ('5784|7550', 'Clade A'),
        ('7396|2154', 'Clade B'),
        ('2055|539', 'Clade C')
      ]
    
    t.label(labels)
    
    # Make the replaced label names in green, bold italic and two times bigger
    colors = [(8518, 'label', '#00ff00', 'bold-italic', 2),
              ('6529', 'label', '#00ff00', 'bold-italic', 2),
              (6321, 'label', '#00ff00', 'bold-italic', 2)]

    t.color(colors)

    t.upload(tn='label', uid=uploadID, pn='Demo', td='Label-example', folder=True)

    time.sleep(15)

    t.download(display_mode=2)
