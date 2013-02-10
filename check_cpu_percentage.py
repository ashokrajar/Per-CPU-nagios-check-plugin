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

import sys
import time
from optparse import OptionParser


###  Global Identifiers  ###

# Mapping of CPU stat values to their 'meaning'
cpu_stat_var_array = ('user', 'nice', 'system', 'idle', 'iowait', 'irq', 'softirq', 'steal_time') 

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
cmd_parser.add_option("-d", "--debug", 
                      action="store_true", dest="debug", 
                      default=False, help="enable debug")

(cmd_options, cmd_args) = cmd_parser.parse_args()

# Bounds Checking
if not (cmd_options.cpu_name and cmd_options.warning_percent and cmd_options.critical_percent):
    cmd_parser.print_help()
    sys.exit(3)
elif (cmd_options.warning_percent > 100 or cmd_options.critical_percent > 100):
    print 'ERROR: Percentages must be less than 100'
    cmd_parser.print_help()
    sys.exit(3)
elif (cmd_options.warning_percent > cmd_options.critical_percent):
    print 'ERROR: CRITIAL level must be /higher/ than WARNING level'
    cmd_parser.print_help()
    sys.exit(3)

# Collect CPU Statistic Object 
class CollectStat:
    """Object to Collect CPU Statistic Data"""
    def __init__(self,cpu_name):
        
        self.total = 0 
        self.cpu_stat_dict = {}
        
        for line in open("/proc/stat"):
            line = line.strip()
            
            if cmd_options.debug:
                    print "DEBUG LINE:", line 
        
            if line.startswith(cpu_name):
                cpustat=line.split()
                cpustat.pop(0)              # Remove the First collumn of the Line 'cpu'

                # Remove the unwanted data from the array
                # only retain first 8 field on the file
                while len(cpustat) > 8:
                    cpustat.pop()

                if cmd_options.debug:
                    print "DEBUG : cpustat array %s" % cpustat
                        
                cpustat=map(float, cpustat)     # Convert the Array to Float

                for i in range(len(cpustat)):
                    self.cpu_stat_dict[cpu_stat_var_array[i]] = cpustat[i]

                # Calculate the total utilization
                for i in cpustat:
                    self.total += i 

                break

        if cmd_options.debug:
            print "DEBUG : cpu statistic dictionary %s" % self.cpu_stat_dict
            print "DEBUG : total statistics %s" % self.total

# Get Sample CPU Statistics 
initial_stat = CollectStat(cmd_options.cpu_name)
time.sleep(cmd_options.sleep_time)
final_stat = CollectStat(cmd_options.cpu_name)

cpu_total_stat = final_stat.total - initial_stat.total

if cmd_options.debug:
    print "DEBUG : diff total stat %f" % cpu_total_stat

for cpu_stat_var,cpu_stat in final_stat.cpu_stat_dict.items():
    globals()['cpu_%s_usage_percent' % cpu_stat_var] = ((final_stat.cpu_stat_dict[cpu_stat_var] - initial_stat.cpu_stat_dict[cpu_stat_var])/cpu_total_stat)*100  

cpu_usage_percent = cpu_user_usage_percent + cpu_nice_usage_percent + cpu_system_usage_percent + cpu_iowait_usage_percent + cpu_irq_usage_percent + cpu_softirq_usage_percent + cpu_steal_time_usage_percent

# Check if CPU Usage is Critical/Warning/OK
if cpu_usage_percent >= cmd_options.critical_percent:
    print cmd_options.cpu_name,
    print 'STATISTICS CRITICAL : total=%.2f%% user=%.2f%% system=%.2f%% iowait=%.2f%% steal=%.2f%% | user=%.2f system=%.2f iowait=%.2f steal=%.2f warn=%d crit=%d' % (
        cpu_usage_percent,
        cpu_user_usage_percent, 
        cpu_system_usage_percent, 
        cpu_iowait_usage_percent, 
        cpu_steal_time_usage_percent, 
        cpu_user_usage_percent, 
        cpu_system_usage_percent, 
        cpu_iowait_usage_percent, 
        cpu_steal_time_usage_percent, 
        cmd_options.warning_percent, 
        cmd_options.critical_percent)
    sys.exit(2)

elif  cpu_usage_percent >= cmd_options.warning_percent:
    print cmd_options.cpu_name,
    print 'STATISTICS WARNING : total=%.2f%% user=%.2f%% system=%.2f%% iowait=%.2f%% steal=%.2f%% | user=%.2f system=%.2f iowait=%.2f steal=%.2f warn=%d crit=%d' % (
        cpu_usage_percent,
        cpu_user_usage_percent, 
        cpu_system_usage_percent, 
        cpu_iowait_usage_percent, 
        cpu_steal_time_usage_percent, 
        cpu_user_usage_percent, 
        cpu_system_usage_percent, 
        cpu_iowait_usage_percent, 
        cpu_steal_time_usage_percent, 
        cmd_options.warning_percent, 
        cmd_options.critical_percent)
    sys.exit(1)

else:
    print cmd_options.cpu_name,
    print 'STATISTICS OK : total=%.2f%% user=%.2f%% system=%.2f%% iowait=%.2f%% steal=%.2f%% | user=%.2f system=%.2f iowait=%.2f steal=%.2f warn=%d crit=%d' % (
        cpu_usage_percent,
        cpu_user_usage_percent, 
        cpu_system_usage_percent, 
        cpu_iowait_usage_percent, 
        cpu_steal_time_usage_percent, 
        cpu_user_usage_percent, 
        cpu_system_usage_percent, 
        cpu_iowait_usage_percent, 
        cpu_steal_time_usage_percent, 
        cmd_options.warning_percent, 
        cmd_options.critical_percent)
    sys.exit(0)
