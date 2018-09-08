#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

sys.path.append('/Users/sky/Downloads/iTOL')

import logging
import iTOL
import os
import time

logger = logging.getLogger('[iTOL]')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

logger.setLevel(logging.INFO)

fh = logging.FileHandler('domain.log')
fh.setLevel(logging.INFO), fh.setFormatter(formatter)
logger.addHandler(fh)

warn, info, error = logger.warning, logger.info, logger.error

if __name__ == '__main__':
    uploadID = 'p4Wug0RBrghlsMfh6oXngg'
    data_path = os.path.join(os.path.dirname(iTOL.__file__), 'data')
    tree, notation = os.path.join(data_path, 'fake.tree.newick'), os.path.join(data_path, 'fake.tree.notation.tsv')
    wd = os.getcwd()

    t = iTOL.TOL(tfile=tree, wd=wd)

    # The nested list ``data`` shows a general data structure (ID1, length, D1, D2, D3, ...).
    
    data = [(8518, 1200, 'RE|100|150|#ff0000|SH2', 'EL|400|500|#0000ff|SH3', 'OC|700|900|#00ff00|PH')]

    t.domain(data)

    t.upload(tn='domain', uid=uploadID, pn='Demo', td='Domain-example', folder=True)

    time.sleep(15)

    # Set datasets_visible='0' to make the pie dataset visible.
    t.download(display_mode=2, datasets_visible='0')
