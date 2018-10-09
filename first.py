from dateutil.parser import parse
import datetime
import sys
import os
import numpy as np
import json
import re
import getopt

import pylab as plt

compiled_regex = re.compile(r'(?i)^(?P<date>\d+(-|/)\d+(-|/)\d+)\s(?P<time>\d+:\d+:\d+(\.\d+)?)\s\[PID\s(?P<pid>\d+)\]\s\[(?P<res_time>\d+)ms\]\s\[UID\s(?P<user_id>\w+)\]\s\[(?P<log_level>\w+)\]\s(?P<uri>/\w+)\s(?P<message>.*$)')

try:
   opts, args = getopt.getopt(sys.argv[1:], 's:e:f:', ['start=', 'end=', 'file='])
except getopt.GetoptError:
   print("Invalid opts")
   sys.exit(2)

for opt, arg in opts:
  if opt in ('-s', '--start'):
    try:
      int(arg)
      if int(arg) < 0:
        start_date = datetime.datetime.now() - datetime.timedelta(seconds=abs(int(arg)))
      else:
        print("Invalid start date, possible values [-10, '2018-08-30 17:12:19.846066']")
        sys.exit(2)
    except ValueError:
      if len(arg) == 26:
        start_date = parse(arg)
      else:
        print("Invalid start date, possible values [-20, '2018-08-30 17:12:19.846066']")
        sys.exit(2)
  elif opt in ('-e', '--end'):
    try:
      int(arg)
      if int(arg) <= 0:
        end_date = datetime.datetime.now() - datetime.timedelta(seconds=abs(int(arg)))
      else:
        print("Invalid end date, possible values [-30, '2018-08-30 17:12:19.846066']")
        sys.exit(2)
    except ValueError:
      if len(arg) == 26:
        end_date = parse(arg)
      else:
        print("Invalid end date, possible values [-40, '2018-08-30 17:12:19.846066']")
  elif opt in ('-f', '--file'):
    if os.path.isfile(arg):
      logfile = arg
    else:
      print("logfile does not exits")
      sys.exit(2)

#print(start_date)
#print(end_date)
#print(logfile)

if not end_date >= start_date:
  print("start_date cannot be after end date")
  sys.exit(1)



#response_times = []
response_times_re = []
error_hash = {}
with open(logfile) as infile:
  for line in infile:
    #if 'Everything looks good' in line:
    search_r = compiled_regex.search(line)
    if bool(search_r):
      gd = search_r.groupdict()
      gd['datetime'] = parse(gd['date'] + ' ' + gd['time'])
      del([gd['date'],gd['time']])
      gd['res_time'] = int(gd['res_time'])
      if gd['datetime'] >= start_date and gd['datetime'] <= end_date:
        if gd['log_level'] != 'ERROR':
          response_times_re.append(int(gd['res_time']))
        else:
          error_name = gd['message'].split()[-1]
          if not error_hash.has_key(error_name):
            error_hash[error_name] = 0
          else:
            error_hash[error_name] = error_hash[error_name] + 1


      #response_times.append(int(line.split('ms]')[0].split('[')[-1]))
find_percentile = [50,90,95]
respose_percentile = {}
# for i in find_percentile:
#   respose_percentile[i] = np.percentile(response_times,i)
# print(json.dumps(respose_percentile,indent=4,sort_keys=True))

for i in find_percentile:
  respose_percentile[i] = np.percentile(response_times_re,i)
print(json.dumps(respose_percentile,indent=4,sort_keys=True))

plt.bar(range(0,len(error_hash.values())), error_hash.values(), align='center')
plt.xticks(range(0,len(error_hash.values())), error_hash.keys())
plt.show()
