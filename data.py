#!/usr/bin/env python
import sys
import numpy

if __name__ == '__main__':
  
  argv = sys.argv[1:]
  if len(argv) < 2:
    print sys.argv[0] + ' <sensor data> <taint log>'
    sys.exit()

  file1 = argv[0]
  file2 = argv[1]
  #update_str = '[color]'
  eventlogs = ['[TextView]', '[color]', '[Canvas]']
  #update_str = "[Canvas]"

  values = []
  with open(file1) as f:
    for line in f:
      record = {'value': line.strip(), 'trigger': False}
      values.append(record)

  csvfile = file2[:file2.find('.')] + '.csv'
  gapfile = file2[:file2.find('.')] + '.gap'

  valid_values = []
  gaps = []

  with open(file2) as f:
    count = 0
    gap = 0
    for line in f:
      if '[App]' in line:
        _ = line[line.find('0x'):]
        index = int(_, 16)
        valid_values.append(values[index-1])
        count += 1
        gap += 1
      else:
        event = False
        for s in eventlogs:
          if s in line:
            event = True
            break
        if event:
          if gap > 1:
            # if there is only 1 sensor data between two events, consider they happen at the same time
            gaps.append(count)
            count = 0
            valid_values[-1]['trigger'] = True
          gap = 0
  
  with open(csvfile, 'w') as of:
    print 'output label data to', csvfile
    for record in valid_values:
      of.write(record['value']+','+str(record['trigger'])+'\n')

  with open(gapfile, 'w') as of:
    print 'output gap to', gapfile
    for i in gaps:
      of.write('%d\n' % i)

  print 'window size = %d' % numpy.median(gaps)