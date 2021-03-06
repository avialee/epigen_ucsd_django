#!/usr/bin/env python
# Time-stamp: <2019-01-23 10:05:21>

import os
import sys
import django
import io

os.chdir("../")
basedir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(basedir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "epigen_ucsd_django.settings")
django.setup()
from nextseq_app.models import Barcode


def getArgs():
    import argparse
    parser = argparse.ArgumentParser(description='Import barcodes script.')
    parser.add_argument('-b', '--barcode_file', dest='barcode_file',
                        help='input barcode file  (csv format, basedir is ../data/nextseq_app/barcodes)')
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    return args.barcode_file


def main():
    fl = basedir+'/data/nextseq_app/barcodes/'+getArgs()
    with io.open(fl, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    indexes = {l.replace(u'\ufeff', '').split(',')[0]: l.replace(
        u'\ufeff', '').split(',')[1]for l in lines}
    for k, v in indexes.items():
        print(k+':'+v)
        obj, created = Barcode.objects.get_or_create(indexid=k, indexseq=v,kit='BK')


if __name__ == '__main__':
    main()
