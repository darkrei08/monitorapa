#!/usr/bin/env -S python3 -u

# This file is part of MonitoraPA
#
# Copyright (C) 2022 Giacomo Tesio <giacomo@tesio.it>
# Copyright (C) 2022 Leonardo Canello <leonardocanello@protonmail.com>
#
# MonitoraPA is a hack. You can use it according to the terms and
# conditions of the Hacking License (see LICENSE.txt)

import sys
sys.path.insert(0, '.') # NOTA: da eseguire dalla root del repository git

from lib import check

from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
import time
from datetime import datetime
import os
import os.path
import psutil
import tempfile

jsChecks = {}

jsFramework = """

function monitoraPAClick(element){
    window.monitoraPAClickPending = true;
    window.setTimeout(function(){
        element.click();
    }, 2000);
    window.setTimeout(function(){
        window.monitoraPAClickPending = false;
    }, 6000);
}

window.monitoraPACache = {}
function monitoraPADownloadResource(uri){
    if(Object.hasOwn(window.monitoraPACache, uri)){
        return window.monitoraPACache[uri];
    }
    window.monitoraPACache[uri] = '';
    var req = new XMLHttpRequest();
    req.open("GET", uri, false);
    req.onreadystatechange = function(){
        if (req.readyState === 4) {
            var content = req.responseText;
            window.monitoraPACache[uri] = content;
        }
    }
    req.send();
    return window.monitoraPACache[uri];
}


function runMonitoraPACheck(results, name, check){
    var issues;

    if(window.monitoraPAUnloading == true || window.monitoraPAClickPending == true){
        // skip check since a previous check caused a navigation
        return;
    }
    
    try {
        issues = check();
        results[name] = {
            'completed': true,
            'issues': issues
        }
    } catch(e) {
        issues = "runMonitoraPACheck: " + e.name + ": " + e.message;
        results[name] = {
            'completed': false,
            'issues': issues
        }
    }
}
"""

singleJSCheck = """
runMonitoraPACheck(monitoraPAResults, '%s', function(){
%s
});
"""

runAllJSChecks = """
function runAllJSChecks(){
debugger;
    var monitoraPAResults = {};
    window.monitoraPAResults = monitoraPAResults;

%s
    
    return window.monitoraPAResults;
}
"""

class BrowserNeedRestartException(Exception):
    pass

def usage():
    print("""
./cli/check/browsing.py out/$SOURCE/$DATE/dataset.tsv

Where:
- $SOURCE is a folder dedicated to a particular data source
- $DATE is the data source creation date in ISO 8601 format (eg 2022-02-28)
""")
    sys.exit(-1)


def waitUntilPageLoaded(browser, period=2):
    
    readyState = False
    
    while not readyState:
        time.sleep(period)
        readyState = browser.execute_script('return document.readyState == "complete" && !window.monitoraPAUnloading && !window.monitoraPAClickPending;')


def openBrowser(cacheDir):
    
    op = webdriver.ChromeOptions()
    op.add_argument('--user-data-dir='+cacheDir)
    op.add_argument('--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"')
    op.add_argument('--headless')
    op.add_argument('--incognito')
    op.add_argument('--disable-web-security')
    op.add_argument('--no-sandbox')
    op.add_argument('--disable-extensions')
    op.add_argument('--dns-prefetch-disable')
    op.add_argument('--disable-gpu')
    op.add_argument('--ignore-certificate-errors')
    op.add_argument('--ignore-ssl-errors')
    op.add_argument('enable-features=NetworkServiceInProcess')
    op.add_argument('disable-features=NetworkService')
    op.add_argument('--window-size=1920,1080')
    op.add_argument('--aggressive-cache-discard')
    op.add_argument('--disable-cache')
    op.add_argument('--disable-application-cache')
    op.add_argument('--disable-offline-load-stale-cache')
    op.add_argument('--disk-cache-size=0')
    op.add_experimental_option("excludeSwitches", ["enable-automation"])
    op.add_experimental_option('useAutomationExtension', False)
    op.add_argument('--disable-blink-features=AutomationControlled')

    browser = webdriver.Chrome('chromedriver', options=op)
    browser.set_page_load_timeout(90)
    
    browser.get('about:blank')
    
    return browser
    
def browseTo(browser, url):
    # we are in incognito mode: each new tab get a clean state for cheap
    
    while len(browser.window_handles) > 1:
        browser.switch_to.window(browser.window_handles[-1])
        browser.delete_all_cookies()
        browser.close()
    browser.switch_to.window(browser.window_handles[0])
    browser.get('about:blank')
    browser.execute_script("window.open('');")
    browser.switch_to.window(browser.window_handles[-1])
    try:
        browser.get(url)
    except TimeoutException:
        if len(browser.title) > 1:
            pass # after 90 something has been loaded anyway
        else:
            raise
    except WebDriverException as err:
        if url.startswith('http://') and ('net::ERR_CONNECTION_REFUSED' in err.msg or 'net::ERR_CONNECTION_TIMED_OUT' in err.msg):
            browseTo(browser, url.replace('http://', 'https://'))
            return
        else:
            raise
    browser.execute_script("window.addEventListener('beforeunload', e => { window.monitoraPAUnloading = true; });")

def runChecks(automatism, browser):
    url = automatism.address
    results = {}

    try:
        browseTo(browser, url)

        while len(results) != len(jsChecks):
            waitUntilPageLoaded(browser)
            
            script = jsFramework;
        
            allChecks = ""
            for js in jsChecks:
                if not (js in results): 
                    checkCode = jsChecks[js]['script']
                    allChecks += singleJSCheck % (js, checkCode)

            script += runAllJSChecks % allChecks
            script += "return runAllJSChecks();";
        
            newResults = browser.execute_script(script)
            #print(newResults)
            for js in newResults:
                results[js] = newResults[js]
        
        completionTime = str(datetime.now())
        for js in jsChecks:
            execution = check.Execution(automatism)
            issues = results[js]['issues']
            if results[js]['completed']:
                execution.complete(issues, completionTime)
            else:
                execution.interrupt(issues, completionTime)
            print("execution of %s:" % js, str(execution))
            jsChecks[js]['output'].write(str(execution)+'\n')

    except WebDriverException as err:
        print("WebDriverException of type %s occurred" % err.__class__.__name__, err.msg)
            
        # un check ha causato una eccezione: 
        # - registro i risultati raccolti
        # - registro l'eccezione su tutti i check che non ho potuto eseguire
        failTime = str(datetime.now())
        for js in jsChecks:
            execution = check.Execution(automatism)
            if js in results:
                issues = results[js]['issues']
                if results[js]['completed']:
                    execution.complete(issues, failTime)
                else:
                    execution.interrupt(issues, failTime)
            else:
                issues = "%s: %s" % (err.__class__.__name__, err.msg)
                execution.interrupt(issues)
            jsChecks[js]['output'].write(str(execution)+'\n')
            print("execution of %s:" % js, str(execution))

        if err.__class__.__name__ == 'TimeoutException' and 'receiving message from renderer' in err.msg:
            raise BrowserNeedRestartException
        if 'invalid session id' in err.msg:
            raise BrowserNeedRestartException

    #time.sleep(100000)

def restartBrowser(browser, cacheDir):
    print('restarting Browser: pid %d, dataDir %s' % (browser.service.process.pid, cacheDir))
    process = psutil.Process(browser.service.process.pid)
    tokill = process.children(recursive=True)
    tokill.append(process)
    browser.quit()
    for p in tokill:
        try:
            p.kill()
        except psutil.NoSuchProcess:
            pass
    browser = None
    time.sleep(5)
    return openBrowser(cacheDir)
    

def loadChecks(dataset, checksToRun):
    files = os.listdir('./cli/check/browsing/')
    files = sorted(files)
    for jsFile in files:
        jsFilePath = './cli/check/browsing/%s' % jsFile
        #print("jsFilePath %s" % jsFilePath)
        if os.path.isfile(jsFilePath) and jsFile.endswith('.js'):
            js = ""
            with open(jsFilePath, "r") as f:
                js = f.read()
            outputFile = check.outputFileName(dataset, 'browsing', jsFile.replace('.js', '.tsv'))
            directory = os.path.dirname(outputFile)
            #print("mkdir %s", directory)
            os.makedirs(directory, 0o755, True)
            checksToRun[jsFile] = {
                'script': js,
                'output': open(outputFile, "w", buffering=1)
            }

def browserReallyNeedARestart(browser):
    try:
        browseTo(browser, 'https://monitora-pa.it/tools/ping.html')
    except:
        return True
    return False

def main(argv):
    if len(sys.argv) != 2:
        usage()

    dataset = sys.argv[1]

    if not os.path.isfile(dataset):
        print(f"input dataset not found {dataset}");
        usage()

    cacheDirsContainer = os.path.dirname(check.outputFileName(dataset, 'browsing.caches', 'tmp.tsv'))
    os.makedirs(cacheDirsContainer, 0o755, True)
    cacheDir = tempfile.mkdtemp(prefix='cache-%d-' % os.getpid(), dir=cacheDirsContainer)

    loadChecks(dataset, jsChecks)
    browser = openBrowser(cacheDir)

    count = 0
    try:
        with open(dataset, 'r') as inf:
            for line in inf:
                automatism = check.parseInput(line)
                if automatism.type != 'Web':
                    continue

                print()
                print(count, automatism);
                
                try:
                    runChecks(automatism, browser)
                except BrowserNeedRestartException:
                    if browserReallyNeedARestart(browser):
                        browser = restartBrowser(browser, cacheDir)
                    
                if count % 500 == 499:
                    browser = restartBrowser(browser, cacheDir)
                count += 1
    except (KeyboardInterrupt):
        print("Interrupted at %s" % count)

    browser.quit()


if __name__ == "__main__":
    main(sys.argv)
