#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import iTOL
import os
import time

logger = logging.getLogger('[iTOL]')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

logger.setLevel(logging.INFO)

fh = logging.FileHandler('image.log')
fh.setLevel(logging.INFO), fh.setFormatter(formatter)
logger.addHandler(fh)

warn, info, error = logger.warning, logger.info, logger.error

if __name__ == '__main__':
    uploadID = 'p4Wug0RBrghlsMfh6oXngg'
    data_path = os.path.join(os.path.dirname(iTOL.__file__), 'data')
    tree, notation = os.path.join(data_path, 'fake.tree.newick'), os.path.join(data_path, 'fake.tree.notation.tsv')
    wd = os.getcwd()

    t = iTOL.TOL(tfile=tree, wd=wd)

    # The nested list ``data`` shows a general data structure:
    # (ID, position, size_factor, rotation, horizontal_shift, vertical_shift,image_url).
    
    u1 = 'http://smart.embl.de/smart/DDvec.cgi?smart=1086:TyrKc(189|448)+SH3(454|510)+Pfam_Inhibitor_Mig-'
    u2 = '6(852|918)+0(57|62)+1(117|122)+0(141|146)+0(215|220)+0(266|271)+2(358|363)+0(401|406)+0(450|455)'
    u3 = '+2(481|486)+2(546|551)+1(577|582)+1(592|597)+0(1042|1047)+2(1084|1089)+0(1086|1091)'
    data = [(8518, -1, 1, 0, 0, 0, 'http://itol.embl.de/img/species/9606.jpg'),
            ('6529', 1, 1, 0, 0, 0, 'http://itol.embl.de/img/species/4530.jpg'),
            (6321, 1, 1, 0, 0, 0, u1 + u2 + u3),
            ('5784|729', 0, 1, 90, 0, 0, 'http://itol.embl.de/img/species/6239.jpg')]

    t.image(data)

    t.upload(tn='image', uid=uploadID, pn='Demo', td='Image-example', folder=True)

    time.sleep(15)

    # Set datasets_visible='0' to make the pie dataset visible.
    t.download(display_mode=2, datasets_visible='0')
