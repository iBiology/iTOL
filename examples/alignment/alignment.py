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

fh = logging.FileHandler('alignment.log')
fh.setLevel(logging.INFO), fh.setFormatter(formatter)
logger.addHandler(fh)

warn, info, error = logger.warning, logger.info, logger.error

if __name__ == '__main__':
    uploadID = 'p4Wug0RBrghlsMfh6oXngg'
    data_path = os.path.join(os.path.dirname(iTOL.__file__), 'data')
    tree, alignment = os.path.join(data_path, 'fake.tree.newick'), os.path.join(data_path, 'fake.alignment.fasta')
    wd = os.getcwd()

    t = iTOL.TOL(tfile=tree, wd=wd)

    t.alignment(alignment)

    t.upload(tn='alignment', uid=uploadID, pn='Demo', td='Alignment-example', folder=True)

    time.sleep(15)

    # Set display_mode=0 to display the tree in normal mode (alignment cannot be displayed in circular mode).
    # Set datasets_visible='0' to make the pie dataset visible.
    t.download(display_mode=0, datasets_visible=0)
