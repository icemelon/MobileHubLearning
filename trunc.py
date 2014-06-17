#! /usr/bin/env python

import sys

left = 0
length = 90000

with open(sys.argv[1]) as file:
    index = 0
    for line in file:
        if index >= left:
            print line.strip()
        index += 1
        if index >= left+length:
            break