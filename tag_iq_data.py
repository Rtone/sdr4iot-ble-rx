#!/usr/bin/python -u
# -*- coding: utf-8 -*-

import csv
import datetime
from datetime import datetime, timedelta
from optparse import OptionGroup, OptionParser
import numpy as np


# Calculate delay from reference date time
def delay_useconds(ref_time_obj, target_time_obj):
    diff_timestamp_obj = target_time_obj - ref_time_obj
    diff_useconds = diff_timestamp_obj.seconds * \
        1e6 + diff_timestamp_obj.microseconds
    return diff_useconds

# Linearly interpolate position of robots in function of time
def interpolate_position(robot_node, delay_packet_timestamp_useconds, dict_robot_pos):
    robot_location = []
    all_timestamps_sorted = sorted(dict_robot_pos.keys())
    x_interval_timestamp = [int(dict_robot_pos[x][0])
                            for x in all_timestamps_sorted]
    y_interval_timestamp = [int(dict_robot_pos[y][1])
                            for y in all_timestamps_sorted]
    estimated_x = np.interp(
        delay_packet_timestamp_useconds, all_timestamps_sorted, x_interval_timestamp)
    estimated_y = np.interp(
        delay_packet_timestamp_useconds, all_timestamps_sorted, y_interval_timestamp)
    robot_location = [robot_node, int(estimated_x), int(estimated_y)]
    return robot_location

# Estimate the position of a robot in function of timestamp
def estimate_robot_position(packet_timestamp, robot_timestamp_file):
    dict_robot_pos = {}
    packet_timestamp_obj = datetime.strptime(
        packet_timestamp, '%Y-%m-%d %H:%M:%S.%f')
    ref_date_obj = datetime(
        packet_timestamp_obj.year, packet_timestamp_obj.month, packet_timestamp_obj.day, 0, 0, 0, 0)
    delay_packet_timestamp_useconds = delay_useconds(
        ref_date_obj, packet_timestamp_obj)
    with open(robot_timestamp_file) as csvfile:
        reader_robot_info = csv.DictReader(csvfile)
        for row in reader_robot_info:
            robot_timestamp_obj = datetime.strptime(
                row['Time'], '%Y-%m-%d %H:%M:%S.%f')
            delay_robot_timestamp_useconds = delay_useconds(
                ref_date_obj, robot_timestamp_obj)
            dict_robot_pos[delay_robot_timestamp_useconds] = [
                row['X'], row['Y']]
            robot_node = row['Robot_node']
    estimated_position = interpolate_position(robot_node,
                                              delay_packet_timestamp_useconds, dict_robot_pos)
    return estimated_position

# Add a tag (robot_node,X,Y) to packets
def tag_iq_data(robot_csvfile, packet_csvfile, tag_csvfile):
    """
     Parameters:
            robot_csvfile       --- csv file path for the robot information where are recorded: #Time,Robot_node,X,Y,Angle
            packet_csvfile      --- csv file path for  packet information where are recorded: #Time,X,Y,Angle,Start_trame,End_trame,Channel_frequency,Sample_rate
            tag_csvfile         --- csv file path for  packet and robot information where will be recorded: #Time,Angle,Start_trame,End_trame,Channel_frequency,Sample_rate,Robot_node,X,Y
    """

    with open(packet_csvfile) as csvfile:
        reader_packet_info = csv.DictReader(csvfile)
        for row in reader_packet_info:
            new_row = row
            packet_timestamp = row['Time']
            estimated_position = estimate_robot_position(
                packet_timestamp, robot_csvfile)
            new_row['Robot_node'] = estimated_position[0]  # add robot node
            new_row['X'] = estimated_position[1]  # add 'X' value
            new_row['Y'] = estimated_position[2]  # add 'Y' value
            with open(tag_csvfile, 'a+') as csvfile:
                fieldnames = ['Time', 'Start_trame',
                              'End_trame', 'Channel_frequency', 'Sample_rate', 'Robot_node', 'X', 'Y']

                writer = csv.DictWriter(csvfile,  fieldnames=fieldnames)
                writer.writerow(new_row)
    print('Information about tagged packets are recorded into:', tag_csvfile)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-r", "--robotcsv-file", type="string", default='',
                      help="csv file path where are recorded: #Timestamp,Robot_node,X,Y,Angle")
    parser.add_option("-p", "--packetcsv-file", type="string", default='',
                      help="csv file path where are recorded: #time,start_frame,end_frame, frequency, sample_rate")
    parser.add_option("-o", "--outputcsv-file", type="string", default='',
                      help="csv file path which will be used to tag BLE packet information: #time,start_frame,end_frame, frequency, sample_rate,Robot_node,X,Y")
    (opts, _) = parser.parse_args()
    with open(opts.outputcsv_file, 'w') as csvfile:
        fieldnames = ['Time', 'Start_trame',
                      'End_trame', 'Channel_frequency', 'Sample_rate', 'Robot_node', 'X', 'Y']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
    tag_iq_data(opts.robotcsv_file, opts.packetcsv_file, opts.outputcsv_file)
