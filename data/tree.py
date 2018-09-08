#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A simple script for generating fake phylogenetic tree with fake IDs and fake Latin names using ETE3.
"""

import logging
import random
import string
from ete3 import Tree

formatter = '%(levelname)s %(asctime)s %(name)s %(message)s'
logging.basicConfig(level=logging.ERROR, format=formatter, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('[iTOL-DATA]')
warn, info, error = logger.warning, logger.info, logger.error


def latin(minimum=3, maximum=8, separator=' '):
    """
    Simple function to generate fake (two parts) Latin species names.
    
    :param minimum: int, minimum number of letters in each part of the Latin name.
    :param maximum: int, maximum number of letters in each part of the Latin name.
    :param separator: str, a delimiter which separated two parts of the Latin name.
    :return: str, a space separated two parts fake Latin name.
    """
    
    genus = ''.join(random.sample(string.ascii_lowercase, random.randint(3, 8)))
    epithet = ''.join(random.sample(string.ascii_lowercase, random.randint(3, 8)))
    return separator.join([genus.title(), epithet])


def tree(n, names):
    """
    Simple function to generate fake phylogenetic tree using ETE3.
    
    :param n: int, the number of terminal nodes (or leaves) expected to generate.
    :param name: dict, node id, name dictionary for labeling terminal nodes.
    """
    
    t = Tree()
    t.populate(n, names_library=names.keys(), random_branches=True, support_range=(0.7, 1))
    t.write(format=2, outfile='fake.tree.newick', dist_formatter='%0.4g', support_formatter='%0.4g')
    with open('fake.tree.notation.tsv', 'w') as o:
        o.write('#TaxaID\tName\n')
        o.writelines('{}\t{}\n'.format(k, v) for k, v in names.items())

    
if __name__ == '__main__':
    # Generate fake taxa IDs
    number = 60
    ids = random.sample(range(1, 10000), number)
    
    # Assign a fake taxon ID to a fake Latin name
    names = {i: latin() for i in ids}
    
    # Generate a fake tree using fake names
    tree(number, names)
