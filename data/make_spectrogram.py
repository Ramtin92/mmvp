import numpy as np
import scipy.io.wavfile as wav
from numpy.lib import stride_tricks

""" short time fourier transform of audio signal """
def stft(sig, frameSize, overlapFac=0.5, window=np.hanning):
    win = window(frameSize)
    hopSize = int(frameSize - np.floor(overlapFac * frameSize))
    # zeros at beginning (thus center of 1st window should be for sample nr. 0)
    samples = np.append(np.zeros(int(np.floor(frameSize / 2.0))), sig)

    # cols for windowing
    cols = np.ceil((len(samples) - frameSize) / float(hopSize)) + 1
    # zeros at end (thus samples can be fully covered by frames)
    samples = np.append(samples, np.zeros(frameSize))

    frames = stride_tricks.as_strided(samples, shape=(int(cols), frameSize),
                                      strides=(samples.strides[0] * hopSize, samples.strides[0])).copy()
    frames *= win
    return np.fft.rfft(frames)


""" scale frequency axis logarithmically """
def logscale_spec(spec, sr=44100, factor=20.):
    timebins, freqbins = np.shape(spec)

    scale = np.linspace(0, 1, freqbins) ** factor
    scale *= (freqbins - 1) / max(scale)
    scale = np.unique(np.round(scale))

    # create spectrogram with new freq bins
    newspec = np.complex128(np.zeros([timebins, len(scale)]))
    for i in range(0, len(scale)):
        if i == len(scale) - 1:
            newspec[:, i] = np.sum(spec[:, int(scale[i]):], axis=1)
        else:
            newspec[:, i] = np.sum(spec[:, int(scale[i]):int(scale[i + 1])], axis=1)

    # list center freq of bins
    allfreqs = np.abs(np.fft.fftfreq(freqbins * 2, 1. / sr)[:freqbins + 1])
    freqs = []
    for i in range(0, len(scale)):
        if i == len(scale) - 1:
            freqs += [np.mean(allfreqs[int(scale[i]):])]
        else:
            freqs += [np.mean(allfreqs[int(scale[i]):int(scale[i + 1])])]

    return newspec, freqs


""" plot spectrogram"""
def plotstft(audio_path, binsize=2 ** 10, plotpath=None, colormap="jet", fig_name="spectrogram"):
    samplerate, samples = wav.read(audio_path)
    import matplotlib.pyplot as plt
    s = stft(samples[:, 0], binsize)

    sshow, freq = logscale_spec(s, factor=1.0, sr=samplerate)
    sshow = sshow[2:, :]
    ims = 20. * np.log10(np.abs(sshow) / 10e-6)  # amplitude to decibel
    timebins, freqbins = np.shape(ims)

    """
    plt.figure(figsize=(3200.0/300.0, 2100.0/300.0))

    # plt.title("Audio Spectrogram", fontsize=32)
    plt.xlabel("Time (s)", fontsize=32)
    plt.ylabel("Frequency (kHz)", fontsize=32)
    plt.xlim([0, timebins - 1])
    plt.ylim([0, freqbins])

    xlocs = np.float32(np.linspace(0, timebins - 1, 5))
    plt.xticks(xlocs, ["%.01f" % l for l in ((xlocs * len(samples) / timebins) + (0.5 * binsize)) / samplerate], fontsize=24)
    ylocs = np.int16(np.round(np.linspace(0, freqbins - 1, 23)))[::4]
    ylocs1 = list(range(int(np.max(freq)//1000)+1))[::4]

    plt.yticks(ylocs[1:], ylocs1[1:], fontsize=24)

    plt.imshow(np.transpose(ims), origin="lower", aspect="auto", cmap=colormap, interpolation="none")
    # plt.colorbar()
    plt.tight_layout()
    plt.savefig("audio_spectrogram_low_drop_can_coke.png", dpi=300)
    """

    ims = np.transpose(ims)
    ims = ims[0:256, :]
    return ims, 1/samplerate*samples.shape[0]

