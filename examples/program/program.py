#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import iTOL
import os
import time
from random import random, choice, choices
from itertools import chain

logger = logging.getLogger('[iTOL]')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

logger.setLevel(logging.INFO)

fh = logging.FileHandler('program.log')
fh.setLevel(logging.INFO), fh.setFormatter(formatter)
logger.addHandler(fh)

warn, info, error = logger.warning, logger.info, logger.error


if __name__ == '__main__':
    uploadID = 'p4Wug0RBrghlsMfh6oXngg'
    data_path = os.path.join(os.path.dirname(iTOL.__file__), 'data')
    tree, annotation = os.path.join(data_path, 'fake.tree.newick'), os.path.join(data_path, 'fake.tree.notation.tsv')
    alignment = os.path.join(data_path, 'fake.alignment.fasta')
    wd = os.getcwd()

    t = iTOL.TOL(tfile=tree, wd=wd)
    
    # Replace the fake Latin names (IDs) with their corresponding fake scientific names
    # Data structure (ID, name)
    names = [line.strip().split('\t') for line in open(annotation) if not line.startswith('#')]
    t.label(names)
    
    # Randomly change label color, font size and font mode
    colors = ['#800020', '#4f0d17', '#ff8d00', '#4f0d17', '#dfcbd4', '#d8beca', '#b2edc9', '#00447c', '#ff8d00',
              '#ffffb2', '#204ed3', '#a39298', '#c097aa', '#feb4b1', '#ffe200', '#f69191', '#ff288d', '#5f72ff',
              '#b17e95', '#f69191', '#c3cbe2', '#ffbec4', '#daedfe', '#18b6fd']
    modes = ['normal', 'bold', 'bold-italic', 'italic']
    # Data structure (ID, label_type, color, font_mode, font_size)
    data = [[name[0], 'label', choice(colors), choice(modes), random() * 10] for name in names]
    t.color(data)
    
    # Generate fake boxplot
    
    population = list(range(0, 300, 1))
    # Data structure (ID, minimum, q1, median, q3, maximum, value1, ...)
    data = [[name[0], sorted(choices(population, k=5))] for name in names]
    data = [list(chain.from_iterable(d)) for d in data]
    t.boxplot(data, outfile='1-boxplot.txt')
    
    # Generate fake simpe bar plot
    # Data structure (ID, value)
    data = [[name[0], choice(population)] for name in names]
    t.sbar(data, outfile='2-sbar.txt')
    
    # Generate fake pie char
    # Data structure (ID, position, radius, value1, value2, value3, ...)
    data = [[name[0], random(), choice(range(1, 30, 1)), choices(population, k=5)] for name in names]
    for d in data:
        print(d)
    data = [list(chain.from_iterable(d)) for d in data]
    t.pie(data, outfile='3-pie.txt')
    
    # t.upload(tn='color', uid=uploadID, pn='Demo', td='Color-example', folder=True)
    #
    # time.sleep(15)
    #
    # # Display range legend using include_ranges_legend=1
    # t.download(display_mode=2, include_ranges_legend=1)
