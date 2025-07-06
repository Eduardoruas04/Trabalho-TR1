import numpy as np
import zlib
import random

# === ENQUADRAMENTO ===

def enquadramento_contagem(mensagem: bytes) -> bytes:
    """
    Enquadramento por contagem de caracteres.
    O primeiro byte representa o tamanho total do quadro (mensagem + 1).
    """
    tamanho = len(mensagem) + 1
    if tamanho > 255:
        raise ValueError("Mensagem muito longa para enquadramento por contagem.")
    return bytes([tamanho]) + mensagem

def desenquadramento_contagem(quadro: bytes) -> bytes:
    """
    Desenquadramento de contagem de caracteres.
    Verifica se o tamanho declarado no primeiro byte corresponde ao real.
    """
    if not quadro:
        raise ValueError("Quadro vazio.")
    tamanho = quadro[0]
    if tamanho != len(quadro):
        raise ValueError("Erro no quadro.")
    return quadro[1:]

def enquadramento_byte_stuffing(mensagem: bytes, flag=b'~', esc=b'\x1B') -> bytes:
    """
    Enquadramento com inserção de bytes (byte stuffing).
    Adiciona FLAGS no início e fim do quadro e insere ESC antes de FLAGS ou ESC dentro da mensagem.
    """
    resultado = bytearray(flag)
    for byte in mensagem:
        if byte == flag[0] or byte == esc[0]:
            resultado.extend(esc)
        resultado.append(byte)
    resultado.extend(flag)
    return bytes(resultado)

def desenquadramento_byte_stuffing(quadro: bytes, flag=b'~', esc=b'\x1B') -> bytes:
    """
    Desenquadramento com remoção de bytes inseridos.
    Remove os bytes de escape (ESC) adicionados antes de FLAGS ou ESC.
    """
    if not (quadro.startswith(flag) and quadro.endswith(flag)):
        raise ValueError("Quadro malformado.")
    conteudo = quadro[1:-1]
    resultado = bytearray()
    i = 0
    while i < len(conteudo):
        if conteudo[i:i+1] == esc:
            i += 1  # Ignora o ESC
        resultado.append(conteudo[i])
        i += 1
    return bytes(resultado)

def enquadramento_bit_stuffing(mensagem: bytes) -> bytes:
    """
    Enquadramento com inserção de bits (bit stuffing).
    Após cinco bits '1' consecutivos, insere um bit '0'.
    Adiciona também a FLAG 01111110 no início e fim do quadro.
    """
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
    """
    Remove o bit stuffing e as FLAGS do quadro.
    Após cinco bits '1', remove o bit '0' inserido.
    """
    bits = ''.join(f'{byte:08b}' for byte in quadro)
    bits = bits[8:-8]  # Remove as flags (01111110)
    destuffed = ''
    cont = 0
    i = 0
    while i < len(bits):
        b = bits[i]
        if b == '1':
            cont += 1
            destuffed += b
            if cont == 5:
                i += 1  # Pula o bit '0' inserido
                cont = 0
        else:
            destuffed += b
            cont = 0
        i += 1
    return int(destuffed, 2).to_bytes((len(destuffed) + 7) // 8, byteorder='big')

# === DETECÇÃO DE ERROS ===

def aplicar_paridade_par(dados: bytes) -> bytes:
    """
    Aplica bit de paridade par no final do quadro.
    Adiciona '1' se a contagem de bits '1' for ímpar, senão adiciona '0'.
    """
    bits = ''.join(f'{b:08b}' for b in dados)
    return dados + bytes([1]) if bits.count('1') % 2 != 0 else dados + bytes([0])

def aplicar_crc32(dados: bytes) -> bytes:
    """
    Aplica o código de redundância cíclica (CRC-32) padrão IEEE 802.
    Anexa ao final do quadro 4 bytes correspondentes ao checksum.
    """
    crc = zlib.crc32(dados) & 0xFFFFFFFF
    return dados + crc.to_bytes(4, 'big')

# === CORREÇÃO DE ERROS (HAMMING 7,4) ===

def codificar_hamming_7_4(dados: bytes) -> bytes:
    """
    Codifica os dados utilizando o código de Hamming (7,4).
    Cada nibble (4 bits) de dados é transformado em 7 bits com 3 bits de paridade.
    """
    resultado = bytearray()
    for byte in dados:
        for i in (4, 0):  # Divide byte em dois nibbles
            nibble = (byte >> i) & 0x0F
            d = [(nibble >> j) & 1 for j in range(3, -1, -1)]
            p1 = d[0] ^ d[1] ^ d[3]
            p2 = d[0] ^ d[2] ^ d[3]
            p3 = d[1] ^ d[2] ^ d[3]
            hamming = (p1 << 6) | (p2 << 5) | (d[0] << 4) | (p3 << 3) | (d[1] << 2) | (d[2] << 1) | d[3]
            resultado.append(hamming)
    return bytes(resultado)

def decodificar_hamming_7_4(codigo: bytes) -> bytes:
    """
    Decodifica os dados codificados com Hamming (7,4).
    Detecta e corrige 1 bit com erro. Agrupa cada 2 símbolos de 7 bits em 1 byte.
    """
    resultado = bytearray()
    bits = []
    for byte in codigo:
        # Extração dos bits de paridade e dados
        p1 = (byte >> 6) & 1
        p2 = (byte >> 5) & 1
        d1 = (byte >> 4) & 1
        p3 = (byte >> 3) & 1
        d2 = (byte >> 2) & 1
        d3 = (byte >> 1) & 1
        d4 = byte & 1

        # Cálculo dos bits de síndrome
        s1 = p1 ^ d1 ^ d2 ^ d4
        s2 = p2 ^ d1 ^ d3 ^ d4
        s3 = p3 ^ d2 ^ d3 ^ d4
        erro_pos = (s3 << 2) | (s2 << 1) | s1  # Posição do erro (se houver)

        # Corrigir o bit com erro, se necessário
        bits_corrigidos = [p1, p2, d1, p3, d2, d3, d4]
        if erro_pos != 0 and erro_pos <= 7:
            bits_corrigidos[erro_pos - 1] ^= 1  # Corrige o bit com erro

        # Extrai os 4 bits de dados corrigidos
        d1 = bits_corrigidos[2]
        d2 = bits_corrigidos[4]
        d3 = bits_corrigidos[5]
        d4 = bits_corrigidos[6]
        bits.extend([d1, d2, d3, d4])

        # Agrupa dois nibbles em 1 byte
        if len(bits) == 8:
            byte_result = sum([bit << (7 - i) for i, bit in enumerate(bits)])
            resultado.append(byte_result)
            bits.clear()
    return bytes(resultado)

def introduzir_erro(quadro: bytes, n_erros=1) -> bytes:
    """
    Inverte aleatoriamente 'n_erros' bits em um quadro de bytes.
    Utilizado para simular ruído ou falhas de transmissão no canal.
    """
    bits = [int(b) for byte in quadro for b in f"{byte:08b}"]
    
    for _ in range(n_erros):
        pos = random.randint(0, len(bits) - 1)
        bits[pos] ^= 1  # Inverte o bit na posição sorteada

    # Reagrupamento dos bits em bytes
    bytes_modificados = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bits):
                byte = (byte << 1) | bits[i + j]
        bytes_modificados.append(byte)
    
    return bytes(bytes_modificados)
