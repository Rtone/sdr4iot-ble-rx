#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Bluetooth LE Receiver
# Author: Jan Wagner
# Generated: Fri Jan 17 17:44:20 2020
##################################################

from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import time


class gr_ble(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Bluetooth LE Receiver")

        ##################################################
        # Variables
        ##################################################
        self.transition_width = transition_width = 300e3
        self.sample_rate = sample_rate = 5e6
        self.data_rate = data_rate = 1e6
        self.duration_seconds = duration_seconds = 10
        self.cutoff_freq = cutoff_freq = 850e3
        self.ble_channel_spacing = ble_channel_spacing = 2e6
        self.ble_channel = ble_channel = 12
        self.ble_base_freq = ble_base_freq = 2402e6
        self.squelch_threshold = squelch_threshold = -70
        self.rf_gain = rf_gain = 30
        self.num_samples = num_samples = duration_seconds*sample_rate
        self.lowpass_filter = lowpass_filter = firdes.low_pass(1, sample_rate, cutoff_freq, transition_width, firdes.WIN_HAMMING, 6.76)
        self.iq_output = iq_output = "/dev/null"
        self.gmsk_sps = gmsk_sps = int(sample_rate / data_rate)
        self.gmsk_omega_limit = gmsk_omega_limit = 0.035
        self.gmsk_mu = gmsk_mu = 0.5
        self.gmsk_gain_mu = gmsk_gain_mu = 0.7
        self.freq_offset = freq_offset = 1e6
        self.freq = freq = ble_base_freq+(ble_channel_spacing * ble_channel)

        ##################################################
        # Message Queues
        ##################################################
        self.message_queue = message_queue = gr.msg_queue(2)

        ##################################################
        # Blocks
        ##################################################
        self.unpacked_to_packed = blocks.unpacked_to_packed_bb(1, gr.GR_LSB_FIRST)
        self.uhd_usrp_source_0 = uhd.usrp_source(
        	",".join(("", "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_source_0.set_samp_rate(sample_rate)
        self.uhd_usrp_source_0.set_center_freq(freq+freq_offset, 0)
        self.uhd_usrp_source_0.set_gain(rf_gain, 0)
        self.uhd_usrp_source_0.set_antenna('J2', 0)
        self.message_sink = blocks.message_sink(gr.sizeof_char*1, self.message_queue, True)
        self.freq_xlating_fir_filter_lp = filter.freq_xlating_fir_filter_ccc(1, (lowpass_filter), -freq_offset, sample_rate)
        self.digital_gmsk_demod_0 = digital.gmsk_demod(
        	samples_per_symbol=gmsk_sps,
        	gain_mu=gmsk_gain_mu,
        	mu=gmsk_mu,
        	omega_relative_limit=gmsk_omega_limit,
        	freq_error=0.0,
        	verbose=False,
        	log=False,
        )
	self.blocks_head_0 = blocks.head(gr.sizeof_gr_complex*1, int(num_samples))
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_gr_complex*1, iq_output, False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.analog_simple_squelch = analog.simple_squelch_cc(squelch_threshold, 0.1)
        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_simple_squelch, 0), (self.freq_xlating_fir_filter_lp, 0))    
        self.connect((self.digital_gmsk_demod_0, 0), (self.unpacked_to_packed, 0))    
        self.connect((self.freq_xlating_fir_filter_lp, 0), (self.digital_gmsk_demod_0, 0))    
        self.connect((self.blocks_head_0, 0), (self.analog_simple_squelch, 0))    
        self.connect((self.blocks_head_0, 0), (self.blocks_file_sink_0, 0))
	self.connect((self.uhd_usrp_source_0, 0), (self.blocks_head_0, 0))
        self.connect((self.unpacked_to_packed, 0), (self.message_sink, 0))    

    def get_transition_width(self):
        return self.transition_width

    def set_transition_width(self, transition_width):
        self.transition_width = transition_width
        self.set_lowpass_filter(firdes.low_pass(1, self.sample_rate, self.cutoff_freq, self.transition_width, firdes.WIN_HAMMING, 6.76))

    def get_sample_rate(self):
        return self.sample_rate

    def set_sample_rate(self, sample_rate):
        self.sample_rate = sample_rate
	self.set_gmsk_sps(int(self.sample_rate / self.data_rate))
        self.set_lowpass_filter(firdes.low_pass(1, self.sample_rate, self.cutoff_freq, self.transition_width, firdes.WIN_HAMMING, 6.76))
	self.set_num_samples(self.duration_seconds*self.sample_rate)
        self.uhd_usrp_source_0.set_samp_rate(self.sample_rate)

    def get_duration_seconds(self):
        return self.duration_seconds

    def set_duration_seconds(self, duration_seconds):
        self.duration_seconds = duration_seconds
        self.set_num_samples(self.duration_seconds*self.sample_rate)

    def get_data_rate(self):
        return self.data_rate

    def set_data_rate(self, data_rate):
        self.data_rate = data_rate
        self.set_gmsk_sps(int(self.sample_rate / self.data_rate))

    def get_cutoff_freq(self):
        return self.cutoff_freq

    def set_cutoff_freq(self, cutoff_freq):
        self.cutoff_freq = cutoff_freq
        self.set_lowpass_filter(firdes.low_pass(1, self.sample_rate, self.cutoff_freq, self.transition_width, firdes.WIN_HAMMING, 6.76))

    def get_ble_channel_spacing(self):
        return self.ble_channel_spacing

    def set_ble_channel_spacing(self, ble_channel_spacing):
        self.ble_channel_spacing = ble_channel_spacing
        self.set_freq(self.ble_base_freq+(self.ble_channel_spacing * self.ble_channel))

    def get_ble_channel(self):
        return self.ble_channel

    def set_ble_channel(self, ble_channel):
        self.ble_channel = ble_channel
        self.set_freq(self.ble_base_freq+(self.ble_channel_spacing * self.ble_channel))

    def get_ble_base_freq(self):
        return self.ble_base_freq

    def set_ble_base_freq(self, ble_base_freq):
        self.ble_base_freq = ble_base_freq
        self.set_freq(self.ble_base_freq+(self.ble_channel_spacing * self.ble_channel))

    def get_squelch_threshold(self):
        return self.squelch_threshold

    def set_squelch_threshold(self, squelch_threshold):
        self.squelch_threshold = squelch_threshold
        self.analog_simple_squelch.set_threshold(self.squelch_threshold)

    def get_rf_gain(self):
        return self.rf_gain

    def set_rf_gain(self, rf_gain):
        self.rf_gain = rf_gain
        self.uhd_usrp_source_0.set_gain(self.rf_gain, 0)

    def get_num_samples(self):
        return self.num_samples

    def set_num_samples(self, num_samples):
        self.num_samples = num_samples
        self.blocks_head_0.set_length(int(self.num_samples))

    def get_lowpass_filter(self):
        return self.lowpass_filter

    def set_lowpass_filter(self, lowpass_filter):
        self.lowpass_filter = lowpass_filter
        self.freq_xlating_fir_filter_lp.set_taps((self.lowpass_filter))

    def get_iq_output(self):
        return self.iq_output

    def set_iq_output(self, iq_output):
        self.iq_output = iq_output
        self.blocks_file_sink_0.open(self.iq_output)

    def get_gmsk_sps(self):
        return self.gmsk_sps

    def set_gmsk_sps(self, gmsk_sps):
        self.gmsk_sps = gmsk_sps

    def get_gmsk_omega_limit(self):
        return self.gmsk_omega_limit

    def set_gmsk_omega_limit(self, gmsk_omega_limit):
        self.gmsk_omega_limit = gmsk_omega_limit

    def get_gmsk_mu(self):
        return self.gmsk_mu

    def set_gmsk_mu(self, gmsk_mu):
        self.gmsk_mu = gmsk_mu

    def get_gmsk_gain_mu(self):
        return self.gmsk_gain_mu

    def set_gmsk_gain_mu(self, gmsk_gain_mu):
        self.gmsk_gain_mu = gmsk_gain_mu

    def get_freq_offset(self):
        return self.freq_offset

    def set_freq_offset(self, freq_offset):
        self.freq_offset = freq_offset
        self.uhd_usrp_source_0.set_center_freq(self.freq+self.freq_offset, 0)
        self.freq_xlating_fir_filter_lp.set_center_freq(-self.freq_offset)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.uhd_usrp_source_0.set_center_freq(self.freq+self.freq_offset, 0)


def main(top_block_cls=gr_ble, options=None):

    tb = top_block_cls()
    tb.start()
    try:
        raw_input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()
