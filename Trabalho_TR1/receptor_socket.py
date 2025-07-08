# receptor_socket.py
import socket
import json
from Camada_enlace import (
    desenquadramento_contagem,
    desenquadramento_byte_stuffing,
    desenquadramento_bit_stuffing,
    decodificar_hamming,
    calcular_crc32_manual
)

HOST = '127.0.0.1'
PORT = 12345

def processar_recepcao(quadro_tx: bytes, metadata: dict) -> str:
    """
    Aplica a lógica de recepção com base nos metadados recebidos.
    Retorna a mensagem decodificada ou uma mensagem de erro.
    """
    print("\n--- PROCESSANDO DADOS NO RECEPTOR ---")
    try:
        err_tipo = metadata.get('err_tipo')
        enq_tipo = metadata.get('enq_tipo')

        # Seleciona a função de desenquadramento correta
        desenq_func = {
            "Contagem": desenquadramento_contagem,
            "Byte Stuffing": desenquadramento_byte_stuffing,
            "Bit Stuffing": desenquadramento_bit_stuffing
        }.get(enq_tipo)

        if not desenq_func:
            return "Erro: Tipo de enquadramento desconhecido."

        quadro_processado = b''
        status = "OK"

        # Usa a informação de erro dos metadados para decodificar
        if err_tipo == "Hamming":
            m_bits = metadata.get('m_bits', 4)
            quadro_processado = decodificar_hamming(quadro_tx, m=m_bits)
            status = "Dados recebidos e corrigidos por Hamming."
        
        elif err_tipo == "CRC":
            if len(quadro_tx) < 4:
                return "Erro: Quadro de CRC inválido."
            payload = quadro_tx[:-4]
            crc_recebido = int.from_bytes(quadro_tx[-4:], 'big')
            if crc_recebido != calcular_crc32_manual(payload):
                status = "ALERTA: Erro detectado pelo CRC!"
            else:
                status = "OK: Verificação de CRC bem-sucedida."
            quadro_processado = payload

        elif err_tipo == "Paridade":
            if len(quadro_tx) < 1:
                return "Erro: Quadro de paridade inválido."
            payload = quadro_tx[:-1]
            paridade = quadro_tx[-1]
            bits = ''.join(f'{b:08b}' for b in payload)
            if (bits.count('1') % 2 == 0 and paridade != 0) or \
               (bits.count('1') % 2 == 1 and paridade != 1):
                status = "ALERTA: Erro detectado pela Paridade!"
            else:
                status = "OK: Verificação de paridade bem-sucedida."
            quadro_processado = payload
        
        print(f"Status da verificação: {status}")

        # Aplica o desenquadramento no quadro já processado
        mensagem_final = desenq_func(quadro_processado).decode("utf-8", errors="replace")
        return mensagem_final

    except Exception as e:
        print(f"ERRO CRÍTICO DURANTE A RECEPÇÃO: {e}")
        return f"Falha na decodificação no receptor: {e}"


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Receptor aguardando conexão em {HOST}:{PORT}...")

        while True: # Loop para aceitar múltiplas conexões
            conn, addr = s.accept()
            with conn:
                print(f"\nConectado por {addr}")
                
                # 1. Receber Metadados
                # Primeiro, recebe 4 bytes que informam o tamanho dos metadados
                metadata_length_bytes = conn.recv(4)
                if not metadata_length_bytes:
                    continue
                metadata_length = int.from_bytes(metadata_length_bytes, 'big')
                
                # Agora, recebe a quantidade exata de bytes dos metadados
                metadata_json = conn.recv(metadata_length).decode('utf-8')
                metadata = json.loads(metadata_json)
                print(f"Metadados recebidos: {metadata}")

                # 2. Receber o Quadro de Dados
                quadro_tx = conn.recv(4096) # Recebe o quadro principal
                print(f"Quadro de dados recebido ({len(quadro_tx)} bytes)")

                print(f"\n[RX] Recebido {len(quadro_tx)} bytes do transmissor.")
                print(f" -> DADOS (hex): {quadro_tx.hex(' ')}")
                resposta = processar_recepcao(quadro_tx, metadata)
                
                # 3. Processar e obter a resposta
                resposta = processar_recepcao(quadro_tx, metadata)
                print(f"Mensagem decodificada: '{resposta}'")

                # 4. Enviar a resposta de volta ao transmissor
                conn.sendall(resposta.encode('utf-8'))
                print("Resposta enviada ao transmissor.")

if __name__ == '__main__':
    main()