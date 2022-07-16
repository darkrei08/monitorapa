#!/usr/bin/env python3

# This file is part of MonitoraPA
#
# Copyright (C) 2022 Giacomo Tesio <giacomo@tesio.it>
# Copyright (C) 2022 Leonardo Canello <leonardocanello@protonmail.com>
#
# MonitoraPA is a hack. You can use it according to the terms and
# conditions of the Hacking License (see LICENSE.txt)

import sys
#sys.path.insert(0, '.')

from lib import check

from seleniumwire import webdriver
from selenium.common.exceptions import WebDriverException
import time
from datetime import datetime
import os.path

import socket

jsChecks = {}

jsFramework = """
function sendMonitoraPACheckResult(url, name, issues){
        var http = new XMLHttpRequest();
        http.open("GET", url);
        http.setRequestHeader('X-MonitoraPA-CheckName', name);
        http.setRequestHeader('X-MonitoraPA-CheckIssues', issues);
        http.setRequestHeader('X-MonitoraPA-Owner', window.monitoraPAOwner);
        http.setRequestHeader('X-MonitoraPA-Address', window.monitoraPAAddress);
        http.send()
} 
function runMonitoraPACheck(name, check){
    var issues;
    try {
        issues = check();
        sendMonitoraPACheckResult("https://monitora-pa.it/check/completed", name, issues);
    } catch(e) {
        issues = "runMonitoraPACheck: " + e.name + ": " + e.message;
        sendMonitoraPACheckResult("https://monitora-pa.it/check/interrupted", name, issues);
    }
}
"""

singleJSCheck = """
runMonitoraPACheck('{%s}', function(){
{%s}
});
"""

def usage():
    print("""
./cli/selenium.py out/$SOURCE/$DATE/dataset.tsv

Where:
- $SOURCE is a folder dedicated to a particular data source
- $DATE is the data source creation date in ISO 8601 format (eg 2022-02-28)
""")
    sys.exit(-1)




def clickConsentButton(url, browser):
	# thanks Mauro Gorrino
    consentPath = "//button[contains(translate(., 'ACET', 'acet'), 'accett')]"
    buttons = browser.find_elements_by_xpath(consentPath)
    for button in buttons:
        try:
            browser.execute_script("arguments[0].click()", button)
        except Exception:
            pass
    return len(buttons) > 0


def saveError(lineNum, error):
    fname = '%s/%s.ERR.txt' % (outDir, lineNum)
    with open(fname, 'w') as f:
        f.write(error)

def interceptor(request):
    if request.url.startswith('https://monitora-pa.it/'):
        checkTime = str(datetime.now())
        owner = request.headers['X-MonitoraPA-Owner']
        address = request.headers['X-MonitoraPA-Address']
        checkName = request.headers['X-MonitoraPA-CheckName']
        checkIssues = request.headers['X-MonitoraPA-CheckIssues']
        checkFile = jsCheck[checkName]['output']
        if request.url.endswith('success/'):
            checkFile.write(f"{owner}\tWeb|t{address}\t{checkTime}\t1\t{checkIssues}")
        else:
            checkFile.write(f"{owner}\tWeb|t{address}\t{checkTime}\t0\t{checkIssues}")
        request.create_response(
            status_code=200,
        )

def openBrowser():
    op = webdriver.ChromeOptions()
#    op.add_argument('--headless')
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

    browser = webdriver.Chrome('chromedriver', options=op)
    browser.request_interceptor = interceptor
    browser.scopes = [
        '.*monitora-pa.*'
    ]
    
    browser.get('about:blank')
    
    return browser
    
def browseTo(browser, url):
    # we are in incognito mode: each new tab get a clean state for cheap
    
    while len(browser.window_handles) > 1:
        browser.switch_to.window(driver.window_handles[-1])
        browser.close()
    browser.switch_to.window(browser.window_handles[0])
    # browser.delete_all_cookies()
    browser.execute_script("window.open('');")
    browser.switch_to.window(browser.window_handles[-1])
    browser.get(url)

def getPageContent(browser):
    dom = browser.find_element_by_tag_name('html').get_attribute('innerHTML')
    return dom.encode('utf-8')
    
def waitUntilPageLoaded(browser):
    
    oldContent = ''
    newContent = getPageContent(browser)
    
    oldRequests = 0
    newRequests = len(browser.requests)
    
    while oldContent != newContent or oldRequests != newRequests:
        time.sleep(2)
        oldContent = newContent
        oldRequests = newRequests
        newContent = getPageContent(browser)
        newRequests = len(browser.requests)

def runChecks(automatism, browser):
    url = automatism.address

    try:
        print("browsing to ", url)
        browseTo(browser, url)
        waitUntilPageLoaded(browser)
        
        print("clickConsentButton ", url)
        consented = clickConsentButton(url, browser)
        if consented:
            waitUntilPageLoaded(browser)

        driver.execute_script(f"window.monitoraPAOwner = '{automatism.owner}';")
        driver.execute_script(f"window.monitoraPAAddress = '{automatism.address}';")
        driver.execute_script(jsFramework)
        
        allChecks = ""
        for js in jsChecks:
            checkCode = jsChecks[js]['script']
            allChecks += singleJSCheck % (js, checkCode)

        script = "setTimeout(function(){%s},0);" % allChecks
        browser.execute_script(script)
        
        time.sleep(1)
        
        waitUntilPageLoaded(browser)
    except WebDriverException as err:
        saveError(lineNum, "%s\n%s" % (url, err))
    #time.sleep(100000)

def loadChecks(dataset):
    checksToRun = {}
    files = os.listdir('./cli/check/selenium/')
    for jsFile in files:
        if os.path.isfile(jsFile) and jsFile.endswith('.js'):
            with open(jsFile) as f:
                js = f.read()
            outputFile = check.outputFileName(dataset, 'selenium', jsFile.replace('.js', '.tsv'))
            checksToRun[jsFile] = {
                'script': js,
                'output': open(outputFile, "w")
            }
    return checksToRun;


def main(argv):
    if len(sys.argv) != 2:
        usage()

    dataset = sys.argv[1]

    if not os.path.isfile(dataset):
        print(f"input dataset not found {dataset}");
        usage()

    jsChecks = loadChecks(dataset)
    browser = openBrowser()

    count = 0
    try:
        with open(dataset, 'r') as inf:
            for line in inf:
                automatism = check.parseInput(line)
                if automatism.type != 'Web':
                    continue

                runChecks(automatism, browser)
                count += 1
    except (KeyboardInterrupt):
        print("Interrupted at %s" % count)

    del browser.request_interceptor
    browser.quit()


if __name__ == "__main__":
    main(sys.argv)
