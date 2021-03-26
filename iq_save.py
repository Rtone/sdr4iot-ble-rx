#!/usr/bin/python -u
# -*- coding: utf-8 -*-


import csv
import os
from optparse import OptionGroup, OptionParser
import numpy as np


# Extract BLE IQ data and save it  into a .sigmf-data
def iq_save(csv_file, iq_file):
    """
     Parameters:
            csv-file    --- csv file path where are recorded: #Time,Robot_Number,X,Y,Angle,Start_trame,End_trame,Channel_frequency,Sample_rate
            data-file   --- Sigmf-data file path

    """
    data_file_sigmfdata = iq_file.split('.')[0]+'-BLE_IQ.sigmf-data'
    base_data = os.path.dirname(data_file_sigmfdata)
    if not os.path.exists(base_data):
        os.makedirs(base_data)
    with open(data_file_sigmfdata, 'a+') as data_to_file:    
        with open(csv_file) as csvfile:
            reader_csv = csv.DictReader(csvfile)
            for row in reader_csv:
                print(row)
                start_frame = int(row['Start_trame'])
                end_frame = int(row['End_trame'])
                iq_data = np.memmap(iq_file, dtype=np.complex64, mode='r',
                                offset=start_frame, shape=end_frame-start_frame)
                data_to_file.write(iq_data.tobytes())
    print('BLE IQ data are extracted and saved into:', data_file_sigmfdata)
    print('Run sigmf_recording.py with extracted BLE data file to get a sigmf archive')


if __name__ == '__main__':
    parser = OptionParser()
    #csv and data file path
    parser.add_option("-c", "--csv-file", type="string", default='',
                     help="csv file path where are recorded: #time,start_trame,endtrame,frequency,sample_rate")
    parser.add_option("-d", "--data-file", type="string", default='',
                     help="IQ file path to be used to extract BLE IQ data")
    (opts, _) = parser.parse_args()
    iq_save(opts.csv_file, opts.data_file)
