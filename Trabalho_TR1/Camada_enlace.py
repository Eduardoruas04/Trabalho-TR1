import numpy as np
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

# --- INÍCIO DA IMPLEMENTAÇÃO MANUAL DO CRC-32 ---

def gerar_tabela_crc32() -> tuple:
    """
    Gera a tabela de consulta para o cálculo rápido do CRC-32.
    O polinômio 0xEDB88320 é a representação refletida do polinômio padrão.
    """
    polinomio_refletido = 0xEDB88320
    tabela_crc = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ polinomio_refletido
            else:
                crc = crc >> 1
        tabela_crc.append(crc)
    return tuple(tabela_crc)

# A tabela é gerada uma única vez quando o módulo é carregado
CRC32_TABLE = gerar_tabela_crc32()

def calcular_crc32_manual(dados: bytes) -> int:
    """
    Calcula o checksum CRC-32 (padrão IEEE 802.3) para um conjunto de dados.
    """
    crc = 0xFFFFFFFF
    for byte in dados:
        indice = (crc ^ byte) & 0xFF
        crc = (crc >> 8) ^ CRC32_TABLE[indice]
    return crc ^ 0xFFFFFFFF

def aplicar_crc32(dados: bytes) -> bytes:
    """
    Aplica o código de redundância cíclica (CRC-32) padrão IEEE 802.
    Anexa ao final do quadro 4 bytes correspondentes ao checksum.
    """
    # Linha original foi substituída:
    # crc = zlib.crc32(dados) & 0xFFFFFFFF
    crc = calcular_crc32_manual(dados)
    return dados + crc.to_bytes(4, 'big')

# --- FIM DA IMPLEMENTAÇÃO DO CRC-32 ---


# === CORREÇÃO DE ERROS (HAMMING n,m) ===

def calcular_bits_paridade(m: int) -> int:
    """
    Calcula o número de bits de paridade (r) necessários para m bits de dados.
    A condição de Hamming é: 2^r >= m + r + 1.
    """
    r = 1
    while 2**r < m + r + 1:
        r += 1
    return r

def codificar_hamming(dados: bytes, m: int) -> bytes:
    """
    Codifica dados usando o código de Hamming com m bits de dados.
    Os bits de paridade (r) são calculados e os blocos (n=m+r) são formados.
    """
    if m < 1:
        raise ValueError("O número de bits de dados (m) deve ser pelo menos 1.")

    r = calcular_bits_paridade(m)
    n = m + r

    # 1. Converter bytes de entrada em um fluxo de bits
    bits_dados = [int(b) for byte in dados for b in f"{byte:08b}"]
    
    # Adicionar padding para que o total de bits seja múltiplo de m
    if len(bits_dados) % m != 0:
        bits_dados.extend([0] * (m - (len(bits_dados) % m)))

    bits_codificados = []
    # 2. Processar em blocos de m bits
    for i in range(0, len(bits_dados), m):
        bloco = bits_dados[i:i+m]
        
        # 3. Construir o bloco codificado (n bits)
        codeword = [0] * n
        idx_dados = 0
        # Inserir bits de dados nas posições que não são potência de 2
        for j in range(n):
            pos = j + 1
            if (pos & (pos - 1)) != 0:  # Se não for potência de 2
                if idx_dados < len(bloco):
                    codeword[j] = bloco[idx_dados]
                    idx_dados += 1
        
        # 4. Calcular e inserir os bits de paridade
        for j in range(r):
            pos_paridade = 2**j
            xor_val = 0
            for k in range(n):
                pos_dado = k + 1
                if (pos_dado != pos_paridade) and (pos_dado & pos_paridade):
                    xor_val ^= codeword[k]
            codeword[pos_paridade - 1] = xor_val
        
        bits_codificados.extend(codeword)
        
    # 5. Converter o fluxo de bits codificados de volta para bytes
    # Adicionar padding para que o total seja múltiplo de 8
    if len(bits_codificados) % 8 != 0:
        bits_codificados.extend([0] * (8 - (len(bits_codificados) % 8)))
        
    resultado_bytes = bytearray()
    for i in range(0, len(bits_codificados), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits_codificados[i+j]
        resultado_bytes.append(byte)
        
    return bytes(resultado_bytes)


def decodificar_hamming(codigo: bytes, m: int) -> bytes:
    """
    Decodifica e corrige erros em dados codificados com Hamming(n, m).
    """
    if m < 1:
        raise ValueError("O número de bits de dados (m) deve ser pelo menos 1.")

    r = calcular_bits_paridade(m)
    n = m + r
    
    # 1. Converter bytes codificados em um fluxo de bits
    bits_codificados = [int(b) for byte in codigo for b in f"{byte:08b}"]

    bits_decodificados = []
    # 2. Processar em blocos de n bits
    for i in range(0, len(bits_codificados), n):
        bloco = bits_codificados[i:i+n]
        if len(bloco) < n:
            continue # Ignora blocos incompletos (padding)

        # 3. Calcular a síndrome para detectar/localizar o erro
        pos_erro = 0
        for j in range(r):
            pos_paridade = 2**j
            xor_val = 0
            for k in range(n):
                pos_atual = k + 1
                if pos_atual & pos_paridade:
                    xor_val ^= bloco[k]
            
            if xor_val != 0:
                pos_erro += pos_paridade
        
        # 4. Corrigir o erro, se houver
        if pos_erro > 0 and pos_erro <= n:
            bloco[pos_erro - 1] ^= 1 # Inverte o bit errado

        # 5. Extrair os bits de dados originais
        idx_dados = 0
        for j in range(n):
            pos = j + 1
            if (pos & (pos - 1)) != 0: # Se não for potência de 2
                bits_decodificados.append(bloco[j])

    # 6. Converter o fluxo de bits decodificados de volta para bytes
    resultado_bytes = bytearray()
    for i in range(0, len(bits_decodificados) - 7, 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits_decodificados[i+j]
        resultado_bytes.append(byte)
        
    return bytes(resultado_bytes)

def introduzir_erro_por_taxa(dados: bytes, taxa_de_erro: float) -> bytes:
    """
    Inverte bits em um quadro de dados com base em uma taxa de erro probabilística.

    Args:
        dados: O quadro de bytes original.
        taxa_de_erro: A probabilidade (entre 0.0 e 1.0) de um bit ser invertido.
    """
    if not (0.0 <= taxa_de_erro <= 1.0):
        raise ValueError("A taxa de erro deve estar entre 0.0 e 1.0")

    # Converte os bytes para uma lista mutável de bits (0s e 1s)
    bits = [int(b) for byte in dados for b in f"{byte:08b}"]
    
    erros_introduzidos = 0
    # Percorre cada bit
    for i in range(len(bits)):
        # Sorteia um número aleatório entre 0 e 1
        if random.random() < taxa_de_erro:
            # Se o número sorteado for menor que a taxa, inverte o bit
            bits[i] ^= 1  # Operação XOR para inverter (0->1, 1->0)
            erros_introduzidos += 1
            
    print(f"Taxa de erro de {taxa_de_erro*100:.2f}% aplicada. Total de {erros_introduzidos} bits invertidos.")

    # Reagrupa os bits de volta em bytes
    bytes_modificados = bytearray()
    for i in range(0, len(bits), 8):
        byte_str = "".join(map(str, bits[i:i+8]))
        bytes_modificados.append(int(byte_str, 2))
    
    return bytes(bytes_modificados)