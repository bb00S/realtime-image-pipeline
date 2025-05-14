#!/usr/bin/env python3
import subprocess
import os
import sys

"""
Simulates MapReduce job locally (such as EMR would run).
"""

def run_mapreduce(input_file):
    if not os.path.exists(input_file):
        print("Input file not found:", input_file)
        return

    mapper = subprocess.Popen(['python3', 'mapper.py'], stdin=open(input_file), stdout=subprocess.PIPE)
    sorter = subprocess.Popen(['sort'], stdin=mapper.stdout, stdout=subprocess.PIPE)
    reducer = subprocess.Popen(['python3', 'reducer.py'], stdin=sorter.stdout, stdout=subprocess.PIPE)

    output, _ = reducer.communicate()
    print("=== Aggregated Results ===")
    print(output.decode())

if __name__ == "__main__":
    run_mapreduce("captcha_metadata.csv")
