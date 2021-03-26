#!/usr/bin/python3 -u

import csv
from optparse import OptionGroup, OptionParser
import sigmf
from sigmf import sigmffile, utils
from sigmf.sigmffile import SigMFFile, fromarchive

# SigMF fields for global info
global_info = {
    'core:datatype': 'cf32',
    'core:version': '0.0.1',
    'core:description': 'Metadafile for a SigMF recording of BLE Advertising packets.'
}

# Add Capture settings to SigMfile


def add_capture(sigmf_file, start_frame, sample_rate, frequency):
    capture_md = {
        "core:sampling_rate": int(sample_rate),
        "core:frequency": int(frequency),
        "core:time": utils.get_sigmf_iso8601_datetime_now()
    }
    sigmf_file.add_capture(start_frame, capture_md)

# Add robot positions x(latitude), y(longitude)  to SigMfile


def add_annotation(sigmf_file, start_frame, end_frame, latitude, longitude, robot_num):
    comment = 'Robot#%d positions at the detection of the BLE Packet' % robot_num
    annotation_md = {
        "core:latitude": int(latitude),
        "core:longitude": int(longitude),
        "core:comment": comment
    }
    sigmf_file.add_annotation(
        start_frame, end_frame-start_frame, annotation_md)

# Save Recordings into SigMF format


def sigmf_recording(csv_file, data_file):
    """
     Parameters:
            csv_file    --- csv file path where are recorded: #Time,Robot_Number,X,Y,Angle,Start_trame,End_trame,Channel_frequency,Sample_rate
            data_file   --- Sigmf-data file path

    """
    # Initialize SigMF file
    sigmf_file = SigMFFile(data_file=data_file, global_info=global_info)
    # Define archive name for SigMF data and metadata files
    archive_name = csv_file.split('.')[0]
    with open(csv_file) as csvfile:
        reader_csv = csv.DictReader(csvfile)
        offset = 0
        for row in reader_csv:
            sample_rate = int(row['Sample_rate'])
            len_packet = int(row['End_trame'])-int(row['Start_trame'])
            frequency = int(row['Channel_frequency'])
            robot_node = int(row['Robot_node'])
            latitude = int(row['X'])
            longitude = int(row['Y'])
            start_frame = offset
            end_frame = offset+len_packet
            add_capture(sigmf_file, start_frame, sample_rate, frequency)
            add_annotation(sigmf_file, start_frame, end_frame,
                           latitude, longitude, robot_node)
            offset += len_packet
    # Dump contents to SigMF archive format
    archive_path = sigmf_file.archive(archive_name)
    return archive_path


if __name__ == '__main__':
    parser = OptionParser()
    # csv and data file path
    parser.add_option("-c", "--csv-file", type="string", default='',
                      help="csv file path where are recorded: #time,start_frame,end_frame, frequency, sample_rate,robot node,x,y")
    parser.add_option("-d", "--data-file", type="string",
                      default='', help="BLE IQ Sigmf-data file path")
    (opts, _) = parser.parse_args()
    archive_path = sigmf_recording(opts.csv_file, opts.data_file)
    print('The archive path containing sigmf-data and sigmg-meta file is:', archive_path)
