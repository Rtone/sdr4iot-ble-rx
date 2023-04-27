#!/usr/bin/python -u
#
#  ble-dump: SDR Bluetooth LE packet dumper
#
#  Copyright (C) 2016 Jan Wagner <mail@jwagner.eu>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#

from __future__ import print_function

import zmq
import numpy as np
import time
import binascii
import csv
import os
from collections import namedtuple
from datetime import datetime, timedelta
from optparse import OptionGroup, OptionParser

from gnuradio.eng_option import eng_option

from grc.gr_ble import gr_ble as gr_block
from proto import *


class Stat(object):
    FIELDS = ['ok', 'err_crc', 'err_len', 'err_pdu', 'err_llid']

    def __init__(self):
        self.reset()

    def dump(self):
        output = ""
        err_total = 0
        for field in self.FIELDS:
            if output:
                output += ", "
            value = getattr(self, field)
            output += "{}:{}".format(field, value)
            if field.startswith('err_'):
                err_total += value
        return output + ", err_total:{}".format(err_total)

    def reset(self):
        for field in self.FIELDS:
            setattr(self, field, 0)

# Print current Gnu Radio capture settings


def print_settings(gr, opts):
    print('\n ble-dump:  SDR Bluetooth LE packet dumper')
    print('\nCapture settings:')
    print(' %-22s: %s Hz' %
          ('Base Frequency', '{:d}'.format(int(gr.get_ble_base_freq()))))
    print(' %-22s: %s Hz' %
          ('Sample rate', '{:d}'.format(int(gr.get_sample_rate()))))
    print(' %-22s: %s dB' % ('Squelch threshold',
                             '{:d}'.format(int(gr.get_squelch_threshold()))))

    print('\nLow-pass filter:')
    print(' %-22s: %s Hz' % ('Cutoff frequency',
                             '{:d}'.format(int(gr.get_cutoff_freq()))))
    print(' %-22s: %s Hz' % ('Transition width',
                             '{:d}'.format(int(gr.get_transition_width()))))

    print('\nGMSK demodulation:')
    print(' %-22s: %s' % ('Samples per Symbol',
                          '{:.4f}'.format(gr.get_gmsk_sps())))
    print(' %-22s: %s' % ('Gain Mu', '{:.4f}'.format(gr.get_gmsk_gain_mu())))
    print(' %-22s: %s' % ('Mu', '{:,}'.format(gr.get_gmsk_mu())))
    print(' %-22s: %s' %
          ('Omega Limit', '{:.4f}'.format(gr.get_gmsk_omega_limit())))

    print('\nBluetooth LE:')
    print(' %-22s: %s' % ('Scanning Channels',
                          '{:s}'.format(opts.current_ble_channels.replace(',', ', '))))
    print(' %-22s: %ss' %
          ('Scanning Window', '{:.2f}'.format(opts.ble_scan_window)))
    print(' %-22s: %s' % ('Disable CRC check', '{0}'.format(opts.disable_crc)))
    print(' %-22s: %s' % ('Disable De-Whitening',
                          '{0}'.format(opts.disable_dewhitening)))

    print('\n%-23s: %s\n' %
          ('PCAP output file', '{:s}'.format(opts.pcap_file)))

# Setup Gnu Radio with defined command line arguments


def init_args(gr, opts):
    gr.set_sample_rate(int(opts.sample_rate))
    gr.set_squelch_threshold(int(opts.squelch_threshold))
    gr.set_cutoff_freq(int(opts.cutoff_freq))
    gr.set_transition_width(int(opts.transition_width))
    gr.set_gmsk_sps(opts.samples_per_symbol)
    gr.set_gmsk_gain_mu(opts.gain_mu)
    gr.set_gmsk_mu(opts.mu)
    gr.set_gmsk_omega_limit(opts.omega_limit)
    gr.set_ble_channel(int(opts.scan_channels[0]))
    gr.set_rf_gain(opts.rf_gain)
    gr.set_iq_output(opts.iq_output)
    gr.set_duration_seconds(opts.duration_seconds)
    gr.set_iq_output(gr.iq_output)

# Initialize command line arguments


def init_opts(gr):
    parser = OptionParser(option_class=eng_option, usage="%prog: [opts]")

    # Capture
    capture = OptionGroup(parser, 'Capture settings')
    capture.add_option("-o", "--pcap_file", type="string",
                       default='', help="PCAP output file or named pipe (FIFO)")
    capture.add_option("-m", "--min_buffer_size", type="int",
                       default=65, help="Minimum buffer size [default=%default]")
    capture.add_option("-s", "--sample-rate", type="eng_float",
                       default=gr.sample_rate, help="Sample rate [default=%default]")
    capture.add_option("-t", "--squelch_threshold", type="eng_float", default=gr.squelch_threshold,
                       help="Squelch threshold (simple squelch) [default=%default]")
    capture.add_option('-g', '--rf-gain', type='int',
                       default=gr.rf_gain, help="Capture duration (seconds) [default=%default]")
    capture.add_option('-l', '--duration_seconds', type='int',
                       default=gr.duration_seconds, help="Capture duration (seconds) [default=%default]")

    # Low Pass filter
    filters = OptionGroup(parser, 'Low-pass filter:')
    filters.add_option("-C", "--cutoff_freq", type="eng_float",
                       default=gr.cutoff_freq, help="Filter cutoff [default=%default]")
    filters.add_option("-T", "--transition_width", type="eng_float",
                       default=gr.transition_width, help="Filter transition width [default=%default]")

    # GMSK demodulation
    gmsk = OptionGroup(parser, 'GMSK demodulation:')
    gmsk.add_option("-S", "--samples_per_symbol", type="eng_float",
                    default=gr.gmsk_sps, help="Samples per symbol [default=%default]")
    gmsk.add_option("-G", "--gain_mu", type="eng_float",
                    default=gr.gmsk_gain_mu, help="Gain mu [default=%default]")
    gmsk.add_option("-M", "--mu", type="eng_float",
                    default=gr.gmsk_mu, help="Mu [default=%default]")
    gmsk.add_option("-O", "--omega_limit", type="eng_float",
                    default=gr.gmsk_omega_limit, help="Omega limit [default=%default]")

    # Bluetooth L
    ble = OptionGroup(parser, 'Bluetooth LE:')
    ble.add_option("-c", "--current_ble_channels", type="string",
                   default='37,38,39', help="BLE channels to scan [default=%default]")
    ble.add_option("-w", "--ble_scan_window", type="eng_float",
                   default=10.24, help="BLE scan window [default=%default]")
    ble.add_option("-x", "--disable_crc", action="store_true",
                   default=False, help="Disable CRC verification [default=%default]")
    ble.add_option("-y", "--disable_dewhitening", action="store_true",
                   default=False, help="Disable De-Whitening [default=%default]")

    # Misc
    misc = OptionGroup(parser, "Misc")
    misc.add_option('-d', '--debug', action='store_true',
                    help="Activate debug (dump wrong packets)")
    misc.add_option('-i', '--iq-output', type='string', default=gr.iq_output,
                    help="Filename for IQ data [default=%default]")

    parser.add_option_group(capture)
    parser.add_option_group(filters)
    parser.add_option_group(gmsk)
    parser.add_option_group(ble)
    parser.add_option_group(misc)
    return parser.parse_args()


if __name__ == '__main__':
    MIN_BUFFER_LEN = 65

    # Initialize Gnu Radio
    gr_block = gr_block()
    gr_block.start()

    # Initialize command line arguments
    (opts, args) = init_opts(gr_block)

    # Initialize CSV file  to record start/end of BLE packets and robot positions
    csv_file = opts.iq_output.split('.')[0]+'.csv'
    base_csv = os.path.dirname(csv_file)
    if not os.path.exists(base_csv):
        os.makedirs(base_csv)
    with open(csv_file, 'w') as csvfile:
        fieldnames = ['Time', 'Start_trame', 'End_trame',
                      'Channel_frequency', 'Sample_rate']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    if not opts.pcap_file:
        print('\nerror: please specify pcap output file (-o)')
        exit(1)

    # Verify BLE channels argument
    if ',' not in opts.current_ble_channels:
        opts.current_ble_channels += ','

    # Prepare BLE channels argument
    opts.scan_channels = [int(x) for x in opts.current_ble_channels.split(',')]

    # Set Gnu Radio opts
    init_args(gr_block, opts)

    # Print capture settings
    print_settings(gr_block, opts)

    # Open PCAP file descriptor
    pcap_fd = open_pcap(opts.pcap_file)

    current_hop = 1
    hopping_time = datetime.now() + timedelta(seconds=opts.ble_scan_window)

    # Set initial BLE channel
    current_ble_chan = opts.scan_channels[0]
    gr_block.set_ble_channel(BLE_CHANS[current_ble_chan])

    # Prepare Gnu Radio receive buffers
    gr_buffer = ''
    lost_data = ''

    print('Capturing on BLE channel [ {:d} ] @ {:d} MHz'.format(
        current_ble_chan, int(gr_block.get_freq() / 1000000)))

    stat = Stat()

    if opts.debug:
        def debug(*args):
            print(*args)
    else:
        def debug(*args):
            pass
    global_buffer_len = 0
    lost_data_len = 0

    # ZMQ
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://127.0.0.1:55555") # connect, not bind, the PUB will bind, only 1 can bind
    socket.setsockopt(zmq.SUBSCRIBE, b'') # subscribe to topic of all (needed or else it won't work)
 
    try:
        while True:
            # Move to the next BLE scanning channel
            if datetime.now() >= hopping_time:
                current_ble_chan = opts.scan_channels[current_hop % len(
                    opts.scan_channels)]
                gr_block.set_ble_channel(BLE_CHANS[current_ble_chan])
                hopping_time = datetime.now() + timedelta(seconds=opts.ble_scan_window)
                current_hop += 1
                print("Switching to BLE channel [ {:d} ] @ {:d} MHz ({})".format(
                    current_ble_chan, int(gr_block.get_freq() / 1000000), stat.dump()))
                stat.reset()

            # Fetch data from Gnu Radio message queue
            #gr_buffer += gr_block.message_queue.delete_head().to_string()
            if socket.poll(10) != 0: # check if there is a message on the socket
                msg = socket.recv().decode('latin-1') # grab the message
                gr_buffer += msg
                

            if len(gr_buffer) < opts.min_buffer_size:
                continue

            # Prepend lost data
            if len(lost_data) > 0:
                gr_buffer = ''.join(str(x) for x in lost_data) + gr_buffer
                lost_data = ''

            # Search for BLE_PREAMBLE in received data
            for pos in [position for position, byte, in enumerate(gr_buffer) if byte == BLE_PREAMBLE]:
                pos += BLE_PREAMBLE_LEN
                samples_per_symbol = gr_block.get_gmsk_sps()
                byte_len = 8
                # Position index of BLE  packet beginning in the global buffer of bytes
                index_buffer_byte = pos+global_buffer_len - lost_data_len-1

                # Position index in term of bits
                index_buffer_bits = index_buffer_byte * byte_len

                # Position index of BLE packet beginning in IQ data
                # Note: GFSK demodulator uses  '$samples_per_symbol' samples for 1 bit symbol
                start_frame = index_buffer_bits * samples_per_symbol

                # Check enough data is available for parsing the BLE Access Address
                if len(gr_buffer[pos:]) < (BLE_ADDR_LEN + BLE_PDU_HDR_LEN):
                    continue

                debug("Found something @{}/{}".format(pos, len(gr_buffer)))

                # Extract BLE Access Address
                ble_access_address = unpack(
                    'I', gr_buffer[pos:pos + BLE_ADDR_LEN].encode("latin-1"))[0]
                pos += BLE_ADDR_LEN

                # Dewhitening received BLE Header
                if opts.disable_dewhitening == False:
                    ble_header = dewhitening(
                        gr_buffer[pos:pos + BLE_PDU_HDR_LEN], current_ble_chan)
                else:
                    ble_header = gr_buffer[pos:pos + BLE_PDU_HDR_LEN]

                # Check BLE PDU type
                ble_pdu_type = ble_header[0] & 0x0f
                if ble_pdu_type not in BLE_PDU_TYPE.values():
                    debug("Invalid ble_pdu_type: {:x}".format(ble_pdu_type))
                    stat.err_pdu += 1
                    continue

                if ble_access_address == BLE_ACCESS_ADDR:
                    # Extract BLE Length
                    ble_len = ble_header[1] & 0x3f
                else:
                    ble_llid = ble_header[0] & 0x3
                    if ble_llid == 0:
                        debug("Invalid LLID")
                        stat.err_llid += 1
                        continue

                    # Extract BLE Length
                    ble_len = ble_header[1] & 0x1f

                # Dewhitening BLE packet
                if opts.disable_dewhitening == False:
                    ble_data = dewhitening(
                        gr_buffer[pos:pos + BLE_PDU_HDR_LEN + BLE_CRC_LEN + ble_len], current_ble_chan)
                else:
                    ble_data = gr_buffer[pos:pos +
                                         BLE_PDU_HDR_LEN + BLE_CRC_LEN + ble_len]

                # Verify BLE data length
                if len(ble_data) != (BLE_PDU_HDR_LEN + BLE_CRC_LEN + ble_len):
                    lost_data = gr_buffer[pos - BLE_PREAMBLE_LEN - BLE_ADDR_LEN:pos +
                                          BLE_PREAMBLE_LEN + BLE_ADDR_LEN + BLE_PDU_HDR_LEN + BLE_CRC_LEN + ble_len]
                    debug("Invalid len: {} vs. {}".format(
                        len(ble_data), ble_len))
                    stat.err_len += 1
                    continue

                # Verify BLE packet checksum
                if opts.disable_crc == False:
                    if ble_data[-3:] != crc(ble_data, BLE_PDU_HDR_LEN + ble_len):
                        stat.err_crc += 1
                        continue

                if ble_pdu_type in [BLE_PDU_TYPE[t] for t in ['ADV_IND', 'ADV_DIRECT_IND', 'ADV_NONCONN_IND']]:
                    print("BLE-ADV: t:0x{:x}, {}".format(ble_pdu_type,
                                                         binascii.hexlify(bytearray(reversed(ble_data[2:8])))))
                    print("Index of BLE beginning ADV packet in IQ data: ", start_frame)
                    frame_iq_len = (BLE_ADDR_LEN+BLE_PREAMBLE_LEN +
                                    BLE_PDU_HDR_LEN + BLE_CRC_LEN + ble_len)*8*samples_per_symbol
                    # End of a detected BLE ADV
                    end_frame = start_frame+frame_iq_len
                    record_ble_iq_information(start_frame, end_frame, int(gr_block.get_freq()), int(
                        gr_block.get_sample_rate()), csv_file)

                else:
                    print("BLE-pkt: {}".format(binascii.hexlify(bytearray(ble_data))))
                    print("Index of BLE beginning ADV packet in IQ data:", start_frame)
                    frame_iq_len = (BLE_ADDR_LEN+BLE_PREAMBLE_LEN +
                                    BLE_PDU_HDR_LEN + BLE_CRC_LEN + ble_len)*8*samples_per_symbol
                    # End of a detected BLE packet
                    end_frame = start_frame+frame_iq_len
                    record_ble_iq_information(start_frame, end_frame, int(gr_block.get_freq()), int(
                        gr_block.get_sample_rate()), csv_file)

                # Write BLE packet to PCAP file descriptor
                write_pcap(pcap_fd, current_ble_chan,
                           ble_access_address, ble_data)
                stat.ok += 1
            global_buffer_len += len(gr_buffer)
            lost_data_len += len(lost_data)
            gr_buffer = ''

    except KeyboardInterrupt:
        print("Stopping...")
        pass

pcap_fd.close()
gr_block.stop()
gr_block.wait()
print("SAFE OVER")
