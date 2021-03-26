#!/usr/bin/python -u

import csv
import urllib2
from datetime import datetime, timedelta
from optparse import OptionGroup, OptionParser

# Get BLE emitter positions
def get_robot_position(robot_node, robot_csv_file):
    """
     Parameters:
            robot_node        --- target robot node which will  be tracked
            robot_csv_file    --- csv file path where robot information will be recorded: #Time,Robot_Number,X,Y,Angle
    """

    timestamp = datetime.now()
    if int(robot_node) == int(0) :
            location = [0,0,0]
    else:
            robot_num = '  '+':id: '+str(robot_node)
            position = urllib2.urlopen(
                'http://robotcontrol.wilab2.ilabt.iminds.be:5056/Robot/LocationsYaml')
            read_position = position.read()
            extract_information = read_position.split('\n')
            robot_information_index = extract_information.index(robot_num)
            location = [extract_information[robot_information_index+1][6:],
                        extract_information[robot_information_index+2][6:],
                        extract_information[robot_information_index+6][10:]]
    
    with open(robot_csv_file, 'a+') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([timestamp, robot_node, location[0],
                         location[1], location[2]])
  

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-r", "--robot-node", type="int", default=5,
                      help="Robot node corresponding to the  BLE emitter [default=%default]")
    parser.add_option("-o", "--csv-file", type="string", default='',
                      help="csv file path where will be recorded: #Timestamp,Robot_node,X,Y,Angle")
    (opts, _) = parser.parse_args()
    with open(opts.csv_file, 'w') as csvfile:
        fieldnames = ['Time', 'Robot_node', 'X', 'Y', 'Angle']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
    try:
        while True:
            get_robot_position(opts.robot_node, opts.csv_file)
    except KeyboardInterrupt:
        print("Finished recording...")
        pass
