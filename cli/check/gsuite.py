#!/usr/bin/env -S python3 -u

# This file is part of MonitoraPA
#
# Copyright (C) 2022 Giacomo Tesio <giacomo@tesio.it>
#
# MonitoraPA is a hack. You can use it according to the terms and
# conditions of the Hacking License (see LICENSE.txt)


import sys
sys.path.insert(0, '.') # NOTA: da eseguire dalla root del repository git

from lib import search, check
from urllib.parse import urlparse
import dns.resolver
import time
import os.path

textMarkers = [
    'g-suite',
    '"g suite"',
    'gsuite'
    '"google classroom"',
    'workspace'
]
searchQuery = " ".join(textMarkers)

def checkWebSite(automatism: check.Input) -> search.SearchResult:
    results = search.duckduckgo(searchQuery, automatism.address)
    if len(results) > 0:
        for result in results:
            # cerco il risultato migliore
            for marker in textMarkers:
                if marker in result.title.lower() or marker in result.details.lower():
                    return result
        # se non ne trovo uno migliore, ritorno il primo
        return results[0]
    return None


def http2mx(target: str) -> str:
    target = target.replace("https://", "")
    target = target.replace("http://", "")
    if target.startswith("www."):
        target = target[4:]
    return target
    
mxMarkers = [
    ".google.com.",
    ".googlemail.com."
]
def checkMX(automatism: check.Input) -> str:
    target = http2mx(automatism.address)
    try:
        answers = dns.resolver.resolve(target, 'MX')
        for rdata in answers:
            exchange = rdata.exchange.to_text().lower()
            for marker in mxMarkers:
                if marker in exchange:
                    return str(rdata.preference) + " " + exchange
    except KeyboardInterrupt:
        raise
    except:
        pass #
    return None

def usage():
    print("""
./cli/check/gsuite.py out/$SOURCE/$DATE/dataset.tsv

Identifica i siti che propongono strumenti di Google per la Scuola

Where:
- $SOURCE is a folder dedicated to a particular data source
- $DATE is the data source creation date in ISO 8601 format (eg 2022-02-28)
""")
    sys.exit(-1)

def main(argv):
    if len(argv) != 2:
        usage()

    dataset = argv[1]

    if not os.path.isfile(dataset):
        print("not found: " + dataset);
        usage()
             
    outputFile = check.outputFileName(dataset, 'https.tsv')
    os.makedirs(os.path.dirname(outputFile), 0o755, True)
    
    count = 0
    try:
        with open(dataset, 'r') as inf, open(outputFile, "w", buffering=1) as outf:
            for line in inf:
                automatism = check.parseInput(line)
                if automatism.type != 'Web':
                    continue
                
                
                tmp = urlparse(automatism.address)
                automatism.address = tmp.hostname

                print(automatism.address)
                if automatism.address == None:
                    continue

                execution = check.Execution(automatism)
                try:
                    websiteIssues = checkWebSite(automatism)
                    mxIssues = checkMX(automatism)
                    
                    if websiteIssues == None and mxIssues == None:
                        execution.complete()
                    else:
                        result = {
                            'web': str(websiteIssues),
                            'mx': str(mxIssues)
                        }
                        execution.complete(str(result))
                except Exception as e:
                    execution.interrupt(str(e))
                outf.write(str(execution)+'\n')

                print(count, execution);

                time.sleep(10)
                count += 1
                
    except (KeyboardInterrupt):
        print("Interrupted at %s" % count)

if __name__ == "__main__":
    main(sys.argv)
