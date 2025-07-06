import gi
import numpy as np
import random
import zlib
from Camada_fisica import *
from Camada_enlace import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def introduzir_erro(quadro: bytes, n_erros=1) -> bytes:
    bits = [int(b) for byte in quadro for b in f"{byte:08b}"]
    for _ in range(n_erros):
        pos = random.randint(0, len(bits) - 1)
        bits[pos] ^= 1  # inverte o bit
    resultado = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bits):
                byte = (byte << 1) | bits[i + j]
        resultado.append(byte)
    return bytes(resultado)


class InterfaceModulador(Gtk.Window):
    def __init__(self):
        super().__init__(title="Simulador de Comunicação")
        self.set_default_size(800, 600)
        self.set_border_width(10)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(box)

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Digite a mensagem a ser transmitida")
        box.pack_start(self.entry, False, False, 0)

        box.pack_start(Gtk.Label(label="--- TRANSMISSOR ---"), False, False, 5)

        self.combo = self.criar_combo(["NRZ-Polar", "Manchester", "Bipolar", "ASK", "FSK", "8-QAM"], box, "Modulação")
        self.enq_combo = self.criar_combo(["Contagem", "Byte Stuffing", "Bit Stuffing"], box, "Enquadramento")
        self.err_combo = self.criar_combo(["Paridade Par", "CRC-32", "Hamming"], box, "Detecção/Correção")

        # Checkbox de ruído
        self.check_ruido = Gtk.CheckButton(label="Simular erro no canal (ruído)")
        self.check_ruido.set_active(False)
        box.pack_start(self.check_ruido, False, False, 0)

        botao = Gtk.Button(label="Executar Simulação")
        botao.connect("clicked", self.executar_simulacao)
        box.pack_start(botao, False, False, 0)

        box.pack_start(Gtk.Label(label="Sinal gerado pelo Transmissor"), False, False, 5)
        self.figure, self.ax = plt.subplots(figsize=(8, 3))
        self.canvas = FigureCanvas(self.figure)
        box.pack_start(self.canvas, True, True, 0)

        box.pack_start(Gtk.Label(label="--- RECEPTOR ---"), False, False, 5)
        self.rx_label = Gtk.Label(label="Mensagem recebida: ")
        box.pack_start(self.rx_label, False, False, 5)

    def criar_combo(self, opcoes, box, titulo):
        box.pack_start(Gtk.Label(label=titulo), False, False, 0)
        combo = Gtk.ComboBoxText()
        for op in opcoes:
            combo.append_text(op)
        combo.set_active(0)
        box.pack_start(combo, False, False, 0)
        return combo

    def mostrar_erro(self, mensagem):
        dialog = Gtk.MessageDialog(parent=self, flags=0, message_type=Gtk.MessageType.ERROR,
                                   buttons=Gtk.ButtonsType.CLOSE, text=mensagem)
        dialog.run()
        dialog.destroy()

    def mostrar_alerta(self, mensagem):
        dialog = Gtk.MessageDialog(parent=self, flags=0, message_type=Gtk.MessageType.WARNING,
                                   buttons=Gtk.ButtonsType.OK, text=mensagem)
        dialog.run()
        dialog.destroy()

    def executar_simulacao(self, button):
        mensagem = self.entry.get_text().strip()
        if not mensagem:
            self.mostrar_erro("Mensagem vazia. Digite algo para transmitir.")
            return

        dados = mensagem.encode("utf-8")

        enq_tipo = self.enq_combo.get_active_text()
        try:
            if enq_tipo == "Contagem":
                quadro = enquadramento_contagem(dados)
                desenq_func = desenquadramento_contagem
            elif enq_tipo == "Byte Stuffing":
                quadro = enquadramento_byte_stuffing(dados)
                desenq_func = desenquadramento_byte_stuffing
            else:
                quadro = enquadramento_bit_stuffing(dados)
                desenq_func = desenquadramento_bit_stuffing
        except Exception as e:
            self.mostrar_erro(f"Erro no enquadramento: {e}")
            return

        err_tipo = self.err_combo.get_active_text()
        if err_tipo == "Paridade Par":
            quadro_tx = aplicar_paridade_par(quadro)
        elif err_tipo == "CRC-32":
            quadro_tx = aplicar_crc32(quadro)
        else:
            quadro_tx = codificar_hamming_7_4(quadro)

        # Simulação de ruído
        if self.check_ruido.get_active():
            quadro_tx = introduzir_erro(quadro_tx, n_erros=1)
            print("⚠️ Simulação de erro no canal: 1 bit invertido.")

        bits = [int(b) for byte in quadro_tx for b in f"{byte:08b}"]

        mod_tipo = self.combo.get_active_text()
        mod_func = {
            "NRZ-Polar": nrz_polar,
            "Manchester": manchester,
            "Bipolar": bipolar,
            "ASK": ask_modulation,
            "FSK": fsk_modulation,
            "8-QAM": qam8_modulation
        }.get(mod_tipo)

        if not mod_func:
            self.mostrar_erro("Tipo de modulação inválido.")
            return

        t, s = mod_func(bits)

        self.ax.clear()
        estilo = 'steps-post' if mod_tipo in ["NRZ-Polar", "Manchester", "Bipolar"] else 'default'
        self.ax.plot(t[:3000], s[:3000], drawstyle=estilo)  # mostra apenas os primeiros pontos
        self.ax.set_title(f"Transmissor: {mod_tipo} após {enq_tipo} + {err_tipo}")
        self.ax.set_xlabel("Tempo")
        self.ax.set_ylabel("Amplitude")
        self.ax.grid(True)
        self.canvas.draw()

        # RECEPTOR
        try:
            if err_tipo == "Hamming":
                quadro_corrigido = decodificar_hamming_7_4(quadro_tx)
                quadro_rx = desenq_func(quadro_corrigido)
                if self.check_ruido.get_active():
                    self.mostrar_alerta("Erro detectado e corrigido por Hamming.")
            elif err_tipo == "Paridade Par":
                recebido = quadro_tx[:-1]
                paridade = quadro_tx[-1]
                bits_check = ''.join(f'{b:08b}' for b in recebido)
                if (bits_check.count('1') % 2 == 0 and paridade != 0) or \
                   (bits_check.count('1') % 2 == 1 and paridade != 1):
                    self.mostrar_alerta("Erro detectado no canal pela Paridade.")
                quadro_rx = desenq_func(recebido)
            elif err_tipo == "CRC-32":
                recebido = quadro_tx[:-4]
                crc_recebido = int.from_bytes(quadro_tx[-4:], 'big')
                crc_calc = zlib.crc32(recebido) & 0xFFFFFFFF
                if crc_recebido != crc_calc:
                    self.mostrar_alerta("Erro detectado no canal pelo CRC.")
                quadro_rx = desenq_func(recebido)

            mensagem_rx = quadro_rx.decode("utf-8", errors="replace")
        except Exception as e:
            mensagem_rx = f"[Erro na recepção: {e}]"

        print("\n===== TRANSMISSOR =====")
        print("Mensagem transmitida:", mensagem)
        print("Bits transmitidos:", bits)

        print("\n===== RECEPTOR =====")
        print("Mensagem recebida:", mensagem_rx)
        self.rx_label.set_text("Mensagem recebida: " + mensagem_rx)
