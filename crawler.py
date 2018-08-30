#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import ( division, absolute_import, print_function, unicode_literals )
from builtins import open

from inscrawler import InsCrawler
import sys
import argparse
import json
import pandas as pd
from io import open
import operator

import sys, os, tempfile, logging

if sys.version_info >= (3,):
    import urllib.request as urllib2
    import urllib.parse as urlparse
else:
    import urllib2
    import urlparse

def download_file(url, dest=None, filename=None):
    """ 
    Download and save a file specified by url to dest directory,
    """
    try: 
        u = urllib2.urlopen(url)
    except urllib2.URLError as e:
        print('{} is expired'.format(filename))
        pass
    else:
        scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
        #filename = os.path.basename(path)
        if not filename:
            filename = 'downloaded.file'
        if dest:
            filename = os.path.join(dest, filename)

        with open(filename, 'wb') as f:
            meta = u.info()
            meta_func = meta.getheaders if hasattr(meta, 'getheaders') else meta.get_all
            meta_length = meta_func("Content-Length")
            file_size = None
            if meta_length:
                file_size = int(meta_length[0])
            print("Downloading: {0} Bytes: {1}".format(url, file_size))

            file_size_dl = 0
            block_sz = 8192
            while True:
                buffer = u.read(block_sz)
                if not buffer:
                    break

                file_size_dl += len(buffer)
                f.write(buffer)

                status = "{0:16}".format(file_size_dl)
                if file_size:
                    status += "   [{0:6.2f}%]".format(file_size_dl * 100 / file_size)
                status += chr(13)
                print(status, end="")
            print()

    return filename


def usage():
    return '''
        python crawler.py posts -u cal_foodie -n 100 -o ./output
        python crawler.py posts_full -u cal_foodie -n 100 -o ./output
        python crawler.py profile -u cal_foodie -o ./output
        python crawler.py hashtag -t taiwan -o ./output

        The default number for fetching posts via hashtag is 100.
    '''


def get_posts_by_user(username, number, detail, debug):
    ins_crawler = InsCrawler(has_screen=debug)
    return ins_crawler.get_user_posts(username, number, detail)


def get_profile(username):
    ins_crawler = InsCrawler()
    return ins_crawler.get_user_profile(username)


def get_posts_by_hashtag(tag, number):
    ins_crawler = InsCrawler()
    return ins_crawler.get_latest_posts_by_tag(tag, number)


def arg_required(args, fields=[]):
    for field in fields:
        if not getattr(args, field):
            parser.print_help()
            sys.exit()


def download_photo(data, filepath, tag):
    out = json.dumps(data, ensure_ascii=False)
    df = pd.read_json(out)

    df['file_name'] = (df['img_url']
                        .str.rsplit('/', n=1, expand=True)
                        .iloc[:, 1]
                      )
    directory = os.path.join(filepath, tag)
    if not os.path.exists(directory):
        os.makedirs(directory)

    for i in range(len(df)):
        download_file(df['img_url'][i], dest=directory, filename=df['file_name'][i])
    
def output(data, filepath):
    out = json.dumps(data, ensure_ascii=False)
    if filepath:
        with open(filepath, 'w') as f:
            f.write(out)
    else:
        print(out)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Instagram Crawler',
                                     usage=usage())
    parser.add_argument('mode',
                        help='options: [posts, posts_full, profile, hashtag, photo-hashtag]')
    parser.add_argument('-n', '--number',
                        type=int,
                        help='number of returned posts')
    parser.add_argument('-u', '--username',
                        help='instagram\'s username')
    parser.add_argument('-t', '--tag',
                        help='instagram\'s tag name')
    parser.add_argument('-o', '--output', help='output file name(json format)')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.mode in ['posts', 'posts_full']:
        arg_required('username')
        output(
            get_posts_by_user(
                args.username,
                args.number,
                args.mode == 'posts_full',
                args.debug
            ),
            args.output)
    elif args.mode == 'profile':
        arg_required('username')
        output(get_profile(args.username), args.output)
    elif args.mode == 'photo-hashtag':
        arg_required('tag')
        download_photo(
            get_posts_by_hashtag(args.tag, args.number or 100), args.output, args.tag)
    elif args.mode == 'hashtag':
        arg_required('tag')
        output(
            get_posts_by_hashtag(args.tag, args.number or 100), args.output)
    else:
        usage()
