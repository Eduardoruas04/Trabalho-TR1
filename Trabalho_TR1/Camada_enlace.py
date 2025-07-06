import numpy as np
import zlib
import random

# === ENQUADRAMENTO ===

def enquadramento_contagem(mensagem: bytes) -> bytes:
    tamanho = len(mensagem) + 1
    if tamanho > 255:
        raise ValueError("Mensagem muito longa para enquadramento por contagem.")
    return bytes([tamanho]) + mensagem

def desenquadramento_contagem(quadro: bytes) -> bytes:
    if not quadro:
        raise ValueError("Quadro vazio.")
    tamanho = quadro[0]
    if tamanho != len(quadro):
        raise ValueError("Erro no quadro.")
    return quadro[1:]

def enquadramento_byte_stuffing(mensagem: bytes, flag=b'~', esc=b'\x1B') -> bytes:
    resultado = bytearray(flag)
    for byte in mensagem:
        if byte == flag[0] or byte == esc[0]:
            resultado.extend(esc)
        resultado.append(byte)
    resultado.extend(flag)
    return bytes(resultado)

def desenquadramento_byte_stuffing(quadro: bytes, flag=b'~', esc=b'\x1B') -> bytes:
    if not (quadro.startswith(flag) and quadro.endswith(flag)):
        raise ValueError("Quadro malformado.")
    conteudo = quadro[1:-1]
    resultado = bytearray()
    i = 0
    while i < len(conteudo):
        if conteudo[i:i+1] == esc:
            i += 1
        resultado.append(conteudo[i])
        i += 1
    return bytes(resultado)

def enquadramento_bit_stuffing(mensagem: bytes) -> bytes:
    bits = ''.join(f'{byte:08b}' for byte in mensagem)
    stuffed = ''
    cont = 0
    for b in bits:
        if b == '1':
            cont += 1
            stuffed += b
            if cont == 5:
                stuffed += '0'
                cont = 0
        else:
            stuffed += b
            cont = 0
    stuffed = '01111110' + stuffed + '01111110'
    return int(stuffed, 2).to_bytes((len(stuffed) + 7) // 8, byteorder='big')

def desenquadramento_bit_stuffing(quadro: bytes) -> bytes:
    bits = ''.join(f'{byte:08b}' for byte in quadro)
    bits = bits[8:-8]  # remover as flags
    destuffed = ''
    cont = 0
    i = 0
    while i < len(bits):
        b = bits[i]
        if b == '1':
            cont += 1
            destuffed += b
            if cont == 5:
                i += 1  # pular o zero inserido
                cont = 0
        else:
            destuffed += b
            cont = 0
        i += 1
    return int(destuffed, 2).to_bytes((len(destuffed) + 7) // 8, byteorder='big')

# === DETECÇÃO DE ERROS ===

def aplicar_paridade_par(dados: bytes) -> bytes:
    bits = ''.join(f'{b:08b}' for b in dados)
    return dados + bytes([1]) if bits.count('1') % 2 != 0 else dados + bytes([0])

def aplicar_crc32(dados: bytes) -> bytes:
    crc = zlib.crc32(dados) & 0xFFFFFFFF
    return dados + crc.to_bytes(4, 'big')

# === CORREÇÃO DE ERROS (HAMMING 7,4) ===

def codificar_hamming_7_4(dados: bytes) -> bytes:
    resultado = bytearray()
    for byte in dados:
        for i in (4, 0):
            nibble = (byte >> i) & 0x0F  # extrai 4 bits
            d = [(nibble >> j) & 1 for j in range(3, -1, -1)]  # d1, d2, d3, d4
            p1 = d[0] ^ d[1] ^ d[3]
            p2 = d[0] ^ d[2] ^ d[3]
            p3 = d[1] ^ d[2] ^ d[3]
            hamming = (p1 << 6) | (p2 << 5) | (d[0] << 4) | (p3 << 3) | (d[1] << 2) | (d[2] << 1) | d[3]
            resultado.append(hamming)
    return bytes(resultado)

def decodificar_hamming_7_4(codigo: bytes) -> bytes:
    resultado = bytearray()
    bits = []
    for byte in codigo:
        p1 = (byte >> 6) & 1
        p2 = (byte >> 5) & 1
        d1 = (byte >> 4) & 1
        p3 = (byte >> 3) & 1
        d2 = (byte >> 2) & 1
        d3 = (byte >> 1) & 1
        d4 = byte & 1

        s1 = p1 ^ d1 ^ d2 ^ d4
        s2 = p2 ^ d1 ^ d3 ^ d4
        s3 = p3 ^ d2 ^ d3 ^ d4
        erro_pos = (s3 << 2) | (s2 << 1) | s1

        bits_corrigidos = [p1, p2, d1, p3, d2, d3, d4]
        if erro_pos != 0 and erro_pos <= 7:
            bits_corrigidos[erro_pos - 1] ^= 1  # corrige o bit

        d1 = bits_corrigidos[2]
        d2 = bits_corrigidos[4]
        d3 = bits_corrigidos[5]
        d4 = bits_corrigidos[6]
        bits.extend([d1, d2, d3, d4])

        if len(bits) == 8:
            byte_result = sum([bit << (7 - i) for i, bit in enumerate(bits)])
            resultado.append(byte_result)
            bits.clear()
    return bytes(resultado)


def introduzir_erro(quadro: bytes, n_erros=1) -> bytes:
    
    # Inverte aleatoriamente 'n_erros' bits no quadro (bytearray).
    
    bits = [int(b) for byte in quadro for b in f"{byte:08b}"]
    
    for _ in range(n_erros):
        pos = random.randint(0, len(bits) - 1)
        bits[pos] ^= 1  # inverte o bit
    
    # Reconvertendo bits para bytes
    bytes_modificados = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bits):
                byte = (byte << 1) | bits[i + j]
        bytes_modificados.append(byte)
    
    return bytes(bytes_modificados)
