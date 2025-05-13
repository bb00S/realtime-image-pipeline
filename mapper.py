#!/usr/bin/env python3
import sys
from datetime import datetime

"""
Mapper script for EMR.
Input: timestamp,detected_label,confidence
Output: detected_label \t 1
"""

for line in sys.stdin:
    line = line.strip()
    if not line or line.startswith("timestamp"):
        continue

    try:
        timestamp, label, confidence = line.split(',')
        label = label.strip().upper()
        print(f"{label}\t1")
    except ValueError:
        continue  # skip malformed lines
