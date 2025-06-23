import numpy as np
import matplotlib.pyplot as plt

# === MODULAÇÕES BANDA BASE ===

def nrz_polar(bits, bit_duration=1, samples_per_bit=100):
    """
    Modulação NRZ-Polar: 1 -> +1, 0 -> -1 (nível constante).
    """
    t, signal = [], []
    for bit in bits:
        value = 1 if bit == 1 else -1
        for _ in range(samples_per_bit):
            t.append(len(signal) * bit_duration / samples_per_bit)
            signal.append(value)
    return np.array(t), np.array(signal)


def manchester(bits, bit_duration=1, samples_per_bit=100):
    """
    Modulação Manchester: 0 -> +1/-1, 1 -> -1/+1 (transição no meio do bit).
    """
    t, signal = [], []
    for bit in bits:
        first = 1 if bit == 0 else -1
        second = -first
        for _ in range(samples_per_bit // 2):
            t.append(len(signal) * bit_duration / samples_per_bit)
            signal.append(first)
        for _ in range(samples_per_bit // 2):
            t.append(len(signal) * bit_duration / samples_per_bit)
            signal.append(second)
    return np.array(t), np.array(signal)


def bipolar(bits, bit_duration=1, samples_per_bit=100):
    """
    Modulação Bipolar: 0 -> 0, 1 alterna entre +1 e -1.
    """
    t, signal = [], []
    last = -1
    for bit in bits:
        if bit == 0:
            value = 0
        else:
            last *= -1
            value = last
        for _ in range(samples_per_bit):
            t.append(len(signal) * bit_duration / samples_per_bit)
            signal.append(value)
    return np.array(t), np.array(signal)

# === MODULAÇÕES POR PORTADORA ===

def ask_modulation(bits, bit_duration=1, samples_per_bit=100, freq=5):
    """
    Modulação ASK (Amplitude Shift Keying): bit 1 → A=1, bit 0 → A=0.3.
    """
    total_samples = len(bits) * samples_per_bit
    t = np.linspace(0, bit_duration * len(bits), total_samples)
    signal = np.zeros(total_samples)
    for i, bit in enumerate(bits):
        A = 1 if bit == 1 else 0.3
        for j in range(samples_per_bit):
            idx = i * samples_per_bit + j
            signal[idx] = A * np.sin(2 * np.pi * freq * t[idx])
    return t, signal


def fsk_modulation(bits, bit_duration=1, samples_per_bit=100, f0=5, f1=10):
    """
    Modulação FSK (Frequency Shift Keying): bit 0 → f0, bit 1 → f1.
    """
    total_samples = len(bits) * samples_per_bit
    t = np.linspace(0, bit_duration * len(bits), total_samples)
    signal = np.zeros(total_samples)
    for i, bit in enumerate(bits):
        f = f1 if bit == 1 else f0
        for j in range(samples_per_bit):
            idx = i * samples_per_bit + j
            signal[idx] = np.sin(2 * np.pi * f * t[idx])
    return t, signal


def qam8_modulation(bits, bit_duration=1, samples_per_bit=100, carrier_freq=5):
    """
    Modulação 8-QAM: combina fase e amplitude (3 bits por símbolo).
    """
    # Agrupar os bits em trios (1 símbolo = 3 bits)
    symbols = [bits[i:i+3] for i in range(0, len(bits), 3)]
    total_samples = samples_per_bit * len(symbols)
    t = np.linspace(0, bit_duration * len(symbols), total_samples)
    signal = []

    # Mapeamento de bits para valores I/Q
    mapping = {
        (0,0,0): (1, 1),  (0,0,1): (1, -1),
        (0,1,0): (-1, 1), (0,1,1): (-1, -1),
        (1,0,0): (3, 1),  (1,0,1): (3, -1),
        (1,1,0): (-3, 1), (1,1,1): (-3, -1),
    }

    for i, triplet in enumerate(symbols):
        while len(triplet) < 3:
            triplet.append(0)
        I, Q = mapping[tuple(triplet)]
        symbol_t = t[i*samples_per_bit:(i+1)*samples_per_bit]
        carrier = 2 * np.pi * carrier_freq * symbol_t
        segment = I * np.cos(carrier) + Q * np.sin(carrier)
        signal.extend(segment)

    return t, np.array(signal)
