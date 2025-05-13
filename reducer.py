#!/usr/bin/env python3
import sys

"""
Reducer script for EMR.
Aggregates counts from mapper.
"""

current_label = None
current_count = 0

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    label, count_str = line.split('\t')
    count = int(count_str)

    if label == current_label:
        current_count += count
    else:
        if current_label:
            print(f"{current_label}\t{current_count}")
        current_label = label
        current_count = count

if current_label:
    print(f"{current_label}\t{current_count}")
