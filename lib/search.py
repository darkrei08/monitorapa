# This file is part of MonitoraPA
#
# Copyright (C) 2022 Giacomo Tesio <giacomo@tesio.it>
#
# MonitoraPA is a hack. You can use it according to the terms and
# conditions of the Hacking License (see LICENSE.txt)

import subprocess
import json

class SearchResult:
    uri: str
    title: str
    details: str
    def __init__(self, uri: str, title: str, details: str):
        self.uri = uri
        self.title = title
        self.details = details
    def __str__(self):
        d = {
            'uri': self.uri,
            'title': self.title,
            'details': self.details
        }
        return json.dumps(d)
    def __repr__(self):
        return str(self)

def duckduckgo(search:str, website:str = None) -> [SearchResult]:
    if search == '':
        raise ValueError("empty search")

    cmd = [
        "ddgr", 
        "--noua", 
        "--json"
    ]
    
    cmd += ["--reg", "it-it"]

    if website != None:
        cmd += ["--site", website.replace("http://", "").replace("https://","")]

    cmd.append(search)

    #print (cmd)

    results = []
    search = subprocess.run(cmd, capture_output=True, text=True)
    resultsList = json.loads(search.stdout)
    for item in resultsList:
        result = SearchResult(item['url'], item['title'], item['abstract'])
        results.append(result)
    return results
    
