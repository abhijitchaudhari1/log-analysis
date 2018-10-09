import yaml
import re
import getopt
import sys
import os
import time
from dateutil.parser import parse
import operator
import datetime
import signal

def signal_handler(sig, frame):
  with open('.' + logfile + '.pos', 'w') as filehe:
    filehe.write(str(last_pos))
    sys.exit(1)


signal.signal(signal.SIGINT, signal_handler)





compiled_regex = re.compile(r'(?i)^(?P<date>\d+(-|/)\d+(-|/)\d+)\s(?P<time>\d+:\d+:\d+(\.\d+)?)\s\[PID\s(?P<pid>\d+)\]\s\[(?P<res_time>\d+)ms\]\s\[UID\s(?P<user_id>\w+)\]\s\[(?P<log_level>\w+)\]\s(?P<uri>/\w+)\s(?P<message>.*$)')
ops = {
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "==": operator.eq
      }

try:
   opts, args = getopt.getopt(sys.argv[1:], 'c:f:', ['config=','file='])
except getopt.GetoptError:
   print("Invalid opts")
   sys.exit(2)

for opt, arg in opts:
  if opt in ('-c', '--config'):
    if not os.path.isfile(arg):
      print("config file not present or accesible")
      sys.exit(1)
    with open(arg) as config_file:
      config = yaml.safe_load(config_file)
  elif opt in ('-f', '--file'):
    if not os.path.isfile(arg):
      print("logfile does not exists")
      sys.exit(1)
    logfile = arg

with open(logfile)  as logfileh:
  if os.path.isfile('.' + logfile + '.pos'):
    with open('.' + logfile + '.pos') as posobject:
      last_pos = int(posobject.read())
      logfileh.seek(last_pos)
  error_epoch_array = []
  while True:
    new_line = logfileh.readline()
    if new_line:
      search_r = compiled_regex.search(new_line)
      if bool(search_r):
        gd = search_r.groupdict()
        gd['datetime'] = parse(gd['date'] + ' ' + gd['time'])
        del([gd['date'],gd['time']])
        gd['pid'] = int(gd['pid'])
        gd['res_time'] = int(gd['res_time'])
        for rule in config['rules']:
          if config['rules'][rule]['parameter'] == 'res_time':
            op_func = ops[config['rules'][rule]['operator']]
            if config['rules'][rule].has_key('start_time') and config['rules'][rule]['start_time'] != -1 and gd['datetime'] > config['rules'][rule]['start_time'] + datetime.timedelta(seconds=config['rules'][rule]['interval']):
              print("Rule: " + rule + " breach")
              #print(config['rules'][rule]['start_time'])
              config['rules'][rule]['start_time'] = -1
            # if config['rules'][rule].has_key('start_time') and config['rules'][rule]['start_time'] != -1 and config['rules'][rule]['start_time'] > gd['datetime']:
            #   print("Out of order log discarded")
            # else:
            if op_func(gd['res_time'], config['rules'][rule]['threshold']):
              if (not config['rules'][rule].has_key('start_time')) or (config['rules'][rule].has_key('start_time') and config['rules'][rule]['start_time'] == -1):
                config['rules'][rule]['start_time'] = gd['datetime']
              if config['rules'][rule]['start_time'] > gd['datetime'] and (config['rules'][rule].has_key('last_low_time') and gd['datetime'] > config['rules'][rule]['last_low_time']):
                config['rules'][rule]['start_time'] = gd['datetime']

            else:
              config['rules'][rule]['start_time'] = -1
              config['rules'][rule]['last_low_time'] = gd['datetime']
          elif config['rules'][rule]['parameter'] == 'error_count':
            if 'ERROR' in gd['log_level']:
              op_func = ops[config['rules'][rule]['operator']]
              error_epoch_array.append(int(gd['datetime'].strftime("%s")))
              error_epoch_array.sort()
              error_epoch_array = [s for s in error_epoch_array if s >= (error_epoch_array[-1] - config['rules'][rule]['interval'])]
              if op_func(len(error_epoch_array),config['rules'][rule]['threshold']):
                print("Rule: " + rule + " breach")
                # print(error_epoch_array)
                error_epoch_array = []
          else:
            print("unsupported parameter")
            sys.exit(1)
      else:
        print("parse fail")
      last_pos = logfileh.tell()
    else:
      time.sleep(0.5)


