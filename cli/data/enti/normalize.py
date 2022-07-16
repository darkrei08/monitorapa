#!/usr/bin/env python3

# This file is part of MonitoraPA
#
# Copyright (C) 2022 Giacomo Tesio <giacomo@tesio.it>
#
# MonitoraPA is a hack. You can use it according to the terms and
# conditions of the Hacking License (see LICENSE.txt)

import sys
import os.path

def usage():
    print("""
./cli/data/enti/normalize.py ./out/enti/YYYY-MM-YY/enti.tsv

Will create ./out/enti/YYYY-MM-YY/dataset.tsv
""")
    sys.exit(-1)

def outputFileName(inputFileName):
    return os.path.join(os.path.dirname(inputFileName), "dataset.tsv")

def normalizeUrl(url):
    if len(url) < 4 or url.startswith('about'):
        return ""
    if not url.startswith('http'):
        return 'http://' + url
    return url
    
def main(argv):
    if len(argv) != 2:
        usage()
    try:
        with open(argv[1], "r") as inf, open(outputFileName(argv[1]), mode="w") as outf:
            i = 0
            for line in inf:
                if i == 0:
                    i += 1 # skip column headers
                    continue
                line = line.strip(" \n")
                fields = line.split('\t');
                outID = fields[1]
                webSite = normalizeUrl(fields[29])
                if webSite != '':
                    outf.write('\t'.join([outID, 'Web', webSite]) + '\n')
                outf.write('\t'.join([outID, 'Email', fields[19]]) + '\n')                
    except IOError as ioe:
        print(f"[ ERR ]: IOError: {ioe}")
        usage()

if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        print("[ ERR ] KeyboardInterrupt, aborting")
        sys.exit(1)
