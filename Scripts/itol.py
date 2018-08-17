#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Command-line script for `ITOL <http://itol.embl.de>`_ batch access (data upload and download).
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
logger = logging.getLogger('iTOL')
warn, info, error = logger.warning, logger.info, logger.error

UPLOAD_URL = "http://itol.embl.de/batch_uploader.cgi"
DOWNLOAD_URL = "http://itol.embl.de/batch_downloader.cgi"


def upload(tfile='', zfile='', tn='', uid='', pn='', td='', folder=False):
    """
    Zip tree file (regular text file in Newick, Nexus, PhyloXML or Jplace format) into a ZIP file or directly upload
    a zip file to ITOL server (batch upload).

    :param tfile: str, path of a tree file, in one of the supported formats (Newick, Nexus, PhyloXML or Jplace).
    :param zfile: str, path of a ZIP archive contains the tree and all other dataset and annotation files.
    :param tn: str, if not provided, the basename of the tree file will be used instead.
    :param uid: str, your upload ID, which is generated when you enable batch uploading in your account. If an
    uid is not provided, the tree will not be associated with any account, and will be deleted after 30 days.
    :param pn: str, required if ID is specified, case sensitive, and should be unique in your account.
    :param td: str, description of your tree, ignored if ID is not specified.
    :param folder, bool, whether zip all text files (must have .txt extension) in the same directory with tree file. If
    set to True, zip all text files in the folder, otherwise only zip and upload the tree file.

    Note: Either a treefile (regular text file) or a zipfile is needed. The name of the tree file will be automatically
    renamed to have the extension '.tree' or '.tree.txt', if necessary. The text file will be zipped into a temporary
    ZIP file for uploading and the temporary ZIP file will be deleted upon the process exit. If a ZIP file is provided,
    however, users are responsible for renaming the name of the tree file and make sure the file have the extension
    '.tree' or '.tree.txt'. The user provided ZIP file will not be modified or deleted.
    
    .. Note:
        Unlike use the ``TOL`` class, which will zip all text file inside the work directory if folder is set to True.
        In this command line tool, set the argument ``folder`` or ``-f`` flag will zip all text files (must have the
        extension .txt) in the same directory with tree file into a temporary zip file.
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
                info('Finding and zipping all text files in directory {} into a ZIP file.'.format(dn))
                files = [f for f in os.listdir(dn) if f != basename and f.endswith('.txt')]
                if files:
                    info('Zipping {} text files into the ZIP file.'.format(len(files)))
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


def download(tid, fmt='pdf', outfile='', **kwargs):
    """
    Download (or export) a tree from ITOL server (batch download).

    :param tid: str, ITOL tree ID or URL which will be exported.
    :param fmt: str, output file format, supported values are: svg, eps, pdf and png for graphical formats and
    newick, nexus and phyloxml for text formats.
    :param outfile: str, path of the output file.
    :param kwargs: optional parameters.
    """
    
    if tid:
        if tid.startswith('http'):
            treeID = tid.split('/')[-1]
        elif tid.isdigit():
            treeID = tid
        else:
            error('Invalid tid {}, argument tid accepts an ITOL tree ID or URL.'.format(tid))
            sys.exit(1)
    else:
        error('No tid provided, please proved a tid (tree ID or URL) for downloading.')
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
    args['tree'] = treeID
    args['format'] = fmt

    respond = requests.get(DOWNLOAD_URL, params=args)
    msg = respond.text
    code = msg.rstrip().split(':')[0]
    if code == 'ERROR':
        error('Tree download failed due to the following reason:\n\t{}'.format(msg))
    elif code.startswith('Invalid'):
        error('Download failed due to the following reason:\n\t{}'.format(msg))
    else:
        outfile = outfile if outfile else 'iTOL.download.{}'.format(fmt)
        try:
            with open(outfile, 'wb') as out:
                out.write(respond.content)
            info('Tree download successfully and data has been saved to:\n\t{}'.format(os.path.abspath(outfile)))
        except IOError:
            error('Save tree to file {} failed, location may not writable.'.format(outfile))
    

if __name__ == '__main__':
    des = 'Command line tool for ITOL (http://itol.embl.de) bach access.'
    epilog = """Either a tree file (regular text file), a ZIP file, a tree ID or tree URL assigned by ITOL can be
    passed as DATA argument. It will automatically check the type of the data. If a regular text file is provided,
    it assumes the text file is a tree file in Newick, Nexus, PhyloXML or Jplace format. The name of the tree file
    will be automatically renamed to have the extension '.tree' or '.tree.txt', if necessary. The text file will be
    zipped into a temporary ZIP file for uploading and the temporary ZIP file will be deleted upon the process exit.
    If a ZIP file is provided, however, users are responsible for renaming the name of the tree file and make sure
    the file have the extension '.tree' or '.tree.txt'. The user provided ZIP file will not be modified or deleted.
    In case a treefile is in use, the '-f' flag will zip and upload all text files (must have .txt extension) saved
    along with the tree file to ITOL. If a tree ID or URL is provided, it will download data from the ITOL server.
    If no outfile provided, the output will be saved in current work directory and named iTOL.download.[format]. All
    optional parameters for managing the behavior of downloading can also be used by add a '--' prefix before the name
    of the parameter (lower case), and followed by the value of the parameter (the parameter and the value need to be
    separated by a space), all available parameters can be found inside the ITOL help page. Argument not related
    to upload or download will be ignored, i.e. when you are uploading data, the `-o` option for output of the download
    will be ignored, while you are downloading, the '-n' option for a tree name will also be ignored.
    """

    parse = argparse.ArgumentParser(description=des, prog='itol.py', usage='%(prog)s DATA [OPTIONS]', epilog=epilog)

    parse.add_argument('DATA', help='A tree file name, a ZIP file name, a tree ID or URL.')
    parse.add_argument('-i', help='Your upload ID (ID for batch uploading).', metavar='uploadID')
    parse.add_argument('-n', help='The name you assign to the tree.', metavar='treeName')
    parse.add_argument('-p', help='Project name, required if uploadID is set.', metavar='projectName')
    parse.add_argument('-d', help='Description of your tree.', metavar='treeDescription')
    parse.add_argument('-f', help='Output file format, default: pdf. Graphical formats: svg, eps, pdf and png; '
                                  'text formats: newick, nexus and phyloxml', default='pdf')
    parse.add_argument('-o', help='Path of the output file.')
    parse.add_argument('-a', help='Force zip all text files along with the tree file.', action='store_true')

    args, unknown = parse.parse_known_args()
    data, uid, tn, pn, td, fmt, outfile, folder = args.DATA, args.i, args.n, args.p, args.d, args.f, args.o, args.a

    kwargs = {}
    for i, item in enumerate(unknown):
        if item.startswith('--'):
            try:
                kwargs[item[2:]] = unknown[i + 1]
            except IndexError:
                error('No value provided to optional parameter {}.'.format(item[1:]))
            except KeyError:
                error('Invalid optional parameter {} provided.'.format(item[1:]))

    if data.isdigit():
        if os.path.isfile(data):
            tf, zf = (None, data) if is_zipfile(data) else (data, None)
            upload(tfile=tf, zfile=zf, tn=tn, uid=uid, pn=pn, td=td, folder=folder)
        else:
            download(data, fmt=fmt, outfile=outfile, **kwargs)
    elif data.startswith('http'):
        download(data, fmt=fmt, outfile=outfile, **kwargs)
    elif os.path.isfile(data):
        tf, zf = (None, data) if is_zipfile(data) else (data, None)
        upload(tfile=tf, zfile=zf, tn=tn, uid=uid, pn=pn, td=td, folder=folder)
    else:
        error('Invalid data {}, data accepts a tree file, a ZIP file, a tree ID or URL.')
