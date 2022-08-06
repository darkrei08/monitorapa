#!/usr/bin/env python3

# This file is part of MonitoraPA
#
# Copyright (C) 2022 Leonardo Canello <leonardocanello@protonmail.com>
# Copyright (C) 2022 Giacomo Tesio <giacomo@tesio.it>
#
# MonitoraPA is a hack. You can use it according to the terms and
# conditions of the Hacking License (see LICENSE.txt)

import sys
sys.path.insert(0, '.') # NOTA: da eseguire dalla root del repository git

from lib import mailer, check

import smtplib
import ssl
import configparser
import sys
import datetime
import os
import time
from email.message import EmailMessage
from getpass import getpass


def usage():
    print("""
./cli/mail/notify.py out/$SOURCE/$DATE/check/output.tsv cli/mail/notify/PA04.template out/$SOURCE/$DATE/enti.tsv "Colonna Owner"

Laddove:
- out/$SOURCE/$DATE/check/output.tsv contiene l'output di un check i cui
  problemi si intende segnalare ai responsabili affinché li correggano
- cli/mail/notify/PA04.template è il template della mail che si intende inviare
- out/$SOURCE/$DATE/enti.tsv è il dataset iniziale da cui si era partiti
  che fornirà le variabili sostituite nel testo della mail
- "Colonna Owner" è la colonna in cui è possibile rintracciare la chiave
  contenuta nella prima colonna dell'output.tsv
  
I log degli invii effettuati viene salvato in out/$SOURCE/$DATE/notify/output.PA04.tsv
un log per ogni riga presente nel file sorgente iniziale (ad esempio enti.tsv)
con il consueto formato di check.Execution:
- Completed == 0 and Issues = "" => l'invio non era necessario
- Completed == 0 and Issues != "" => si è verificato un errore durante l'invio
- Completed == 1 => Issue contiene data e ora dell'invio e destinatario
""")
    sys.exit(-1)

def computeLogFileName(checkToNotify, mailTemplatePath):
    if not '/check/' in checkToNotify:
        raise Error("Checks to notify must be in a .../check/.. folder")
    if not checkToNotify.endswith('.tsv'):
        raise Error("Checks to notify must end in .tsv")
    if not mailTemplatePath.endswith('.template'):
        raise Error("Mail templates must end in .template")
    templateName = os.path.basename(mailTemplatePath).replace('.template', '')
    result = checkToNotify
    result = result.replace('/check/', '/notify/')
    result = result.replace('.tsv', '.' + templateName + '.tsv')
    
    os.makedirs(os.path.dirname(result), 0o755, True)
    
    return result

def countLinesToSkip(logFileName):
    result = 0
    try:
        with open(logFileName, "r") as inputFile:
            for line in inputFile:
                result += 1
    except:
        # in caso di errore si rifa dall'inizio
        return 0
    return result

def sendMail(server, template, environment, execution, debugReceiverEmail):
    loggedAutomatism = check.Input(execution.owner, 'MonitoraPA_Notification', execution.address)
    loggedExecution = check.Execution(loggedAutomatism)
    
    try:
        headers = template.headers(execution, environment)
        messageContent = template.message(execution, environment)
        
        msg = EmailMessage()
        for header in headers:
            msg[header] = headers[header]
        if debugReceiverEmail != "":
            msg['To']=debugReceiverEmail
        
        # Ci mettiamo in Cc per vedere le mail che mandiamo
        # (Bcc non viene accettato dalle PEC)
        if 'Cc' in headers and headers['Cc'] != headers['From']:
            msg['Cc'] = headers['From'] + '; ' + headers['Cc']
        else:
            msg['Cc'] = headers['From']
        
        msg.set_content(messageContent)
        
        #server.send_message(msg)   # Invio effettivo
        
        loggedExecution.complete(headers['To'])

    except Exception as ex:
        loggedExecution.interrupt(str(ex))

    return loggedExecution

def needsNotification(execution: check.Execution):
    return execution.completed == "1" and execution.issues != ""

def loadCheckResults(fileName):
    # ATTENZIONE: stiamo assumendo una singola esecuzione per owner
    # questo è vero per il dataset AgID-IPA ma potrebbe non esserlo in
    # futuro!
    executions = {}
    with open(fileName, "r") as inputFile:
        for line in inputFile:
            execution = check.parseExecution(line)
            if needsNotification(execution):
                executions[execution.owner] = execution
    return executions
    

def main(argv):
    if len(argv) != 5:
        usage()
    
    # NOTA BENE: carichiamo l'intero set delle esecuzioni che richiedono
    # notifica in memoria. Quando ciò dovesse risultare insostenibile
    # possiamo effettuare gli invii in blocchi via ./cli/tools/split.py
    executions = loadCheckResults(argv[1])
        
    logFileName = computeLogFileName(argv[1], argv[2])
    linesToSkip = countLinesToSkip(logFileName)
    
    # leggo la configurazione del server mail
    # TODO: prompt per la password, in modo da non doverla salvare
    configParser = configparser.RawConfigParser()
    configParser.read('./cli/mail/notify.cfg')
    config = dict(configParser.items('server-settings'))

    sendForReal = str(config['send_for_real'])

    smtpServer = str(config['smtp_server'])
    port = int(config['port'])
    senderEmail = str(config['sender_email'])
    delay = int(config['delay'])
    debugReceiverEmail = str(config['debug_receiver_email'])
    if debugReceiverEmail != "":
        print("DEBUG RUN: mails will be sent to " + debugReceiverEmail);

    password = getpass("Insert Password for " + smtpServer + " (empty to stop):\n")
    if password == "":
        return
    print("OK.")

    template = mailer.Template(argv[2], senderEmail)

    primaryKeyColumn = argv[4]
    lineNumber = 0
    columnNames = []

    with open(argv[3], "r") as inputFile, \
         open(logFileName, "a") as logFile, \
         smtplib.SMTP_SSL(smtpServer, port) as server:

        server.login(sender_email, password) # login al server SMTP
        
        for line in inputFile:
            
            if lineNumber < linesToSkip:
                lineNumber += 1
                continue
            
            cells = line.strip(" \n").split('\t')
            if len(columnNames) == 0:
                columnNames = cells
                if primaryKeyColumn not in columnNames:
                    raise Error("Owner column '" + primaryKeyColumn + "' not found in "+argv[3])
            else:
                environment = {}
                for index in range(len(columnNames)):
                    variableName = columnNames[index]
                    environment[variableName] = cell[index]
                
                owner = environment[primaryKeyColumn]
                loggedExecution = None
                
                if owner in executions:
                    loggedExecution = sendMail(server, template, environment, executions[owner], debugReceiverEmail)
                else:
                    loggedAutomatism = check.Input(owner, 'MonitoraPA_Notification', 'unknown')
                    loggedExecution = check.Execution(loggedAutomatism)
                    loggedExecution = check.interrupt('No need for notification.')
            
            print(lineNumber, loggedExecution)
            logFile.write(str(loggedExecution)+'\n')
            lineNumber += 1
 

if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        print("Interrupted.")
