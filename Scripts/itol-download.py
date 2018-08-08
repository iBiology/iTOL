#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Command-line script for ITOL (http://itol.embl.de) batch access (data upload and download).
"""

import os
import sys
import tempfile
import argparse
from zipfile import ZipFile
import requests
import logging

formatter = '%(levelname)s %(asctime)s %(name)s %(message)s'
logging.basicConfig(level=logging.INFO, format=formatter, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('iTOL')
warn, info, error = logger.warning, logger.info, logger.error

UPLOAD_URL = "http://itol.embl.de/batch_uploader.cgi"
DOWNLOAD_URL = "http://itol.embl.de/batch_downloader.cgi"


def download(tid, fmt='pdf', outfile='', **kwargs):
    """
    Download (or export) a tree from ITOL server (batch download).

    :param tid: str, ITOL tree ID which will be exported.
    :param fmt: str, output file format, supported values are: svg, eps, pdf and png for graphical formats and
    newick, nexus and phyloxml for text formats.
    :param outfile: str, path of the output file.
    :param kwargs: optional parameters.
    """
    
    if tid:
        if not tid.isdigit():
            error('Invalid tid {}, argument tid accepts an ITOL tree ID.'.format(tid))
            sys.exit(1)
    else:
        error('No tid provided, please proved a tid (tree ID) for downloading.')
        sys.exit(1)
    
    if isinstance(fmt, str):
        fmt = fmt.lower()
        formats = ['svg', 'eps', 'pdf', 'png', 'newick', 'nexus', 'phyloxml']
        if fmt not in formats:
            error("Invalid format. Supported formats: \n\t{}.".format(', '.join(formats)))
            sys.exit(1)
    else:
        error('Invalid output format, argument fmt accepts a string representing output format.')
        sys.exit(1)
    
    args = kwargs
    args['tree'] = tid
    args['format'] = fmt
    
    respond = requests.get(DOWNLOAD_URL, params=args)
    msg = respond.text
    code = msg.rstrip().split(':')[0]
    if code == 'ERROR':
        error('Tree download failed due to the following reason:\n\t{}'.format(msg))
        sys.exit(1)
    else:
        outfile = outfile if outfile else 'iTOL.download.{}'.format(fmt)
        try:
            with open(outfile, 'wb') as out:
                out.write(respond.content)
            info('Tree download successfully and data has been saved to:\n\t{}'.format(os.path.abspath(outfile)))
        except IOError:
            error('Save tree to file {} failed, location may not writable.'.format(outfile))


if __name__ == '__main__':
    des = 'Tool for downloading data (batch access) from ITOL (http://itol.embl.de).'
    epilog = """If no outfile provided, the output will be saved in current work directory and named iTOL.download.[
    format]. All optional parameters not listed above can also be used by add a '-' prefix before the name of the
    parameter, all available parameters can be found inside the ITOL help page.
    """
    
    parse = argparse.ArgumentParser(description=des, prog='itol-download', usage='%(prog)s TREEID [OPTIONS]',
                                    epilog=epilog)
    
    parse.add_argument('TREEID', help='Tree ID assigned by ITOL when you upload data.')
    parse.add_argument('-f', help='Output file format, default: pdf. '
                                  'Graphical formats: svg, eps, pdf and png. '
                                  'Text formats: newick, nexus and phyloxml.', default='pdf')
    parse.add_argument('-o', help='Path of the output file.')

    args, unknown = parse.parse_known_args()

    tid, fmt, outfile = args.TREEID, args.f, args.o
    
    kwargs = {}
    for i, item in enumerate(unknown):
        if item.startswith('-'):
            try:
                kwargs[item[1:]] = unknown[i + 1]
            except IndexError:
                error('No value provided to optional parameter {}.'.format(item[1:]))
            except KeyError:
                error('Invalid optional parameter {} provided.'.format(item[1:]))
    download(tid, fmt=fmt, outfile=outfile, **kwargs)
