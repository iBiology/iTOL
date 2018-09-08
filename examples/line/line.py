#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import iTOL
import os
import time

logger = logging.getLogger('[iTOL]')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

logger.setLevel(logging.INFO)

fh = logging.FileHandler('line.log')
fh.setLevel(logging.INFO), fh.setFormatter(formatter)
logger.addHandler(fh)

warn, info, error = logger.warning, logger.info, logger.error

if __name__ == '__main__':
    uploadID = 'p4Wug0RBrghlsMfh6oXngg'
    data_path = os.path.join(os.path.dirname(iTOL.__file__), 'data')
    tree, notation = os.path.join(data_path, 'fake.tree.newick'), os.path.join(data_path, 'fake.tree.notation.tsv')
    wd = os.getcwd()

    t = iTOL.TOL(tfile=tree, wd=wd)

    # The nested list ``data`` shows a general data structure (ID, position, radius, value1, value2, value3...).
    
    data = [(8518, '-10|-15', '0|0', '5|3'), ('6529', '0|0', '10|5', '20|10', '30|15')]

    t.line(data)

    # DATASET_LINECHART is not supported in batch mode yet, a warning message will be displayed.
    t.upload(tn='line', uid=uploadID, pn='Demo', td='Line-example', folder=True)

    time.sleep(15)

    # Set datasets_visible='0' to make the pie dataset visible.
    # DATASET_LINECHART is not supported in batch mode yet, download will fail due to the following reason:
    # 'Invalid SVG received from headless browser.'
    t.download(display_mode=2, datasets_visible='0')
