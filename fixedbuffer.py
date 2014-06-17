#! /usr/bin/env python

import sys

class SensorEvent:
    def __init__(self, values):
        self.timestamp = values[0]
        self.values = values[1:4]
        self.trigger = values[4]

    def __str__(self):
        s = str(self.timestamp) + ',' \
            + str(self.values[0]) + ',' \
            + str(self.values[1]) + ',' \
            + str(self.values[2])
        return s

argv = sys.argv[1:]
if len(argv) < 2:
    print sys.argv[0], '<app_trace.csv> <buffer size>'
    sys.exit()

trace_file = argv[0]
buffer_size = eval(argv[1])

samples = []
with open(trace_file) as file:
    for line in file:
        if line:
            data = [eval(x) for x in line.split(',')]
            e = SensorEvent(data)
            samples.append(e)

WINDOW_SIZE = 23
delays = []
delayed_cnt = 0
for i in range(len(samples)):
    event = samples[i]
    if event.trigger:
        delay = buffer_size - 1 - (i % buffer_size)
        if delay > WINDOW_SIZE:
            delayed_cnt += 1
        delays.append(delay)

delays = sorted(delays)
delay95 = delays[int(.95 * len(delays))]

print 'delayed trigger: %d/%d(%.2f%%)' % (delayed_cnt, len(delays), 100.0 * delayed_cnt / len(delays))
print 'max delay:', max(delays)
print '95% delay:', delay95
print 'avg delay:', 1.0 * sum(delays) / len(delays)

sys.exit()

filename = trace_file[:trace_file.find('.')] + '_' + str(buffer_size) + '.buffer'
print 'output to', filename

with open(filename, 'w') as of:
    index = 0
    length = len(samples)
    while index < length:
        count = buffer_size
        if index + count > length:
            count = length - index
        of.write(str(count) + '\n')
        for j in range(count):
            of.write(str(samples[index + j]) + '\n')
        index += count
        
