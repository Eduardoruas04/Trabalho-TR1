import matplotlib.pyplot as plt
import numpy as np

# === MODULAÇÕES BANDA BASE ===

def nrz_polar(bits, bit_duration=1, samples_per_bit=100):
    """
    Gera forma de onda NRZ-POLAR a partir de uma lista de bits.
    """
    t = []
    signal = []
    for bit in bits:
        value = 1 if bit == 1 else -1
        for _ in range(samples_per_bit):
            t.append(len(signal) * bit_duration / samples_per_bit)
            signal.append(value)
    return np.array(t), np.array(signal)


def manchester(bits, bit_duration=1, samples_per_bit=100):
    """
    Gera a forma de onda Manchester a partir de uma lista de bits.
    """
    t = []
    signal = []
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
    Gera a forma de onda Bipolar a partir de uma lista de bits.
    """
    t = []
    signal = []
    last = -1
    for bit in bits:
        value = 0 if bit == 0 else -1 * last
        if bit == 1:
            last *= -1
        for _ in range(samples_per_bit):
            t.append(len(signal) * bit_duration / samples_per_bit)
            signal.append(value)
    return np.array(t), np.array(signal)


# === MODULAÇÕES POR PORTADORA ===

def ask_modulation(bits, bit_duration=1, samples_per_bit=100, freq=5):
    """
    Gera modulação ASK (Amplitude Shift Keying).
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
    Gera modulação FSK (Frequency Shift Keying).
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
    Gera modulação 8-QAM (Quadrature Amplitude Modulation).
    """
    symbols = [bits[i:i+3] for i in range(0, len(bits), 3)]
    total_samples = samples_per_bit * len(symbols)
    t = np.linspace(0, bit_duration * len(symbols), total_samples)
    signal = []

    mapping = {
        (0,0,0): (1, 1),  (0,0,1): (1, -1),
        (0,1,0): (-1, 1), (0,1,1): (-1, -1),
        (1,0,0): (3, 1),  (1,0,1): (3, -1),
        (1,1,0): (-3, 1), (1,1,1): (-3, -1),
    }

    for i, bits_triplet in enumerate(symbols):
        while len(bits_triplet) < 3:
            bits_triplet.append(0)
        I, Q = mapping[tuple(bits_triplet)]
        symbol_t = t[i*samples_per_bit:(i+1)*samples_per_bit]
        carrier = 2 * np.pi * carrier_freq * symbol_t
        segment = I * np.cos(carrier) + Q * np.sin(carrier)
        signal.extend(segment)
    return t, np.array(signal)


# === TESTE AUTOMÁTICO LOCAL ===

if __name__ == "__main__":
    bits = [1, 0, 1, 1, 0, 0, 1]

    modulations = [
        ("NRZ-Polar", nrz_polar),
        ("Manchester", manchester),
        ("Bipolar", bipolar),
        ("ASK", ask_modulation),
        ("FSK", fsk_modulation),
        ("8-QAM", qam8_modulation)
    ]

    for title, func in modulations:
        t, s = func(bits)
        plt.figure(figsize=(10, 2))
        estilo = 'steps-post' if "NRZ" in title or "Manchester" in title or "Bipolar" in title else 'default'
        plt.plot(t, s, drawstyle=estilo)
        plt.title(f"Modulação {title}")
        plt.xlabel("Tempo")
        plt.ylabel("Amplitude")
        plt.grid(True)
        plt.tight_layout()
        plt.show()
