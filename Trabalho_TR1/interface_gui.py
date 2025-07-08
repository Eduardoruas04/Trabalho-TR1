import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import socket
from Camada_enlace import *
from Camada_fisica import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
import json

class InterfaceTransmissor(Gtk.Window):
    def __init__(self):
        super().__init__(title="Transmissor")
        self.set_default_size(800, 600)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(box)

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Digite a mensagem a ser transmitida")
        box.pack_start(self.entry, False, False, 0)

        # --- CONTROLES DE CONFIGURAÇÃO ---
        self.combo_mod = self.criar_combo(["NRZ-Polar", "Manchester", "Bipolar", "ASK", "FSK", "8-QAM"], box, "Modulação")
        self.combo_enq = self.criar_combo(["Contagem", "Byte Stuffing", "Bit Stuffing"], box, "Enquadramento")
        self.combo_err = self.criar_combo(["Paridade", "CRC", "Hamming"], box, "Detecção/Correção")

        # --- CÓDIGO  PARA A TAXA DE ERRO ---
    
        box.pack_start(Gtk.Label(label="Taxa de Erro (%) "), False, False, 0)
        # Cria um ajuste para o SpinButton: valor inicial 0, mínimo 0, máximo 100, passo 0.1
        ajuste = Gtk.Adjustment(value=0, lower=0, upper=100, step_increment=0.1, page_increment=1.0)
        self.spin_taxa_erro = Gtk.SpinButton(adjustment=ajuste, climb_rate=0.1, digits=2)
        box.pack_start(self.spin_taxa_erro, False, False, 5)
       

        # --- BOTÃO DE AÇÃO ---
        enviar_btn = Gtk.Button(label="Enviar Mensagem")
        enviar_btn.connect("clicked", self.enviar_mensagem)
        box.pack_start(enviar_btn, False, False, 0)

        # --- ÁREA DE RESULTADO E GRÁFICO ---
        self.resultado = Gtk.Label(label="Mensagem recebida: (aguardando)")
        box.pack_start(self.resultado, False, False, 0)

        self.figure, self.ax = plt.subplots(figsize=(8, 2))
        self.canvas = FigureCanvas(self.figure)
        box.pack_start(self.canvas, True, True, 0)

    def criar_combo(self, opcoes, box, titulo):
        box.pack_start(Gtk.Label(label=titulo), False, False, 0)
        combo = Gtk.ComboBoxText()
        for op in opcoes:
            combo.append_text(op)
        combo.set_active(0)
        box.pack_start(combo, False, False, 0)
        return combo

    def enviar_mensagem(self, widget):
        msg = self.entry.get_text()
        if not msg:
            self.resultado.set_text("Mensagem vazia.")
            return

        dados = msg.encode('utf-8')
        tipo_mod = self.combo_mod.get_active_text()
        tipo_enq = self.combo_enq.get_active_text()
        tipo_err = self.combo_err.get_active_text()

        # --- Lógica de Enquadramento e Erro (igual a antes) ---
        if tipo_enq == "Contagem":
            quadro = enquadramento_contagem(dados)
        elif tipo_enq == "Byte Stuffing":
            quadro = enquadramento_byte_stuffing(dados)
        else: # Bit Stuffing
            quadro = enquadramento_bit_stuffing(dados)

        m_bits_hamming = 4  # m=4 para Hamming(7,4)
        if tipo_err == "Paridade":
            quadro_tx = aplicar_paridade_par(quadro)
        elif tipo_err == "CRC":
            quadro_tx = aplicar_crc32(quadro)
        else: # Hamming
            quadro_tx = codificar_hamming(quadro, m=m_bits_hamming)
        taxa_percentual = self.spin_taxa_erro.get_value()

        if taxa_percentual > 0:
            taxa_decimal = taxa_percentual / 100.0
            print("\nSIMULANDO ERRO NO CANAL POR TAXA\n")
            # AQUI É O PONTO CRÍTICO: quadro_tx é REATRIBUÍDO com a versão com erro
            quadro_tx = introduzir_erro_por_taxa(quadro_tx, taxa_de_erro=taxa_decimal)
            print("\nFIM DA SIMULAÇÃO DE ERRO\n")

     # Lógica de Modulação e Gráfico 
        bits = [int(b) for byte in quadro_tx for b in f"{byte:08b}"]
        mod_func = {
            "NRZ-Polar": nrz_polar, "Manchester": manchester, "Bipolar": bipolar,
            "ASK": ask_modulation, "FSK": fsk_modulation, "8-QAM": qam8_modulation
        }.get(tipo_mod, nrz_polar)
        t, s = mod_func(bits)
        self.ax.clear()
        estilo = 'steps-post' if tipo_mod in ["NRZ-Polar", "Manchester", "Bipolar"] else 'default'
        self.ax.plot(t[:3000], s[:3000], drawstyle=estilo)
        self.ax.set_title(f"Sinal modulado: {tipo_mod}")
        self.ax.grid(True)
        self.canvas.draw()

        # Envio via Socket (envia o quadro_tx final)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(("127.0.0.1", 12345))

                # 1. Preparar e enviar metadados
                metadata = {
                    "enq_tipo": tipo_enq,
                    "err_tipo": tipo_err,
                    "m_bits": m_bits_hamming if tipo_err == "Hamming" else 0
                }
                metadata_bytes = json.dumps(metadata).encode('utf-8')
                
                # Envia o tamanho dos metadados (cabeçalho de 4 bytes)
                sock.sendall(len(metadata_bytes).to_bytes(4, 'big'))
                # Envia os metadados
                sock.sendall(metadata_bytes)
                
                # 2. Enviar o quadro de dados principal
                sock.sendall(quadro_tx)
                
                # 3. Receber a resposta do servidor
                resposta = sock.recv(1024)
                self.resultado.set_text("Mensagem recebida no receptor: " + resposta.decode('utf-8'))
                print(f"\n[TX] Enviando {len(quadro_tx)} bytes para o receptor...")
                print(f" -> DADOS (hex): {quadro_tx.hex(' ')}")
                sock.sendall(quadro_tx)

        except ConnectionRefusedError:
            self.resultado.set_text("Erro: Conexão recusada. O receptor está rodando?")
        except Exception as e:
            self.resultado.set_text("Erro de comunicação: " + str(e))

if __name__ == "__main__":
    win = InterfaceTransmissor()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
