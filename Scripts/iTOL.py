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
logging.basicConfig(level=logging.ERROR, format=formatter, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('iTOL')
warn, info, error = logger.warning, logger.info, logger.error

UPLOAD_URL = "http://itol.embl.de/batch_uploader.cgi"
DOWNLOAD_URL = "http://itol.embl.de/batch_downloader.cgi"


def upload(treefile='', zfile='', treename='', uploadID='', projectname='', treedescription=''):
    """
    Pack tree file and all notation files (text files ending in .txt) inside work directory into a zip file if necessary
    and upload the zip file to ITOL server (batch upload).

    :param treefile: str, filename of a tree file, in one of the supported formats (Newick, Nexus, PhyloXML or Jplace).
    :param zfile: str, a ZIP archive containing the tree and all other dataset and annotation files.
    :param treename: str, if not provided, the tree file name (basename without extension) will be used instead.
    :param uploadID: str, your upload ID, which is generated when you enable batch uploading in your account. If an
    uploadID is not provided, the tree will not be associated with any account, and will be deleted after 30 days.
    :param projectname: str, required if ID is specified, case sensitive, and should be unique in your account.
    :param treedescription: str, description of your tree, ignored if ID is not specified.

    Note: Either a treefile or a zipfile is needed, if both of them were provided, the zipfile will be ignored.
    If uploadID is not provided, the tree will not be associated with any account and will be deleted after 30 days.
    """
    
    args = {}
    if os.path.isfile(treefile):
        info('Zip and upload tree file {} to ITOL server.'.format(treefile))
        # zfile = os.path.join(wd, 'iTOL.tree.zip')
        zfile = tempfile.mkstemp(suffix='zip', prefix='iTOL.tree')
        name = 'tree.jplace' if treefile.endswith('.jplace') else 'iTOL.tree.txt'
        with ZipFile(zfile, 'w') as zf:
            zf.write(treefile, arcname=name)
    elif zfile:
        info('Upload zipfile {} to ITOL server.'.format(zfile))
    else:
        error('Neither treefile nor zipfile was provided, upload aborted.')
        sys.exit(1)
    
    args['treeName'] = treename if treename else os.path.basename(treefile or zfile)
    if uploadID:
        args['uploadID'] = uploadID
    if projectname:
        args['projectName'] = projectname
    if treedescription:
        args['treeDescription'] = treedescription
    
    if not args['uploadID']:
        warn('Warning!!! No ID was provided!')
        warn('The tree will not be associated with any account and will be deleted after 30 days!')
    
    respond = requests.post(UPLOAD_URL, data=args, files={'zipFile': open(zfile, 'rb')})
    msg = respond.text
    
    if treefile and os.path.isfile(zfile):
        try:
            os.remove(zfile)
        except OSError:
            warn('Failed to delete temporary zip file {}, please try to manually delete it.'.format(zfile))
    
    if msg.startswith('SUCCESS'):
        code, treeID = msg.split(': ')
        info('Tree upload successfully and you can access your tree using the following iTOL tree ID:')
        info('\t{}'.format(treeID))
        
        url = 'https://itol.embl.de/tree/{}'.format(treeID)
        info('You can also view your tree in browser using the following URL: \n\t{}'.format(url))
    else:
        error('Tree upload failed due to the following reason:\n\t{}'.format(info))
        sys.exit(1)
    

def download(treeID, format='pdf', outfile='', **kwargs):
    """
    Download (or export) a tree from ITOL server (batch download).

    :param treeID: str, ITOL tree ID which will be exported.
    :param format: str, output file format, supported values are: svg, eps, pdf and png for graphical formats and
    newick, nexus and phyloxml for text formats.
    :param outfile: str, path of the output file.
    :param kwargs: optional parameters.
    """
    
    if treeID:
        if not isinstance(treeID, str):
            error('Invalid treeID, argument treeID accepts a string pointing to a iTOL tree ID.')
            sys.exit(1)
    else:
        error('No treeID provided, please proved a treeID for downloading.')
        sys.exit(1)
    
    if isinstance(format, str):
        format = format.lower()
        formats = ['svg', 'eps', 'pdf', 'png', 'newick', 'nexus', 'phyloxml']
        if format not in formats:
            error("Invalid format. Supported formats: \n\t{}.".format(', '.join(formats)))
            sys.exit(1)
    else:
        error('Invalid output format, argument format accepts a string representing output format.')
        sys.exit(1)
    
    args = kwargs
    args['tree'] = treeID
    args['format'] = format
    
    respond = requests.get(DOWNLOAD_URL, params=args)
    info = respond.text
    code = info.split(':')[0]
    if code == 'ERROR':
        error('Tree download failed due to the following reason:\n\t{}'.format(info))
        sys.exit(1)
    else:
        outfile = outfile if outfile else 'iTOL.download.{}'.format(format)
        with open(outfile, 'wb') as out:
            out.write(respond.content)
        info('Tree download successfully and data has been saved to:\n\t{}'.format(outfile))


if __name__ == '__main__':
    des = 'A tool for ITOL (http://itol.embl.de) batch access (data upload and download).'
    epilog = """Under uploade mode, either a treefile or a zipfile is needed, if both of them were provided,
    the zipfile will be ignored. under download mode, if no outfile provided, the output will be saved in current
    work directory and named iTOL.download.[format]. All optional parameters not listed above can also be used by add
    '-' prefix before the name of the parameter, all available parameters can be found inside the ITOL help page.
    """
    parse = argparse.ArgumentParser(description=des, prog='iTOL', usage='%(prog)s MODE [OPTIONS]', epilog=epilog)
    
    parse.add_argument('mode', help='Mode of the batch access, either upload or download.')
    parse.add_argument('-treefile', help='filename of a tree file, in Newick, Nexus, PhyloXML or Jplace format.')
    parse.add_argument('-zipfile', help='A ZIP archive containing the tree and all other dataset and annotation files.')
    parse.add_argument('-treename', help='Name of the tree, if not provided, the tree filename will be used instead.')
    parse.add_argument('-uploadID', help='Your upload ID, generated when you enable batch uploading in your account.')
    parse.add_argument('-projectname', help='Required if uploadID is specified, and should be unique in your account.')
    parse.add_argument('-treedescription', help='Description of your tree, ignored if uploadID is not provided.')
    parse.add_argument('-treeID', help='ITOL tree ID which will be exported or downloaded.')
    parse.add_argument('-format', help='Output file format, default: pdf. '
                                       'Graphical formats: svg, eps, pdf and png. '
                                       'Text formats: newick, nexus and phyloxml.', default='pdf')
    parse.add_argument('-outfile', help='Path of the output file.')

    args, unknown = parse.parse_known_args()

    mode, treefile, zfile, tn, uploadID = args.mode, args.treefile, args.zipfile, args.treename, args.uploadID
    pn, tdes, treeID = args.projectname, args.treedescription, args.treeID
    fmt, outfile = args.format, args.outfile
    
    if mode == 'upload':
        upload(treefile=treefile, zfile=zfile, treename=tn, uploadID=uploadID, projectname=pn, treedescription=tdes)
    elif mode == 'download':
        kwargs = {}
        for i, item in enumerate(unknown):
            if item.startswith('-'):
                try:
                    kwargs[item[1:]] = unknown[i + 1]
                except IndexError:
                    error('No value provided to optional parameter {}.'.format(item[1:]))
                except KeyError:
                    error('Invalid optional parameter {} provided.'.format(item[1:]))
        download(treeID, format=fmt, outfile=outfile, **kwargs)
    else:
        error('Invalid batch access mode {}, model only accepts upload or download.'.format(mode))
