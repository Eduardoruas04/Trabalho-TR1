import numpy as np

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

# === DETECÇÃO E CORREÇÃO ===

def aplicar_paridade_par(dados: bytes) -> bytes:
    bits = ''.join(f'{b:08b}' for b in dados)
    return dados + bytes([1]) if bits.count('1') % 2 != 0 else dados + bytes([0])

def aplicar_crc32(dados: bytes) -> bytes:
    import zlib
    crc = zlib.crc32(dados) & 0xFFFFFFFF
    return dados + crc.to_bytes(4, 'big')

def aplicar_hamming(dados: bytes) -> bytes:
    # Simples placeholder
    return dados + b'H'


