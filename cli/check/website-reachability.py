#!/usr/bin/env python3

# This file is part of MonitoraPA
#
# Copyright (C) 2022 Giacomo Tesio <giacomo@tesio.it>
# Copyright (C) 2022 Leonardo Canello <leonardocanello@protonmail.com>
# Copyright (C) 2022 Emilie Rollandin <emilie@rollandin.it>
#
# MonitoraPA is a hack. You can use it according to the terms and
# conditions of the Hacking License (see LICENSE.txt)
import sys
sys.path.insert(0, '.') # NOTA: da eseguire dalla root del repository git

from lib import check

import time
from datetime import datetime
import os.path
import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
cafile = 'cacert.pem'
   
def usage():
    print("""
./cli/check/website-reachability.py out/$SOURCE/$DATE/dataset.tsv

Where:
- $SOURCE is a folder dedicated to a particular data source
- $DATE is the data source creation date in ISO 8601 format (eg 2022-02-28)
""")
    sys.exit(-1)

def checkUrl(url, timeout):
    try:
        response = requests.get(url, timeout=timeout, headers=headers, verify=False)
    except requests.exceptions.HTTPError:
        return False, "Http Error"
    except requests.exceptions.SSLError:
        return False, "SSL Error"
    except requests.exceptions.ConnectionError:
        if url.startswith('http://'):
            return checkUrl(url.replace('http://', 'https://'), 5)
        return False, "Error Connecting"
    except requests.exceptions.Timeout:
        return False, "Timeout Error"
    except requests.exceptions.RequestException:
        return False, "Ops: Something Else"
    except requests.packages.urllib3.exceptions.LocationParseError:
        return False, "Url not valid"
    else:
        return True, response.url


def main(argv):
    if len(sys.argv) != 2:
        usage()

    dataset = sys.argv[1]

    if not os.path.isfile(dataset):
        print(f"input dataset not found: {dataset}");
        usage()

    outputFile = check.outputFileName(dataset, 'browsing', 'website-reachability.tsv')
    directory = os.path.dirname(outputFile)
    #print("mkdir %s", directory)
    os.makedirs(directory, 0o755, True)


    count = 0
    try:
        with open(dataset, 'r') as inf, open(outputFile, "w", buffering=1) as outf:
            for line in inf:
                automatism = check.parseInput(line)
                if automatism.type != 'Web':
                    continue

                print(count, automatism);
                completed, issues = checkUrl(automatism.address, 10)
                
                execution = check.Execution(automatism)
                if completed:
                    execution.complete(issues)
                else:
                    execution.interrupt(issues)
                print('\t', execution);
                outf.write(str(execution)+'\n')
                count += 1

    except (KeyboardInterrupt):
        print("Interrupted at %s" % count)

if __name__ == '__main__':
    main(sys.argv)
