#!/usr/bin/env -S python3 -u

# This file is part of MonitoraPA
#
# Copyright (C) 2022 Giacomo Tesio <giacomo@tesio.it>
# Copyright (C) 2022 Leonardo Canello <leonardocanello@protonmail.com>
# Copyright (C) 2022 Pietro Biase <pietro@pietrobiase.it>
#
# MonitoraPA is a hack. You can use it according to the terms and
# conditions of the Hacking License (see LICENSE.txt)


import sys
sys.path.insert(0, '.') # NOTA: da eseguire dalla root del repository git

from lib import commons, check

import time
from datetime import datetime
import os
import os.path
import psutil
import shutil
import tempfile
import requests

# Timeout for checking website
TimeoutValue = 10	# in seconds

# value written in tsv as result
HTTPS_OK = 'HTTPS-ok'
HTTP_OK = 'HTTP-only'
HTTPS_HTTP_NOK = 'HTTPS_HTTP_nok'


def usage():
    print("""
./cli/check/https.py out/$SOURCE/$DATE/dataset.tsv

Where:
- $SOURCE is a folder dedicated to a particular data source
- $DATE is the data source creation date in ISO 8601 format (eg 2022-02-28)
""")
    sys.exit(-1)

def check_url(url):
    try:
        request_response = requests.head(url, timeout=TimeoutValue, allow_redirects=True)
        status_code = request_response.status_code
        print ("  Status code: %s" % status_code)
        if status_code == 200:
            return True, status_code
        else:
            return False, status_code
    except:
    	return False, 0


def runCheckProtocol(url):
    
    url_https = 'https://' + url.split('//')[1]
    esito, status = check_url(url_https)
    
    if esito == True:
        print("  Nice, you can load %s with https" % url_https)
        text = HTTPS_OK+" ("+str(status)+")"
        return True, text

    else:
        print("  Oh no, %s does not load with https" % url_https)
        
        
    url_http = 'http://' + url.split('//')[1]
    esito, status = check_url(url_http)  
    if esito == True:
        print("  Nice, you can load %s with http" % url_http)
        text = HTTP_OK+" ("+str(status)+")"
        return True, text
        
    else:
        print("  Oh no, %s does not load with http" % url_http)
        text = HTTPS_HTTP_NOK+" ("+str(status)+")"
        return False, text


def run(dataset):
    outputFile = check.outputFileName(dataset, 'https.tsv')
    directory = os.path.dirname(outputFile)
    print("mkdir %s", directory)
    os.makedirs(directory, 0o755, True)

    count = 0
    try:
        with open(dataset, 'r') as inf, open(outputFile, "w", buffering=1) as outf:
            for line in inf:
                automatism = check.parseInput(line)
                if automatism.type != 'Web':
                    continue

                print()
                print(count, automatism);
                
                completed, issues = runCheckProtocol(automatism.address)
                
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


def main(argv):
    if len(sys.argv) != 2:
        usage()

    dataset = sys.argv[1]

    if not os.path.isfile(dataset):
        print(f"input dataset not found: {dataset}");
        usage()
             
    run(dataset)


if __name__ == "__main__":
    main(sys.argv)
