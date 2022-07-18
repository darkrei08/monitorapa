#!/usr/bin/env python3

# This file is part of MonitoraPA
#
# Copyright (C) 2022 Giacomo Tesio <giacomo@tesio.it>
#
# MonitoraPA is a hack. You can use it according to the terms and
# conditions of the Hacking License (see LICENSE.txt)

import sys
import os.path

def usage():
    print("""
./cli/tools/split.py ./path/to/file.tsv N

Split ./path/to/file.tsv into N files of roughly the same size 
with a sequential prefix. Useful to parallelize the elaboration
of large dataset, e.g. 

./cli/tools/split.py ./out/enti/YYYY-MM-YY/dataset.tsv $(nproc --all)
""")
    sys.exit(-1)

def main(argv):
    if len(argv) != 3:
        usage()
    try:
        chunks = int(argv[2])
    except:
        print(f"{argv[2]} is not an integer")
        usage()
        
    inputFile = argv[1]
    outputDir = os.path.dirname(inputFile)
    
    lines = []
    try:
        with open(inputFile, "r") as inf:
            lines = inf.readlines()
    except:
        print(f"Cannot read {inputFile}")
        usage()

    if len(lines) == 0:
        print(f"{inputFile} is empty: nothing to do.")
        sys.exits(0)
    
    if len(lines) < chunks:
        print(f"{inputFile} contains less than {chunks} lines: nothing to do.")
        sys.exits(0)

    chunkSize = len(lines) // chunks
    if len(lines) % chunks > 0:
        chunkSize += 1
    
    chunked = []
    for i in range(0, len(lines), chunkSize):
        chunked.append(lines[i:i+chunkSize])
    
    for i in range(0, len(chunked)):
        outputFile = os.path.join(outputDir, str(i).zfill(3) + '-' + os.path.basename(inputFile))
        with open(outputFile, "w") as outf:
            outf.writelines(chunked[i])

if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        print("[ ERR ] KeyboardInterrupt, aborting")
        sys.exit(1)
