#!/usr/bin/env python

import sys
import os
import subprocess
import math

"""
argv = sys.argv
if len(argv) < 1:
    print sys.argv[0], '<training data> [testing data]'
"""

class Record:
    def __init__(self):
        self.trigger = None
        self.send = None
        self.state = None
        self.predicted = None
        #self.probability = None
        self.delayed = False
        self.delayed_num = None
        self.wasted = False

    def __str__(self):
        s = str(self.trigger) + '\t' \
            + str(self.send) + '\t' \
            + str(self.predicted) + '\t'

        if self.trigger:
            s += str(self.delayed_num)
        if self.delayed:
            s += '*'
        if self.send and self.wasted:
            s += '#'
        return s

class Predictor:
    def __init__(self, window):
        self.win = window
        self.records = []
        self.state = 2 # 0: idle, 1: transit, 2: active
        self.false_cnt = 0 # continuous false count
        self.buffer = 0

    def predict(self, line):
        data = line.split()

        # update state: increase buffer size, update state
        self.buffer += 1
        if 'FALSE' in data[2]:
            predicted = False
            self.false_cnt += 1
            if self.false_cnt >= self.win:
                self.false_cnt = 0
                if self.state == 2:
                    self.state = 1
                elif self.state == 1:
                    self.state = 0
        else:
            predicted = True
            self.false_cnt = 0
            self.state = 2

        # now decide if we need to send back the buffer
        send = False
        if self.state != 0 and self.buffer >= self.win:
            send = True
            self.buffer = 0

        rec = Record()
        rec.trigger = 'TRUE' in data[1]
        rec.send = send
        rec.state = self.state
        rec.predicted = predicted

        self.records.append(rec)

    def report(self, filename):

        
        of = open(filename, 'w')

        trigger_cnt = 0
        delay_list = []
        delayed_triggers = 0
        for i in range(len(self.records)):
            if self.records[i].trigger:
                trigger_cnt += 1
                j = i
                while j < len(self.records):
                    if self.records[j].send:
                        break
                    j += 1
                
                self.records[i].delayed_num = j - i
                delay_list.append(j-i)

                if j - i > self.win:
                    self.records[i].delayed = True
                    delayed_triggers += 1
        
        if len(delay_list) > 0:
            avg = 1.0 * sum(delay_list) / len(delay_list)
        else:
            avg = 0
        delay_list = sorted(delay_list)
        delay95 = delay_list[int(len(delay_list) * 0.95)]


        send_list = []
        waste_cnt = 0
        buffer_size_list = []
        for i in range(len(self.records)):
            if self.records[i].send:
                send_list.append(i)
        for i in range(len(send_list)):
            if i == 0:
                left = 0
            else:
                left = send_list[i-1]+1
            right = send_list[i]
            buffer_size_list.append(right-left+1)
            wasted = True
            for j in range(left, right+1):
                if self.records[j].trigger:
                    wasted = False
                    break
            if wasted:
                self.records[right].wasted = True
                waste_cnt += 1

        avg_buffer_size = 1.0 * sum(buffer_size_list) / len(buffer_size_list)
        max_buffer_size = max(buffer_size_list)

        of.write('Window size %d\n' % WINDOW_SIZE)
        of.write('Delayed trigger: %s/%s(%.2f%%)\n' % (delayed_triggers, trigger_cnt, 100.0*delayed_triggers/trigger_cnt))
        of.write('Average delayed samples %.1f\n' % avg)
        of.write('Maximum delayed samples %d\n' % max(delay_list))
        of.write('95%% max delayed sample %d\n' % delay95)
        of.write('Waste sending buffer: %s/%s(%.2f%%)\n' % (waste_cnt, len(send_list), 100.0*waste_cnt/len(send_list)))
        of.write('Average buffer size: %.1f\n' % avg_buffer_size)
        of.write('Maximum buffer size: %d\n' % max_buffer_size)
        of.write('---------------------------------------------\n')
        of.write('trigger\tsend\tpredicted\tdelay/wasted\n')
        for rec in self.records:
            of.write(rec.__str__() + '\n')
        print 'output to', filename
        #for i in range(len(self.records)):


def run_randomforest(numTrees):
    #filename = 'cost_%s_c_%s.txt' % (cost, C)
    #of = open(filename, 'w')
    #proc = subprocess.Popen('java -cp weka.jar weka.Run weka.classifiers.meta.CostSensitiveClassifier -cost-matrix "[0.0 %s; 1.0 0.0]" -S 1 -t training.arff -T testing.arff -c first -p 0 -W weka.classifiers.functions.LibLINEAR -- -S 1 -C %s -E 0.01 -B 1.0' % (cost, C),
    #    shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    filename = 'randforest_%s.txt' % numTrees
    proc = subprocess.Popen('java -cp weka.jar weka.Run weka.classifiers.trees.RandomForest -t training.arff -T testing.arff -c first -p 0 -I %s -K 0 -S 1 -num-slots 1' % numTrees,
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    predictor = Predictor(WINDOW_SIZE)

    for line in proc.stdout.readlines():
        line = line.strip()
        #print line
        if line and line[0].isdigit():
            predictor.predict(line)

    retval = proc.wait()
    predictor.report(filename)

def run_svm(Cost):
    filename = 'svm_cost_%s.txt' % (Cost)
    proc = subprocess.Popen('java -cp weka.jar weka.Run weka.classifiers.meta.CostSensitiveClassifier -cost-matrix "[0.0 %s; 1.0 0.0]" -S 1 -t training.arff -T testing.arff -c first -p 0 -W weka.classifiers.functions.LibLINEAR -- -S 1 -C %s -E 0.01 -B 1.0' % (1, Cost),
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    predictor = Predictor(WINDOW_SIZE)

    for line in proc.stdout.readlines():
        line = line.strip()
        #print line
        if line and line[0].isdigit():
            predictor.predict(line)

    retval = proc.wait()
    predictor.report(filename)

if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 1:
        print sys.argv[0], '<window size>'
        exit()

    if not os.path.exists('training.arff'):
        print 'Cannot find training.arff'
        exit()
    if not os.path.exists('testing.arff'):
        print 'Cannot find testing.arff'
        exit()

    global WINDOW_SIZE
    WINDOW_SIZE = eval(args[0])

    run_randomforest(7)
    sys.exit()


    numTrees_list = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    for num in numTrees_list:
        run_randomforest(num)

