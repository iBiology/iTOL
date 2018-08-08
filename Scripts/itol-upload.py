#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Command-line script for uploading data (batch access) to ITOL (http://itol.embl.de) server.
"""

import os
import sys
import tempfile
import argparse
from zipfile import ZipFile, is_zipfile
import requests
import logging

formatter = '%(levelname)s %(asctime)s %(name)s %(message)s'
logging.basicConfig(level=logging.INFO, format=formatter, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('iTOL-UPLOAD')
warn, info, error = logger.warning, logger.info, logger.error

UPLOAD_URL = "http://itol.embl.de/batch_uploader.cgi"
DOWNLOAD_URL = "http://itol.embl.de/batch_downloader.cgi"


def upload(tfile='', zfile='', tn='', uid='', pn='', td='', folder=False):
    """
    Zip tree file (regular text file in Newick, Nexus, PhyloXML or Jplace format) into a ZIP file or directly upload
    a zip file to ITOL server (batch upload).

    :param tfile: str, filename of a tree file, in one of the supported formats (Newick, Nexus, PhyloXML or Jplace).
    :param zfile: str, a ZIP archive containing the tree and all other dataset and annotation files.
    :param tn: str, if not provided, the tree file name (basename without extension) will be used instead.
    :param uid: str, your upload ID, which is generated when you enable batch uploading in your account. If an
    uid is not provided, the tree will not be associated with any account, and will be deleted after 30 days.
    :param pn: str, required if ID is specified, case sensitive, and should be unique in your account.
    :param td: str, description of your tree, ignored if ID is not specified.
    :param folder, bool, whether zip all sister text files (must have .txt extension) saved along with the tree file. If
    set to True, zip all text files in the folder, otherwise only zip and upload the tree file.

    Note: Either a treefile (regular text file) or a zipfile is needed. The name of the tree file will be automatically
    renamed to have the extension '.tree' or '.tree.txt', if necessary. The text file will be zipped into a temporary
    ZIP file for uploading and the temporary ZIP file will be deleted upon the process exit. If a ZIP file is provided,
    however, users are responsible for renaming the name of the tree file and make sure the file have the extension
    '.tree' or '.tree.txt'. The user provided ZIP file will not be modified or deleted.
    """
    
    if tfile and os.path.isfile(tfile):
        info('Zip and upload tree file {} to ITOL server.'.format(tfile))
        # Although .mktemp() is UNSAFE to use, use .mkstemp() will lead to the temp file CANNOT be deleted due to
        # PermissionError: [WinError 32] The process can not access to the file because is used by other process
        # on Windows platform, still no clue why this happened.
        zfile, name = tempfile.mktemp(suffix='.zip', prefix='iTOL.tree.'), 'iTOL.tree.txt'

        with ZipFile(zfile, 'w') as zf:
            if folder:
                dn, basename = os.path.dirname(os.path.abspath(tfile)), os.path.basename(tfile)
                files = [f for f in os.listdir(dn) if f != basename and f.endswith('.txt')]
                if files:
                    for fn in files:
                        zf.write(os.path.join(dn, fn), arcname=fn)
            zf.write(tfile, arcname=name)
            
    elif zfile and os.path.isfile(zfile):
        info('Upload zipfile {} to ITOL server.'.format(zfile))
    else:
        error('Neither valid tfile nor valid zipfile was provided, upload aborted.')
        sys.exit(1)

    kwargs = {'treeName': tn if tn else os.path.basename(tfile or zfile)}
    if uid:
        kwargs['uploadID'] = uid
    else:
        warn('Warning!!! No uploadID was provided!')
        warn('The tree will not be associated with any account and will be deleted after 30 days!')
    if pn:
        kwargs['projectName'] = pn
    if td:
        kwargs['treeDescription'] = td
    
    respond = requests.post(UPLOAD_URL, data=kwargs, files={'zipFile': open(zfile, 'rb')})
    msg = respond.text
    
    if tfile and os.path.isfile(zfile):
        try:
            os.remove(zfile)
        except OSError as e:
            print(e)
            warn('Failed to delete temporary zip file {}, please try to manually delete it.'.format(zfile))

    if msg.startswith('SUCCESS'):
        code, treeID = msg.rstrip().split(': ')
        info('Upload successfully and you can access your tree using the following iTOL tree ID:\n\t{}'.format(treeID))
        
        url = 'https://itol.embl.de/tree/{}'.format(treeID)
        info('You can also view your tree in browser using the following URL: \n\t{}'.format(url))
    else:
        error('tree upload failed due to the following reason:\n\t{}'.format(msg))
        sys.exit(1)
    

if __name__ == '__main__':
    des = 'Tool for uploading a tree file (text file) or a ZIP file (batch access) to ITOL (http://itol.embl.de).'
    epilog = """Either a treefile (regular text file) or a zipfile is needed. It will automatically check the file
    type you provided. If a regular text file is provided, it assumes the text file is a tree file in Newick,
    Nexus, PhyloXML or Jplace format. The name of the tree file will be automatically renamed to have the extension
    '.tree' or '.tree.txt' if necessary. The text file will be zipped into a temporary ZIP file for uploading and the
    temporary ZIP file will be deleted upon the process exit. If a ZIP file is provided, however, users are
    responsible for renaming the name of the tree file and make sure the file have the extension '.tree' or
    '.tree.txt'. The user provided ZIP file will not be modified or deleted. In case a treefile is in use, the '-f'
    flag will zip and upload all text files (must have .txt extension) saved along with the tree file to ITOL.
    """

    parse = argparse.ArgumentParser(description=des, prog='itol-upload', usage='%(prog)s FILE [OPTIONS]', epilog=epilog)

    parse.add_argument('FILE', help='Path to a tree file (regular text file) or a ZIP file.')
    parse.add_argument('-i', help='Your upload ID (ID for batch uploading).', metavar='uploadID')
    parse.add_argument('-n', help='The name you given to the tree.', metavar='treeName')
    parse.add_argument('-p', help='Project name, required if uploadID is set.', metavar='projectName')
    parse.add_argument('-d', help='Description of your tree.', metavar='treeDescription')
    parse.add_argument('-f', help='Force zip all text files along with the tree file.', action='store_true')

    args = parse.parse_args()

    data, uid, tn, pn, td, folder = args.FILE, args.i, args.n, args.p, args.d, args.f

    if not os.path.isfile(data):
        error('Invalid file {}, it is not a file or does not exist.')
        sys.exit(1)

    tf, zf = (None, data) if is_zipfile(data) else (data, None)

    upload(tfile=tf, zfile=zf, tn=tn, uid=uid, pn=pn, td=td, folder=folder)
