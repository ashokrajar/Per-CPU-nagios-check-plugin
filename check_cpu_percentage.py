#!/usr/bin/env python

'''
Project     :       Per CPU Percentage Check
Version     :       0.2
Author      :       Ashok Raja R <ashokraja.linux@gmail.com>
Summary     :       This program is a nagios plugin that checks Per CPU Utilization in Percentage
Dependency  :       Linux-2.6.18/nagios/Python-2.6

Usage :
```````
shell> python check_cpu_percentage.py -C cpu -w 70 -c 90
'''

import json
import os
import sys
import time
from optparse import OptionParser


###  Global Identifiers  ###

# Mapping of CPU stat values to their 'meaning'
cpu_stat_var_array = ('user', 'nice', 'system', 'idle',
                      'iowait', 'irq', 'softirq', 'steal_time')
# Mapping returncodes to strings
return_strings = ('OK', 'WARNING', 'CRITICAL', 'UNKNOWN')

###   Main code   ###
# Command Line Arguments Parser
cmd_parser = OptionParser(version="%prog 1.1")

cmd_parser.add_option("-C", "--CPU",
                      action="store", type="string",
                      dest="cpu_name",
                      help="CPU to Check",
                      metavar="[cpu | cpu0 | cpu1]",
                      default='cpu')
cmd_parser.add_option("-w", "--warning",
                      type="int", action="store",
                      dest="warning_percent",
                      help="Threshold for WARNING Condition",
                      metavar="WarningPercentage",
                      default=50)
cmd_parser.add_option("-c", "--critical",
                      type="int", action="store",
                      dest="critical_percent",
                      help="Threshold for CRITICAL Condition",
                      metavar="CriticalPercentage",
                      default=75)
cmd_parser.add_option("-s", "--sleep",
                      type="int", action="store",
                      dest="sleep_time",
                      help="Sleep interval between measurements in seconds (default 15)",
                      metavar="SleepTime",
                      default=15)
cmd_parser.add_option("", "--cache",
                      type="string", action="store",
                      dest="cache",
                      default=None, help="Cache file for long time stats (disables sleep)"),
cmd_parser.add_option("-d", "--debug",
                      action="store_true", dest="debug",
                      default=False, help="enable debug")

(cmd_options, cmd_args) = cmd_parser.parse_args()

# Bounds Checking
if not (cmd_options.cpu_name and cmd_options.warning_percent and cmd_options.critical_percent):
    cmd_parser.print_help()
    sys.exit(3)
elif (cmd_options.warning_percent > 100 or cmd_options.critical_percent > 100):
    print('ERROR: Percentages must be less than 100')
    cmd_parser.print_help()
    sys.exit(3)
elif (cmd_options.warning_percent > cmd_options.critical_percent):
    print('ERROR: CRITIAL level must be /higher/ than WARNING level')
    cmd_parser.print_help()
    sys.exit(3)

# Collect CPU Statistic Object
class CollectStat:
    """Object to Collect CPU Statistic Data"""

    def __init__(self, cpu_name):

        self.cpu_stat_dict = {}

        with open("/proc/stat") as statsfile:
            for line in statsfile:

                line = line.strip()

                if cmd_options.debug:
                        print("DEBUG LINE:", line)

                if line.startswith(cpu_name):
                    cpustat = line.split()
                    # Remove the First collumn of the Line 'cpu'
                    cpustat.pop(0)

                    # Remove the unwanted data from the array
                    # only retain first 8 field on the file
                    while len(cpustat) > 8:
                        cpustat.pop()

                    if cmd_options.debug:
                        print("DEBUG : cpustat array %s" % cpustat)

                    # Convert the Array to Float
                    cpustat = list(map(float, cpustat))

                    for i in range(len(cpustat)):
                        self.cpu_stat_dict[cpu_stat_var_array[i]] = cpustat[i]

                    # Calculate the total utilization
                    self.cpu_stat_dict["total"] = 0
                    for i in cpustat:
                        self.cpu_stat_dict["total"] += i

                    break

        if cmd_options.debug:
            print("DEBUG : cpu statistic dictionary %s" % self.cpu_stat_dict)
            print("DEBUG : total statistics %s" % self.cpu_stat_dict["total"])

    def load(self, filename):
        try:
            with open(cmd_options.cache, 'r') as handle:
                self.cpu_stat_dict = json.loads(handle.read())
        except IOError as err:
            print('Could not read "%s" as cache file: %s' % (filename, err))
            sys.exit(3)
        except json.decoder.JSONDecodeError as err:
            print('JSON-Error in "%s": %s' % (filename, err))

    def dump(self, filename):
        try:
            with open(cmd_options.cache, 'w') as handle:
                json.dump(self.cpu_stat_dict, handle)
        except IOError as err:
            print('Could not write "%s" as cache file: %s' % (filename, err))
            sys.exit(3)

# Get Sample CPU Statistics
initial_stat = CollectStat(cmd_options.cpu_name)
# Read cache file
if cmd_options.cache:
    if os.path.islink(cmd_options.cache):
        print('Path "%s" is a link, exiting!' % cmd_options.cache)
        sys.exit(3)
    if os.path.exists(cmd_options.cache):
        if os.path.isfile(cmd_options.cache):
            if os.access(cmd_options.cache, os.W_OK):
                initial_stat.load(cmd_options.cache)
            else:
                print('Could not write "%s" as cache file, exiting!' % cmd_options.cache)
                sys.exit(3)
        else:
                print('Path "%s" is not a file, exiting!' % cmd_options.cache)
                sys.exit(3)
    else:
        initial_stat.dump(cmd_options.cache)
        print('Assuming first cached run - no cache found!')
        sys.exit(3)
else:
    time.sleep(cmd_options.sleep_time)
final_stat = CollectStat(cmd_options.cpu_name)

cpu_total_stat = final_stat.cpu_stat_dict["total"] - initial_stat.cpu_stat_dict["total"]

if cmd_options.debug:
    print("DEBUG : diff total stat %f" % cpu_total_stat)

for cpu_stat_var, cpu_stat in final_stat.cpu_stat_dict.items():
    globals()['cpu_%s_usage_percent' % cpu_stat_var] = (
        (final_stat.cpu_stat_dict[cpu_stat_var] - initial_stat.cpu_stat_dict[cpu_stat_var])/cpu_total_stat)*100

cpu_usage_percent = cpu_user_usage_percent + cpu_nice_usage_percent + cpu_system_usage_percent + \
    cpu_iowait_usage_percent + cpu_irq_usage_percent + \
    cpu_softirq_usage_percent + cpu_steal_time_usage_percent

# Check if CPU Usage is Critical/Warning/OK
if cpu_usage_percent >= cmd_options.critical_percent:
    return_code = 2
elif cpu_usage_percent >= cmd_options.warning_percent:
    return_code = 1
else:
    return_code = 0

# Output
print('CPU STATISTICS %s: total=%.2f%% user=%.2f%% system=%.2f%% iowait=%.2f%% steal=%.2f%% | total=%.2f%%;%d;%d;0;100 user=%.2f%% system=%.2f%% iowait=%.2f%% steal=%.2f%%' % (
    return_strings[return_code],
    cpu_usage_percent,
    cpu_user_usage_percent,
    cpu_system_usage_percent,
    cpu_iowait_usage_percent,
    cpu_steal_time_usage_percent,
    cpu_usage_percent,
    cmd_options.warning_percent,
    cmd_options.critical_percent,
    cpu_user_usage_percent,
    cpu_system_usage_percent,
    cpu_iowait_usage_percent,
    cpu_steal_time_usage_percent,))

# Exit with returncode
sys.exit(return_code)

