#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import iTOL
import os
import time

logger = logging.getLogger('[iTOL]')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

logger.setLevel(logging.INFO)

fh = logging.FileHandler('popup.log')
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
    The nested list ``popups`` shows a general data structure and these data will set two popup items.
    """
    s1 = 'This is the popup title,<h1>Some header</h1><p>Information comes here</p>'
    s2 = '<img src="https://images-na.ssl-images-amazon.com/images/I/91gyeWnRc2L._SL1500_.jpg"/>'
    
    n1 = 'Zbumxj osiapem, info popup,<h1>Homo sapiens</h1><p style="color:blue">More info at'
    n2 = '<a target="_blank" href="https://en.wikipedia.org/wiki/Binomial_nomenclature"> WiKi</a></p>'
    
    popups = [('6304|7550', s1 + s2), (6321, n1 + n2)]

    t.popup(popups)

    t.upload(tn='popup', uid=uploadID, pn='Demo', td='Popup-example', folder=True)

    time.sleep(15)
    
    # Popups only displayed in mouseover popups, downloaded image will not display it.
    # t.download(display_mode=2)
