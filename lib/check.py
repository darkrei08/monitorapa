# This file is part of MonitoraPA
#
# Copyright (C) 2022 Giacomo Tesio <giacomo@tesio.it>
#
# MonitoraPA is a hack. You can use it according to the terms and
# conditions of the Hacking License (see LICENSE.txt)

from datetime import datetime

class Input:
    def __init__(self, owner: str, automatismType: str, automatismAddress: str):
        self.owner = owner
        self.type = automatismType
        self.address = automatismAddress
    def __str__(self):
        return "\t".join([self.owner, self.type, self.address])

def parseInput(line: str) -> Input:
    fields = line.strip().split('\t')
    return Input(fields[0], fields[1], fields[2])

class Execution:
    owner: str
    type: str
    address: str
    time: str
    completed: str = "0"
    issues:str = ""
    def __init__(self, automatism: Input):
        self.owner = automatism.owner
        self.type = automatism.type
        self.address = automatism.address
        self.time = str(datetime.now())
    def complete(self, issues = "", completionTime = None) -> None:
        if completionTime is None:
            completionTime = str(datetime.now())
        self.time = completionTime
        self.completed = "1"
        self.issues = issues.replace('\n', ' ').replace('\t', ' ')
    def interrupt(self, issues, failTime = None) -> None:
        if failTime is None:
            failTime = str(datetime.now())
        self.time = failTime
        self.issues = issues.replace('\n', ' ').replace('\t', ' ')
    def __str__(self) -> str:
        issues = self.issues.replace('\n', ' ').replace('\t', ' ')
        return "\t".join([self.owner, self.type, self.address, self.time, self.completed, issues])

def parseExecution(line: str) -> Execution:
    fields = line.strip().split('\t')
    checkInput = Input(fields[0], fields[1], fields[2])
    execution = Execution(checkInput)
    execution.time = fields[3]
    execution.completed = fields[4]
    execution.issues = fields[5]
    return execution

def outputFileName(dataset, *names):
    from os.path import dirname, basename, join

    if not dataset.endswith('.tsv'):
        raise ValueError("Input file name must end with .tsv")
    if len(names) < 1:
        raise ValueError("Missing file name components.")
    fileName = names[len(names) - 1]
    if not fileName.endswith('.tsv'):
        raise ValueError("Output file name must end with .tsv")
    if '_' in fileName:
        raise ValueError("Output file name cannot contain '_' (see issue #20)")

    executionDir = dirname(dataset)
    if basename(dataset) != 'dataset.tsv':
        mutableNames = list(names)
        mutableNames[len(names) - 1] = fileName.replace('.tsv', '_' + basename(dataset))
        names = tuple(mutableNames)
    
    return join(executionDir, 'check', *names)
