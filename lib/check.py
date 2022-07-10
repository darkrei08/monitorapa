# This file is part of MonitoraPA
#
# Copyright (C) 2022 Giacomo Tesio <giacomo@tesio.it>
#
# MonitoraPA is a hack. You can use it according to the terms and
# conditions of the Hacking License (see LICENSE.txt)

from datetime import datetime

class Input:
    def __init__(self, owner, automatismType, automatismAddress):
        self.owner = owner
        self.type = automatismType
        self.address = automatismAddress
    def __str__(self):
        return "\t".join([self.owner, self.type, self.address])

def parseInput(line):
    fields = line.strip().split('\t')
    return CheckInput(fields[0], fields[1], fields[2])

class Execution:
    def __init__(self, automatism, time = str(datetime.now()), completed = "0", issues = ""):
        self.owner = automatism.owner
        self.type = automatism.type
        self.address = automatism.address
        self.time = time
        self.completed = completed
        self.issues = issues
    def completed(self, issues = ""):
        self.time = str(datetime.now())
        self.completed = "1"
        self.issues = issues
    def interrupted(self, issues):
        self.time = str(datetime.now())
        self.issues = issues
    def __str__(self):
        return "\t".join([self.owner, self.type, self.address, self.time, self.completed, self.issues])

def parseExecution(line):
    fields = line.strip().split('\n')
    checkInput = CheckInput(fields[0], fields[1], fields[2])
    return CheckExecution(checkInput, fields[3], fields[4], fields[5])

def outputFileName(dataset, *names):
    from os.path import dirname, basename, join

    if not dataset.endswith('.tsv'):
        raise ValueError("Input file name must end with .tsv").
    if len(names) < 1:
        raise ValueError("Missing file name components.")
    fileName = names[len(names) - 1]
    if not fileName.endswith('.tsv'):
        raise ValueError("Output file name must end with .tsv").

    executionDir = dirname(dataset)
    if basename(dataset) != 'dataset.tsv':
        names[len(names) - 1] = fileName.replace('.tsv', '-' + basename(dataset))
    
    targetDir = join(executionDir, 'check', *names)
