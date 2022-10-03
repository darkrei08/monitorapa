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
import signal
signal.signal(signal.SIGINT, signal.default_int_handler)

from lib import commons, check

import undetected_chromedriver as uc


import time
from datetime import datetime
import os
import os.path
import psutil
import shutil
import tempfile
import socket
from urllib.parse import urlparse

def usage():
    print("""
./cli/check/browsing.py out/$SOURCE/$DATE/dataset.tsv

Where:
- $SOURCE is a folder dedicated to a particular data source
- $DATE is the data source creation date in ISO 8601 format (eg 2022-02-28)
""")
    sys.exit(-1)

checksToRun = {}
networkLogs = []

def run(dataset):
    loadAllChecks(dataset, checksToRun)
    cacheDir = getCacheDir(dataset)
    browser = openBrowser(cacheDir)

    count = 0
    try:
        with open(dataset, 'r') as inf:
            for line in inf:
                count += 1
                
                #if count < 266:
                #    continue

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
                    
                #if count % 500 == 499:
                #    browser = restartBrowser(browser, cacheDir)
                count += 1
    except (KeyboardInterrupt):
        print("Interrupted at %s" % count)
    finally:
        browser.quit()
        time.sleep(5)
        shutil.rmtree(cacheDir, False)

## Python checks

GoogleFontsServers = [
    'fonts.googleapis.com',
    'fonts.gstatic.com',
    'themes.googleusercontent',
]
AzureServers = [
    '.accesscontrol.windows.net',
    '.graph.windows.net',
    '.onmicrosoft.com',
    '.azure-api.net',
    '.biztalk.windows.net',
    '.blob.core.windows.net',
    '.cloudapp.net',
    '.cloudapp.azure.com',
    '.azurecr.io',
    '.azurecontainer.io',
    '.vo.msecnd.net',
    '.cosmos.azure.com',
    '.documents.azure.com',
    '.file.core.windows.net',
    '.azurefd.net',
    '.vault.azure.net',
    '.management.core.windows.net',
    '.origin.mediaservices.windows.net',
    '.azure-mobile.net',
    '.queue.core.windows.net',
    '.servicebus.windows.net',
    '.database.windows.net',
    '.azureedge.net',
    '.table.core.windows.net',
    '.trafficmanager.net',
    '.azurewebsites.net',
    '.visualstudio.com'
]
AWSServers = [
    '.amazonaws.com'
]
FontAwesomeServers = [
    'use.fontawesome.com'
]
FacebookServers = [
    "atlassolutions.com",
    "e.gg",
    "facebook.com",
    "facebook.de",
    "facebook.fr",
    "facebook.net",
    "fb.com",
    "fb.me",
    "fbcdn.net",
    "friendfeed.com",
    "instagram.com",
    "internalfb.com",
    "messenger.com",
    "meta.com",
    "oculus.com",
    "oversightboard.com",
    "whatsapp.com",
    "workplace.com",
    "apps.fbsbx.com",
    "atdmt.com",
    "atlassolutions.com",
    "facebook.com",
    "facebook.de",
    "facebook.fr",
    "facebook.net",
    "fb.com",
    "fb.me",
    "fbcdn.net",
    "fbsbx.com",
    "friendfeed.com",
    "instagram.com",
    "messenger.com",

    ".atlassolutions.com",
    ".e.gg",
    ".facebook.com",
    ".facebook.de",
    ".facebook.fr",
    ".facebook.net",
    ".fb.com",
    ".fb.me",
    ".fbcdn.net",
    ".friendfeed.com",
    ".instagram.com",
    ".internalfb.com",
    ".messenger.com",
    ".meta.com",
    ".oculus.com",
    ".oversightboard.com",
    ".whatsapp.com",
    ".workplace.com",
    ".apps.fbsbx.com",
    ".atdmt.com",
    ".atlassolutions.com",
    ".facebook.com",
    ".facebook.de",
    ".facebook.fr",
    ".facebook.net",
    ".fb.com",
    ".fb.me",
    ".fbcdn.net",
    ".fbsbx.com",
    ".friendfeed.com",
    ".instagram.com",
    ".messenger.com"    
]
GoogleMapsServers = [
    'maps.googleapis.com'
]
AdobeServers = [
    "adobe.com",
    "fyre.co",
    "livefyre.com",
    "typekit.com",
    "2o7.net",
    "auditude.com",
    "demdex.com",
    "demdex.net",
    "dmtracker.com",
    "efrontier.com",
    "everestads.net",
    "everestjs.net",
    "everesttech.net",
    "hitbox.com",
    "omniture.com",
    "omtrdc.net",
    "touchclarity.com"
]
FontsExt = [
    '.ttf',
    '.woff',
    '.woff2'
]

def eventToEvidence(event):
    return event['request']

def checkContactedHosts(poisonedHosts):
    evidences = []
    for event in networkLogs:
        if event['method'] != 'Network.requestWillBeSent':
            continue
        url = urlparse(event['params']['request']['url'])
        host = url.netloc
        if ':' in host:
            host = host[0:host.index(':')]
        if host in poisonedHosts:
            if host[0] == '.':
                if url.netloc.endswith(host):
                    evidences.append(eventToEvidence(event))
            elif url.netloc == host:
                evidences.append(eventToEvidence(event))
    if len(evidences) == 0:
        return ""
    return str(evidences)

def checkActualUrl(browser):
    return browser.current_url

def checkCookies(browser):
    cookies = browser.get_cookies()
    if len(cookies) == 0:
        return ""
    return str(cookies)

def checkGoogleFonts(browser):
    evidences = []
    
    for event in networkLogs:
        url = urlparse(event['params']['request']['url'])
        host = url.netloc
        if ':' in host:
            host = host[0:host.index(':')]
        if host in GoogleFontsServers:
            if url.path.contains('/css'):
                evidences.append(eventToEvidence(event))
            else:
                for ext in FontsExt:
                    if url.path.endswith(ext):
                        evidences.append(eventToEvidence(event))
                        break
    if len(evidences) == 0:
        return ""
    return str(evidences)

def checkAzure(browser):
    return checkContactedHosts(AzureServers)
def checkAWS(browser):
    return checkContactedHosts(AWSServers)
def checkFontAwesome(browser):
    return checkContactedHosts(FontAwesomeServers)
def checkFacebook(browser):
    return checkContactedHosts(FacebookServers)
def checkGoogleMaps(browser):
    return checkContactedHosts(GoogleMapsServers)
def checkGoogleReCAPTCHA(browser):
    evidences = []
    for event in networkLogs:
        url = urlparse(event['params']['request']['url'])
        host = url.netloc
        if ':' in host:
            host = host[0:host.index(':')]
        if host == 'www.google.com' and url.path.startswith('/recaptcha/api.js'):
            evidences.append(eventToEvidence(event))
    if len(evidences) == 0:
        return ""
    return str(evidences)
def checkAdobe(browser):
    return checkContactedHosts(AdobeServers)


## Check execution

def runChecks(automatism, browser):
    url = automatism.address

    results = {}
    jsChecksCount = countJSChecks(checksToRun)

    try:
        browseTo(browser, url)
        actual_url = browser.current_url

        runPythonChecks('000-', results, browser)
        
        #time.sleep(20)  # to wait for F12
        
        while countJSChecks(results) != jsChecksCount:
            if actual_url != browser.current_url:
                browseTo(browser, actual_url)

            waitUntilPageLoaded(browser)

            # due to the async nature of some check operations
            # we need to regenerate and run this script several times
            # collecting results provided by each run and excluding
            # the previous executed tests.
            script = jsFramework;        
            allChecks = ""
            for toRun in checksToRun:
                if checksToRun[toRun]['type'] != 'js':
                    continue
                if not (toRun in results): 
                    checkCode = checksToRun[toRun]['script']
                    allChecks += singleJSCheck % (toRun, checkCode)

            script += runAllJSChecks % allChecks
            script += "return runAllJSChecks();";
        
            newResults = browser.execute_script(script)
            print('script executed:', newResults)
            for js in newResults:
                if newResults[js]['issues'] != None:
                    results[js] = newResults[js]
 
        runPythonChecks('999-', results, browser)
        
        completionTime = str(datetime.now())
                
        for js in checksToRun:
            execution = check.Execution(automatism)
            issues = results[js]['issues']
            if results[js]['completed']:
                execution.complete(issues, completionTime)
            else:
                execution.interrupt(issues, completionTime)
            print("execution of %s:" % js, str(execution))
            checksToRun[js]['output'].write(str(execution)+'\n')
            
    except WebDriverException as err:
        print("WebDriverException of type %s occurred" % err.__class__.__name__, err.msg)
            
        # un check ha causato una eccezione: 
        # - registro i risultati raccolti
        # - registro l'eccezione su tutti i check che non ho potuto eseguire
        failTime = str(datetime.now())
        for js in checksToRun:
            execution = check.Execution(automatism)
            if js in results:
                issues = results[js]['issues']
                if results[js]['completed']:
                    execution.complete(issues, failTime)
                else:
                    execution.interrupt(issues, failTime)
            else:
                issues = "%s: %s" % (err.__class__.__name__, err.msg)
                execution.interrupt(issues, failTime)
            checksToRun[js]['output'].write(str(execution)+'\n')

        if commons.isNetworkDown():
            print('Network down: waiting...')
            commons.waitUntilNetworkIsBack()
            print('Network restored: back to work')

        if err.__class__.__name__ == 'TimeoutException' and 'receiving message from renderer' in err.msg:
            raise BrowserNeedRestartException
        if 'invalid session id' in err.msg:
            raise BrowserNeedRestartException
        if 'chrome not reachable' in err.msg:
            raise BrowserNeedRestartException
    #time.sleep(100000)

def runPythonChecks(prefix, results, browser):
    for toRun in checksToRun:
        if not toRun.startswith(prefix):
            continue
        if checksToRun[toRun]['type'] != 'py':
            continue
        if toRun in results:
            continue
        try:
            functionToRun = checksToRun[toRun]['function']
            checkResult = functionToRun(browser)
            #print(f'{toRun} completed:', checkResult)
            results[toRun] = {
                'completed': True,
                'issues': checkResult
            }
        except Exception as err:
            print(f'{toRun} interrupted:', str(err))
            results[toRun] = {
                'completed': False,
                'issues': str(err)
            }

def loadAllChecks(dataset, checksToRun):
    
    addPythonCheck(dataset, checksToRun, '000-actual-url', checkActualUrl)
    addPythonCheck(dataset, checksToRun, '000-cookies', checkCookies)
    
    files = os.listdir('./cli/check/browsing/')
    files = sorted(files)
    for jsFile in files:
        addJSCheck(dataset, checksToRun, jsFile)

    addPythonCheck(dataset, checksToRun, '999-cookies', checkCookies)
    addPythonCheck(dataset, checksToRun, '999-aws', checkAWS)
    addPythonCheck(dataset, checksToRun, '999-adobe', checkAdobe)
    addPythonCheck(dataset, checksToRun, '999-azure', checkAzure)
    addPythonCheck(dataset, checksToRun, '999-facebook', checkFacebook)
    addPythonCheck(dataset, checksToRun, '999-fontawesome', checkFontAwesome)
    addPythonCheck(dataset, checksToRun, '999-googlefonts', checkGoogleFonts)
    addPythonCheck(dataset, checksToRun, '999-googlemaps', checkGoogleMaps)
    addPythonCheck(dataset, checksToRun, '999-googlerecaptcha', checkGoogleReCAPTCHA)

def addJSCheck(dataset, checksToRun, jsFile):
    jsFilePath = './cli/check/browsing/%s' % jsFile
    #print("jsFilePath %s" % jsFilePath)
    if not (jsFile.endswith('.js') and os.path.isfile(jsFilePath)):
        return # nothing to do

    js = ""
    with open(jsFilePath, "r") as f:
        js = f.read()
    outputFile = check.outputFileName(dataset, 'browsing', jsFile.replace('.js', '.tsv'))
    directory = os.path.dirname(outputFile)
    #print("mkdir %s", directory)
    os.makedirs(directory, 0o755, True)
    checksToRun[jsFile] = {
        'type': 'js',
        'script': js,
        'output': open(outputFile, "w", buffering=1, encoding="utf-8")
    }

def countJSChecks(dictionary):
    return len([c for c in dictionary if c.endswith('.js')])

def addPythonCheck(dataset, checksToRun, name, pythonFunction):
    outputFile = check.outputFileName(dataset, 'browsing', name + '.tsv')
    directory = os.path.dirname(outputFile)
    #print("mkdir %s", directory)
    os.makedirs(directory, 0o755, True)
    checksToRun[name] = {
        'type': 'py',
        'function': pythonFunction,
        'output': open(outputFile, "w", buffering=1, encoding="utf-8")
    }


jsFramework = """

if(!Object.hasOwn(window, 'MonitoraPA')){
    window.MonitoraPA = {};
    window.monitoraPACallbackPending = 0;
}

function monitoraPAWaitForCallback(){
debugger;
    ++window.monitoraPACallbackPending;
}
function monitoraPACallbackCompleted(){
debugger;
    --window.monitoraPACallbackPending;
}

function monitoraPAClick(element){
    monitoraPAWaitForCallback();
    window.setTimeout(function(){
        element.click();
    }, 2000);
    window.setTimeout(function(){
        // this will be executed only if no navigation occurred
        monitoraPACallbackCompleted();
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

    if(window.monitoraPAUnloading == true || window.monitoraPACallbackPending > 0){
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

def tryPort(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = False
    try:
        sock.bind(("127.0.0.1", port))
        result = True
    except:
        print("Port is in use")
    sock.close()
    return result


## Browser control functions
def openBrowser(cacheDir):
    op = uc.ChromeOptions()
    
    op.headless = True
    op.add_argument('--headless')


    # Tentiamo porte finchè non ne troviamo una libera
    base_port = 42069
    while(not tryPort(base_port)):
        time.sleep(1)
        base_port += 1

    print(base_port)
    
    op.add_argument("--remote-debugging-port=" + str(base_port))
    #op.add_argument("--auto-open-devtools-for-tabs")
    
    op.add_argument('--user-data-dir='+cacheDir)
    op.add_argument('--home='+cacheDir.replace('udd', 'home'))
    op.add_argument('--incognito')
    #op.add_argument('--disable-web-security')
    #op.add_argument('--no-sandbox')
    op.add_argument('--disable-popup-blocking')
    op.add_argument('--disable-extensions')
    op.add_argument('--dns-prefetch-disable')
    op.add_argument('--disable-gpu')
    op.add_argument('--disable-dev-shm-usage')
    #op.add_argument('--ignore-certificate-errors')
    op.add_argument('--ignore-ssl-errors')
    op.add_argument('--enable-features=NetworkServiceInProcess')
    op.add_argument('--disable-features=NetworkService,SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure')
    op.add_argument('--window-size=1920,1080')
    op.add_argument('--aggressive-cache-discard')
    op.add_argument('--disable-cache')
    op.add_argument('--disable-application-cache')
    op.add_argument('--disable-offline-load-stale-cache')
    op.add_argument('--disk-cache-size=' + str(5*1024*1024)) # 5MB
    #op.add_experimental_option("excludeSwitches", ["enable-automation"])
    #op.add_experimental_option('useAutomationExtension', False)
    #op.add_argument('--disable-blink-features=AutomationControlled')
    op.add_argument('--no-first-run --no-service-autorun --password-store=basic')

    chromedriver_path = os.path.join(os.getcwd(),'browserBin/chrome/chrome')
    if os.name == 'nt': # Se viene eseguito su windows
        chromedriver_path += ".exe"
    
    browser = uc.Chrome(options=op, version_main=104, browser_executable_path=chromedriver_path, enable_cdp_events=True)

    browser.get('about:blank')

    browser.add_cdp_listener('Network.requestWillBeSent', collectNetworkLogs)
    browser.add_cdp_listener('Network.requestWillBeSentExtraInfo', collectNetworkLogs)
    browser.add_cdp_listener('Network.responseReceived', collectNetworkLogs)
    browser.add_cdp_listener('Network.responseReceivedExtraInfo', collectNetworkLogs)
    browser.set_page_load_timeout(90)
        
    
    return browser

def browseTo(browser, url):
    # we are in incognito mode: each new tab get a clean state for cheap
    networkLogs = []
    
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
        needRefresh = browser.execute_script('return document.getElementsByTagName("body").length == 0;')
        if needRefresh:
            browser.execute_script('window.location.reload();')
            time.sleep(2)
            browser.get('about:blank')
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
    browser.execute_script("window.addEventListener('unload', e => { window.monitoraPAUnloading = true; }, {capture:true});")
    #print("browseTo DONE")

def waitUntilPageLoaded(browser, period=2):
    #print('waitUntilPageLoaded %s ' % browser.current_url, end='')
    
    readyState = False
    count = 0
    
    while not readyState and count < 60:
        time.sleep(period)
        readyState = browser.execute_script('return document.readyState == "complete" && !window.monitoraPAUnloading && !window.monitoraPACallbackPending;')
        count += 1
    #print()

def restartBrowser(browser, cacheDir):
    print('restarting Browser: pid %d, dataDir %s' % (browser.service.process.pid, cacheDir))
    process = psutil.Process(browser.service.process.pid)
    tokill = process.children(recursive=True)
    tokill.append(process)
    browser.quit()
    time.sleep(10)
    for p in tokill:
        try:
            p.kill()
        except psutil.NoSuchProcess:
            pass
    browser = None
    time.sleep(10)
    return openBrowser(cacheDir)

def collectNetworkLogs(event):
    networkLogs.append(event)
    #print(event)

def browserReallyNeedARestart(browser):
    try:
        browseTo(browser, 'https://monitora-pa.it/tools/ping.html')
    except:
        return True
    return False

def getCacheDir(dataset):
    cacheDirsContainer = os.path.dirname(check.outputFileName(dataset, 'browsing', 'user-data-dirs', 'tmp.tsv'))
    os.makedirs(cacheDirsContainer, 0o755, True)
    cacheDir = tempfile.mkdtemp(prefix='udd-%d-' % os.getpid(), dir=cacheDirsContainer)
    return cacheDir








def main(argv):
    if len(argv) != 2:
        usage()

    dataset = argv[1]

    if not os.path.isfile(dataset):
        print(f"input dataset not found: {dataset}");
        usage()
        
    run(dataset)


if __name__ == "__main__":
    main(sys.argv)
