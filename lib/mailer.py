# This file is part of MonitoraPA
#
# Copyright (C) 2022 Giacomo Tesio <giacomo@tesio.it>
# Copyright (C) 2022 Leonardo Canello <leonardocanello@protonmail.com>
#
# MonitoraPA is a hack. You can use it according to the terms and
# conditions of the Hacking License (see LICENSE.txt)

"""
Classi di utilità per l'invio di segnalazioni agli enti in violazione

Per comprendere questo codice è necessario comprendere le basi della 
programmazione ad oggetti in Python. Fortunatamente non è difficile:

http://openbookproject.net/thinkcs/python/english3e/classes_and_objects_I.html
http://openbookproject.net/thinkcs/python/english3e/classes_and_objects_II.html

NOTA BENE: Non spingetevi oltre nella programmazione ad oggetti senza
aver prima letto seriamente questa intervista a Bjarne Stroustrup e
compreso che non è uno scherzo:
http://harmful.cat-v.org/software/c++/I_did_it_for_you_all
"""

class Template:
	"""
	Modello di mail da inviare.
	
	Il modello è composto di tre parti:
	- documentation, ovvero intestazioni ed informazioni sul template
	  ad uso degli sviluppatori che non viene effettivamente usato 
	  durante l'invio
	- headers, ovvero gli headers SMTP che verranno inviati
	  (fra questi, il Subject e il From)
	- message, testo della mail
	
	La prima riga del file costituisce il separatore fra le diverse parti.
	
	Il valore di ogni header SMTP e il testo della mail possono contenere
	variabili di due tipi:
	1. fornite dall'osservatorio, ovvero
	   - $owner che corrisponde all'identificativo del proprietario
	     dell'automatismo in violazione
	   - $automatismi che corrisponde all'indirizzo dell'automatismo 
	     in violazione
	2. fornite dal file TSV iniziale usato come sorgente per l'osservatorio, 
	   ad esempio il file enti.tsv contenente l'anagrafica AgID-IPA;
	   Tali variabili vengono fornite ai metodi headers() e message() come
	   un dizionario da stringa a stringa chiamato environment, ad esempio
	   ${Descrizione Ente} verrebbe sostituita con il valore corrispondente
	   a environment['Descrizione Ente'].
	   Le variabili non presenti non verranno sostituite, ma non comporteranno
	   un errore.
	"""
	def __init__(self, filePath):
		"Legge il template da filePath."
		with open(filePath, "r") as f:
			lines = f.readlines()
		if len(lines) < 3:
			raise Error("Template is too short: " + filePath)

		separator = lines[0]
		index = 1
		self._documentation = ""
		self._headers = {}
		self._message = ""

		# cicliamo le righe del template fino a trovare il separatore o la fine del file
		while index < len(lines) and lines[index] != separator:
			self._documentation += lines[index] # aggiungiamo alla documentazione
			index += 1
		
		index += 1
		while index < len(lines) and lines[index] != separator:
			header = lines[index].strip(" \n")
			headerNameEnd = header.indexOf(':')
			headerName = header[0:headerNameEnd].strip()
			headerValue = header[headerNameEnd+1:].strip()
			self._headers[headerName] = headerValue # aggiungiamo all'elenco di header
			index += 1
		
		index += 1
		while index < len(lines) and lines[index] != separator:
			self._message += lines[index] # aggiungiamo al messaggio
			index += 1
		
		if 'From' not in self._headers:
			raise Error("Invalid Template: missing From header")
		if 'Subject' not in self._headers:
			raise Error("Invalid Template: missing Subject header")
		if self._message == "":
			raise Error("Invalid Template: missing message content")
			
	def headers(self, execution, environment):
		result = {}
		for headerName in self._headers:
			result[headerName] = replaceVariables(execution, environment, self._headers[headerName])
		return result
	
	def message(self, execution, environment):
		result = replaceVariables(execution, environment, self._message)
		return result

def replaceVariables(automatism, environment, content):
	"""
	Sostituisce le variabili contenute in content con i valori forniti da environment e automatism
	"""
	content = content.replace("$owner", automatism.owner)
	content = content.replace("$automatism", automatism.address)
	for var in environment:
		content = content.replace("${"+var+"}", environment[var])
	return content


