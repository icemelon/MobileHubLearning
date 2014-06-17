#!/usr/bin/env python
import sys
import math

class SensorEvent:
  def __init__(self, values):
    #self.ts = ts
    self.features = {}

    self.features['trigger'] = False
    self.features['x'] = values[0]
    self.features['y'] = values[1]
    self.features['z'] = values[2]
    self.features['mag'] = math.sqrt(values[0]**2+values[1]**2+values[2]**2)
    self.features['trigger'] = values[3]

def load_data(filename):
  global g_events
  g_events = []

  # load data
  with open(filename) as f:
    for line in f:
      data = [eval(x) for x in line.split(',')]
      e = SensorEvent(data[1:])
      g_events.append(e)

def extract_features(events):

  def index_since_trigger_feature(i):
    key = 'index_since_last_tigger'
    if events[i].features['trigger']:
      events[i].features[key] = 0
    else:
      if i == 0:
        events[i].features[key] = '?'
      else:
        if events[i-1].features[key] == '?':
          events[i].features[key] = '?'
        else:
          events[i].features[key] = events[i-1].features[key] + 1

  def diff_feature(i, basis):
  #basis = ['x', 'y', 'z', 'mag']
    for base in basis:
      key = 'd%s' % (base)
      if i == 0:
        events[i].features[key] = '?'
      else:
        events[i].features[key] = events[i].features[base] - events[i-1].features[base]

  def max_min_feature(i, basis, history):
    #basis = ['x', 'y', 'z', 'mag'(,'dx', 'dy', 'dz', 'dmag')]
    for base in basis:
      for his in history:
        min_key = '%s_min_%s' % (base, his)
        max_key = '%s_max_%s' % (base, his)
        diff_key = '%s_max_min_diff_%s' % (base, his)
        mean_key = '%s_mean_%s' % (base, his)
        if i < his-1:
          min_val = max_val = diff_val = mean_val = '?'
        else:
          min_val = min([events[j].features[base] for j in range(i-his+1, i+1)])
          max_val = max([events[j].features[base] for j in range(i-his+1, i+1)])
          diff_val = max_val - min_val
          mean_val = sum([events[j].features[base] for j in range(i-his+1, i+1)]) / his
          
        events[i].features[min_key] = min_val
        events[i].features[max_key] = max_val
        events[i].features[diff_key] = diff_val
        events[i].features[mean_key] = mean_val

  def peak_feature(i, basis):
    for base in basis:
      index_key = '%s_index_since_last_peak' % base
      peak_key = '%s_last_peak' % base
      peak_diff_key = '%s_last_peak_diff' % base
      peak2_key = '%s_last_peak2' % base
      peak2_diff_key = '%s_last_peak2_diff' % base
      diff_key = '%s_last_two_peaks_diff' % base
      if i < 2:
        index_val = peak_val = peak_diff_val = '?'
        peak2_val = peak2_diff_val = diff_val = '?'
      else:
        index_val = '?'
        peak_val = '?'
        peak_diff_val = '?'
        peak2_val = '?'
        peak2_diff_val = '?'
        diff_val = '?'
        if events[i-1].features[base] >= events[i].features[base] and \
          events[i-1].features[base] >= events[i-2].features[base]:
          index_val = 1
        elif events[i-1].features[base] <= events[i].features[base] and \
          events[i-1].features[base] <= events[i-2].features[base]:
          index_val = 1
        else:
          if events[i-1].features[index_key] != '?':
            index_val = 1 + events[i-1].features[index_key]

        if index_val != '?':
          peak = events[i-index_val]
          peak_val = peak.features[base]
          peak_diff_val = abs(events[i].features[base] - peak_val)
          index2 = peak.features[index_key]
          if index2 != '?':
            peak2 = events[i-index_val-index2]
            peak2_val = peak2.features[base]
            peak2_diff_val = abs(events[i].features[base] - peak2_val)
            diff_val = abs(peak_val - peak2_val)

      events[i].features[index_key] = index_val
      events[i].features[peak_key] = peak_val
      events[i].features[peak_diff_key] = peak_diff_val
      events[i].features[peak2_key] = peak2_val
      events[i].features[peak2_diff_key] = peak2_diff_val
      events[i].features[diff_key] = diff_val

  basis = ('x', 'y', 'z', 'mag')
  history = (3, 5, 10, 20)
  for index in range(len(events)):
    #index_since_trigger_feature(index)
    diff_feature(index, basis)
    max_min_feature(index, basis, history)
    peak_feature(index, basis)

def output_schema(of, features, exclude=None):
  of.write('@RELATION pedometer\n')
  of.write('@ATTRIBUTE trigger {TRUE, FALSE}\n')

  if exclude == None:
    exclude = ['trigger']
  else:
    exclude.append('trigger')

  for key in sorted(features.iterkeys()):
    if key not in exclude:
      of.write('@ATTRIBUTE %s NUMERIC\n' % key)
    
  of.write('@data\n')

def output_single_event(of, event, exclude=None):

  if event.features['trigger']:
    of.write('TRUE')
  else:
    of.write('FALSE')

  if exclude == None:
    exclude = ['trigger']
  else:
    exclude.append('trigger')

  for key in sorted(event.features.iterkeys()):
    if key not in exclude:
      of.write(',%s' % event.features[key])  
  of.write('\n')

def check_event(event):
  # check if every feature have values
  valid = True
  for key in event.features.keys():
    if event.features[key] == '?':
      valid = False
      break
  return valid

def output_features(events, filename):
  
  extract_features(events)

  of = open(filename, 'w')
  left = 0
  right = len(events)
  while (True):
    if check_event(events[left]):
      break
    else:
      left += 1

  # output data schema
  output_schema(of, events[left].features)

  # output data
  for i in range(left, right):
    output_single_event(of, events[i])

def output_training(events):
  trigger_list = []
  for i in range(len(events)):
    if events[i].features['trigger']:
      trigger_list.append(i)

  for i in trigger_list:
      for j in range(int(WINDOW_SIZE)):
        events[i-j].features['trigger'] = True
        events[i+j].features['trigger'] = True

  print 'output to training.arff'
  output_features(events, 'training.arff')

def output_testing(events):
  print 'output to testing.arff'
  output_features(events, 'testing.arff')


if __name__ == '__main__':
  args = sys.argv[1:]
  if len(args) < 3:
    print sys.argv[0], '<input csv> <window size> <train/test>'
    sys.exit()

  input_file = args[0]
  global WINDOW_SIZE
  WINDOW_SIZE = eval(args[1])

  load_data(input_file)

  if args[2] == 'train':
    output_training(g_events)
  elif args[2] == 'test':
    output_testing(g_events)