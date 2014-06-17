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
    print sys.argv[0], '<app_trace.csv> <prediction result>'
    sys.exit()

trace_file = argv[0]
predict_file = argv[1]

samples = []
with open(trace_file) as file:
    for line in file:
        if line:
            data = [eval(x) for x in line.split(',')]
            e = SensorEvent(data)
            samples.append(e)

buffer_list = []
predict_cnt = 0
with open(predict_file) as file:
    data_begin = False
    buffer_size = 0
    for line in file:
        if data_begin and line:
            predict_cnt += 1
            buffer_size += 1
            data = line.split()
            send = eval(data[1])
            if send:
                buffer_list.append(buffer_size)
                buffer_size = 0
        else:
            if line.startswith('trigger'):
                data_begin = True
if buffer_size > 0:
    buffer_list.append(buffer_size)

offset = len(samples) - predict_cnt
buffer_list[0] += offset

filename = trace_file[:trace_file.find('.')] + '.buffer'
print 'output to', filename

with open(filename, 'w') as of:
    index = 0
    for buffer_size in buffer_list:
        of.write(str(buffer_size) + '\n')
        for _ in range(buffer_size):
            of.write(str(samples[index]) + '\n')
            index += 1
        
