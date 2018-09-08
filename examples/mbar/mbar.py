#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import iTOL
import os
import time

logger = logging.getLogger('[iTOL]')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

logger.setLevel(logging.INFO)

fh = logging.FileHandler('mbar.log')
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
    """
    
    data = [(8518, 200, 320), ('6529', 330, 230), (6321, 180, 400), (2055, 403, 500), ('9151', 500, 350)]

    t.mbar(data)

    t.upload(tn='mbar', uid=uploadID, pn='Demo', td='Mbar-example', folder=True)

    time.sleep(15)

    # Set datasets_visible='0' to make the mbar dataset visible.
    t.download(display_mode=2, datasets_visible='0')
