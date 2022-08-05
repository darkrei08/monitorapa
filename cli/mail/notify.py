#!/usr/bin/env python3

# This file is part of MonitoraPA
#
# Copyright (C) 2022 Leonardo Canello <leonardocanello@protonmail.com>
# Copyright (C) 2022 Stefano Gazzella <stefano@gdpready.it>
# Copyright (C) 2022 Mario Sabatino <mario@sabatino.pro>
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
import commons
import os
import time
from email.message import EmailMessage


def usage():
    print("""
./cli/mail/notify.py out/$SOURCE/$DATE/check/output.tsv cli/mail/notify/template.PA04.txt out/$SOURCE/$DATE/enti.tsv "Colonna Owner"

Laddove:
- out/$SOURCE/$DATE/check/output.tsv contiene l'output di un check i cui
  problemi si intende segnalare ai responsabili affinché li correggano
- cli/mail/notify/template.PA04.txt è il template della mail che si intende inviare
- out/$SOURCE/$DATE/enti.tsv è il dataset iniziale da cui si era partiti
  che fornirà le variabili sostituite nel testo della mail
- "Colonna Owner" è la colonna in cui è possibile rintracciare la chiave
  contenuta nella prima colonna dell'output.tsv
  
I log degli invii effettuati viene salvato in out/$SOURCE/$DATE/notify/output.tsv
un log per ogni riga presente nel file sorgente iniziale (ad esempio enti.tsv)
con il consueto formato di check.Execution:
- Completed == 0 and Issues = "" => l'invio non era necessario
- Completed == 0 and Issues != "" => si è verificato un errore durante l'invio
- Completed == 1 => Issue contiene data e ora dell'invio e destinatario
""")
    sys.exit(-1)

def computeLogFileName(checkToNotify):
    if not '/check/' in checkToNotify:
        raise Error("Checks to notify must be in a .../check/.. folder")
    result = checkToNotify.replace('/check/', '/notify/')
    return result

def sendMail(server, template, environment, execution):
    pass

def main(argv):
    if len(argv) != 5:
        usage()
    
    needingNotifications = {}
    with open(argv[1], "r") as inputFile:
        for line in inputFile:
            execution = check.parseExecution(line)
            if execution.completed == "1" and execution.issues != "":
                needingNotifications[execution.owner] = execution
    if len(needingNotification) == 0:
        return
        
    template = mailer.Template(argv[2])
    logFileName = computeLogFileName(argv[1])
    
    # leggo la configurazione del server mail
    # TODO: prompt per la password, in modo da non doverla salvare
    configParser = configparser.RawConfigParser()
    configParser.read('./cli/mail/notify.cfg')
    config = dict(configParser.items('server-settings'))

    sendForReal = str(config['send_for_real'])

    smtpServer = str(config['smtp_server'])
    port = int(config['port'])
    senderEmail = str(config['sender_email'])
    password = str(config['password'])
    receiverEmail = str(config['debug_receiver_email'])
    

    # TODO leggere da logFileName quanti sono già stati trattati
    # e ignorarne lo stesso numero durante la lettura della sorgente dati
    skip = 0 # quanti da scartare
    
    primaryKey = argv[4]
    count = 0
    columnNames = []
    with open(argv[3], "r") as inputFile and smtplib.SMTP_SSL(smtpServer, port) as server:
        server.login(sender_email, password) # login al server SMTP
        
        for line in inputFile:
            cells = line.strip().split('\t')
            if len(columnNames) == 0:
                columnNames = cells
                if primaryKey not in columnNames:
                    raise Error("Owner column '"+primaryKey+"' not found in "+argv[3])
            else:
                environment = {}
                for index in range(len(columnNames)):
                    variableName = columnNames[index]
                    environment[variableName] = cell[index]
                if environment[primaryKey] in needingNotification:
                    ownerNeedingNotification = environment[primaryKey]
                    sendMail(server, template, environment, needingNotification[ownerNeedingNotification])
                
                
                
    # TODO
    # TODO  Spostare l'invio dentro sendMail()
    # TODO
                
    
    subject = ""
    message = ""
    configParser = configparser.RawConfigParser()
    configParser.read('./cli/point4.cfg')
    config = dict(configParser.items('server-settings'))

    send_for_real = str(config['send_for_real'])

    smtp_server = str(config['smtp_server'])
    port = int(config['port'])
    sender_email = str(config['sender_email'])
    password = str(config['password'])
    receiver_email = str(config['debug_receiver_email'])

    a = datetime.datetime(2022,5,11,17,2,20)


    with smtplib.SMTP_SSL(smtp_server, port) as server:
        server.login(sender_email, password)

        try:
            time_to_wait = int(argv[3])
        except:
            time_to_wait = 0
        
        count = 0
        out_count = 1

        if not os.path.exists(outDir + '/../point4/log.tsv'):
            open(outDir + '/../point4/log.tsv', 'w').close()

        length = 0

        with open(outDir + '/../point4/log.tsv', 'r') as logf:
            length = len(logf.readlines())
            if length != 0:   
                out_count = length 

        with open(outDir + '/../point3/enti.tsv', 'r') as f, open(outDir + '/../point4/log.tsv', 'ab', buffering=0) as logf:
            if length == 0:   
                logf.write("Codice_IPA\tMail1\tSito_istituzionale\tData".encode("utf-8"))
                logf.flush()
     
            for line in f:
                if count >= out_count:
                  
                    fields = line.split('\t')

                    if (int(fields[35]) == 1):

                        primo_invio = a + datetime.timedelta(seconds=count*10)

                        subject = process(fields, subject, primo_invio)
                        msg = process(fields, message, primo_invio)
                        
                        print("Codice: " + fields[1] + ", Denominazione: " + fields[2] + ", nome: " + fields[12]
          + ", cognome: " + fields[13] + ", sito: " + fields[29].lower() + ", mail: " + fields[19], ", result: " + fields[35])

                        if send_for_real.lower() == "true":
                            # Rimpiazzare receiver_email con fields[19] quando si vuole mandare realmente le mail
                            final_msg = EmailMessage()
                            final_msg['From']=sender_email

                            final_msg['To']=receiver_email #per provare in debug: receiver_email altrimenti fields[19]
                            final_msg['Cc']=sender_email #Per vedere le mail che mandiamo, Bcc non pare essere accettato.

                            final_msg['Subject']=subject
                            final_msg.set_content(msg)

                            print(fields[19])
                            
                            #server.send_message(final_msg)
                            
                            logf.write(("\n%s\t%s\t%s\t%s" % (fields[1], fields[19], fields[29], str(datetime.datetime.now()))).encode("utf-8"))
                            logf.flush()

                            time.sleep(time_to_wait)
                
                    else:
                        logf.write(("\n%s\t%s\t%s" % (fields[1], fields[19], fields[29])).encode("utf-8"))
                        logf.flush()

                count += 1


if __name__ == "__main__":
    main(sys.argv)
