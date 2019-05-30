# Author: Ovidiu Mura
# Date: May 22, 2019

import wave
import numpy as np
from numpy import int16
import matplotlib.pyplot as plt

from scipy.io.wavfile import write
from correlate import *
import scipy.signal

from scipy.io import wavfile

class Mix:

    def __init__(self):
        self.file1 = None
        self.file2 = None
        self.orig_emergency = None
        self.mix_signal = None
        self.normalized_cross_correlation = None
        self.s_1 = None
        self.s_2 = None
        self.output_file = None

    def get_samples_from_files(self, f1, f2):
        w1 = wave.open(f1)
        w2 = wave.open(f2)

        # get samples formatted as a string.
        s01 = w1.readframes(w1.getnframes())
        s02 = w2.readframes(w2.getnframes())

        # takes every 2 bytes and groups them together as 1 sample. ("123456" -> ["12", "34", "56"])
        s1 = [s01[i:i+2] for i in range(0, len(s01), 2)]
        s2 = [s02[i:i+2] for i in range(0, len(s02), 2)]

        self.s_1 = [self.str_to_int(s) for s in s1] #['\x04\x08'] -> [0x0804]
        self.s_2 = [self.str_to_int(s) for s in s2]

    def get_samples_from_file(self, f1):
        w1 = wave.open(f1)

        # get samples formatted as a string.
        s01 = w1.readframes(w1.getnframes())

        # takes every 2 bytes and groups them together as 1 sample. ("123456" -> ["12", "34", "56"])
        s1 = [s01[i:i+2] for i in range(0, len(s01), 2)]

        self.s_1 = [self.str_to_int(s) for s in s1] #['\x04\x08'] -> [0x0804]
        return self.s_1

    # convert samples from strings to ints
    def str_to_int(self, str):
        i = 0
        for c in str[::-1]: # iterate over each char in reverse (because little-endian)
            # get the integer value from char and
            # assign to the lowest byte of as int, then shifting the rest up
            i <<= 8
            i += c
        return i

    def avg_mix_sounds(self, file1, file2, output_file):
        self.output_file = output_file
        w1 = wave.open(file1)
        w2 = wave.open(file2)

        # get samples formatted as a string.
        s01 = w1.readframes(w1.getnframes())
        s02 = w2.readframes(w2.getnframes())

        # takes every 2 bytes and groups them together as 1 sample. ("123456" -> ["12", "34", "56"])
        s1 = [s01[i:i+2] for i in range(0, len(s01), 2)]
        s2 = [s02[i:i+2] for i in range(0, len(s02), 2)]

        # samples1 = [self.bin_to_int(s) for s in samples1] #['\x04\x08'] -> [0x0804]
        s_1 = [self.str_to_int(s) for s in s1] #['\x04\x08'] -> [0x0804]
        s_2 = [self.str_to_int(s) for s in s2]

        self.orig_emergency = np.array(s_1)/10000

        self.s_1 = s_1
        self.s_2 = s_2

        plt.plot(self.s_1[:300], color="red")
        plt.grid(True)
        plt.show()

        # average the samples:
        samples_avg = [(s1+s2)/2 for (s1, s2) in zip(s_1, s_2)]
        self.mix_signal = samples_avg
        print("output_file: "+ str(output_file))
        write(output_file, 48000, self.to_int16(samples_avg))
        return samples_avg

    def mult_mix_sounds(self, file1, file2):
        self.get_samples_from_files(file1, file2)
        sz = min(len(self.s_1),len(self.s_2))
        multiply_signals = np.absolute(np.array(self.s_1[:sz])*np.array(self.s_2[:sz])/100000)
        plt.plot(multiply_signals[:1000], color='red')
        plt.show()

    def add_mix_sounds(self, file1, file2):
        self.get_samples_from_files(file1, file2)
        sz = min(len(self.s_1),len(self.s_2))
        add_signals = np.add(np.array(self.s_1[:sz]),np.array(self.s_2[:sz]))/10000
        plt.plot(add_signals[:1000], color='blue')
        #plt.plot(self.samples_1[:1000], color='gray')
        plt.show()

    def to_int16(self, signal):
        # Take samples in [-1, 1] and scale to 16-bit integers,
        # values between -2^15 and 2^15 - 1.
        return int16(signal*1)

    def is_in_mix(self, s1, s2):
        ys = self.avg_mix_sounds(s1, s2, self.output_file)
        ys = np.absolute(ys)

        self.mix_signal = ys/10000

        x1 = self.mix_signal
        x2 = self.orig_emergency

        norm_corr = Correlate()
        size = min(len(x1), len(x2))
        self.normalized_cross_correlation = norm_corr.normalized_correlation(x1[:size], x2[:size])
        print("norm cross_corr: " + str(self.normalized_cross_correlation))
        cor = norm_corr.discrete_linear_convolution(self.mix_signal[0:1696], self.orig_emergency[0:1696])/10000
        cor2 = norm_corr.discrete_linear_convolution(self.orig_emergency[0:1696], self.orig_emergency[0:1696])/10000
        plt.title("Discrete Linear Convolution")
        plt.plot(cor, color='blue')
        plt.plot(cor2, color='red')
        plt.show()

        print("std corr: " + str(norm_corr.standard_correlate(x1,x2)))
        if(self.normalized_cross_correlation > 0.5):
            return True
        return False

    def plot_mix_and_original_signal(self):
        plt.title("Mixed signal")
        plt.plot(self.mix_signal[:1000], color='blue')
        plt.show()
        plt.title("Emergency signal")
        plt.plot(self.orig_emergency[:1000], color='red')
        # plt.plot(a, color='red')
        # plt.plot((cor), color='green')
        plt.show()


class Convolute:

    def __init__(self):
        self.signal_1 = None
        self.signal_2 = None
        self.convolved = None
        self.gaussian_window = None

    def convolve_gaussian_window(self, s1, s2, p=True):
        self.signal_1 = s1
        self.signal_2 = s2

        self.gaussian_window = scipy.signal.gaussian(M=11, std=2)
        self.gaussian_window /= sum(self.gaussian_window)

        convolved = np.convolve(self.signal_1, self.gaussian_window, mode='valid')
        self.convolved = convolved

        if (p==True):
            plt.title("Convolved signal and the Emergency signal")
            plt.plot(self.signal_1[:1000], color='blue')
            plt.plot(convolved.real[:1000], color='red')
            plt.show()

    def fft_convolve(self, signal_1, signal_2, p=True):
        self.signal_1 = signal_1
        self.signal_2 = signal_2

        # Convolution Theorem: DFT( f * g) = DFT( f ) * DFT(g) -> f * g = IDFT(DFT( f ) * DFT(g))
        fft1 = np.fft.fft(self.signal_1)/100000
        fft2 = np.fft.fft(self.signal_2)/100000
        sz = min(len(fft1.real), len(fft2.real))

        fft_from_convolution_theorem = np.array(np.fft.ifft(fft1[:sz]*fft2[:sz]))

        if(p==True):
            plt.plot(fft_from_convolution_theorem.real[:1000]/60000, color='black')
            # plt.plot(np.array(self.signal_1[:1000])/60000, color='silver')
            plt.show()

        c = Correlate()
        corr_value = c.normalized_correlation(fft_from_convolution_theorem[:sz].real, self.signal_1[:sz])
        if (corr_value > 0.5):
            print("info: emergency sound was detected in the brownian motion FFT convolve, using normalized cross-correlation, {0}".format(corr_value))
