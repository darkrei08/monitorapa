#!/usr/bin/env -S python3 -u

# This file is part of MonitoraPA
#
# Copyright (C) 2022 Giacomo Tesio <giacomo@tesio.it>
#
# MonitoraPA is a hack. You can use it according to the terms and
# conditions of the Hacking License (see LICENSE.txt)

import sys
sys.path.insert(0, '.') # NOTA: da eseguire dalla root del repository git

from lib import check
import os
import glob

def usage():
    print("""
./cli/tools/merge-outputs.py out/$SOURCE/$DATE/dataset.tsv

Where:
- $SOURCE is a folder dedicated to a particular data source
- $DATE is the data source creation date in ISO 8601 format (eg 2022-02-28)
""")
    sys.exit(-1)

def getTargetFileName(filename):
    targetFileNameEnd = filename.index('_')
    targetFileName = filename[0:targetFileNameEnd] + '.tsv'
    return targetFileName
    
def cleanupPreviousMerge(filesToMerge):
    for toMerge in filesToMerge:
        target = getTargetFileName(toMerge)
        if os.path.exists(target):
            os.remove(target)

def main(argv):
    if len(argv) != 2:
        usage()

    filename = os.path.basename(argv[1])
    dirname = os.path.dirname(argv[1])
    os.chdir(dirname)
    filesToMerge = sorted(glob.glob('./**/*_*-' + filename, recursive=True))

    # cancelliamo tutti i file prodotti da un merge precedente 
    # (se qualcosa è andato storto)
    cleanupPreviousMerge(filesToMerge)
    
    # copiamo ogni linea di ciascun file di output in un nuovo file
    # con il nome del check
    for f in filesToMerge:
        target = getTargetFileName(f)
        print (target)
        with open(f, "r") as inputFile, open(target, "a") as outputFile:
            for line in inputFile:
                outputFile.write(line.strip('\n') + '\n')

    # eliminiamo i vecchi file ormai ridondanti
    for f in filesToMerge:
        os.remove(f)

if __name__ == "__main__":
    main(sys.argv)

