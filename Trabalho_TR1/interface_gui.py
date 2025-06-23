import gi
import numpy as np
from Camada_fisica import *
from Camada_enlace import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas

# Carregar GTK3
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class InterfaceModulador(Gtk.Window):
    def __init__(self):
        super().__init__(title="Simulador de Comunicação")
        self.set_default_size(800, 600)

        # Layout principal
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        self.add(box)

        # Entrada de texto
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Digite a mensagem a ser transmitida")
        box.pack_start(self.entry, False, False, 0)

        # ComboBox para tipo de modulação
        self.combo = Gtk.ComboBoxText()
        self.combo.append_text("NRZ-Polar")
        self.combo.append_text("Manchester")
        self.combo.append_text("Bipolar")
        self.combo.append_text("ASK")
        self.combo.append_text("FSK")
        self.combo.append_text("8-QAM")
        self.combo.set_active(0)
        box.pack_start(self.combo, False, False, 0)

        # ComboBox para tipo de enquadramento
        self.enq_combo = Gtk.ComboBoxText()
        self.enq_combo.append_text("Contagem")
        self.enq_combo.append_text("Byte Stuffing")
        self.enq_combo.append_text("Bit Stuffing")
        self.enq_combo.set_active(0)
        box.pack_start(self.enq_combo, False, False, 0)

        # ComboBox para detecção de erros
        self.err_combo = Gtk.ComboBoxText()
        self.err_combo.append_text("Paridade Par")
        self.err_combo.append_text("CRC-32")
        self.err_combo.append_text("Hamming")
        self.err_combo.set_active(0)
        box.pack_start(self.err_combo, False, False, 0)

        # Botão de execução
        botao = Gtk.Button(label="Executar Simulação")
        botao.connect("clicked", self.executar_simulacao)
        box.pack_start(botao, False, False, 0)

        # Área do gráfico
        self.figure, self.ax = plt.subplots(figsize=(8, 3))
        self.canvas = FigureCanvas(self.figure)
        box.pack_start(self.canvas, True, True, 0)

    def executar_simulacao(self, button):
        mensagem = self.entry.get_text().strip()
        if not mensagem:
            self.ax.clear()
            self.ax.set_title("Erro: mensagem vazia")
            self.canvas.draw()
            return

        dados = mensagem.encode("utf-8")

        # ENQUADRAMENTO
        enq_tipo = self.enq_combo.get_active_text()
        if enq_tipo == "Contagem":
            quadro = enquadramento_contagem(dados)
            quadro_rx = desenquadramento_contagem(quadro)
        elif enq_tipo == "Byte Stuffing":
            quadro = enquadramento_byte_stuffing(dados)
            quadro_rx = desenquadramento_byte_stuffing(quadro)
        else:
            quadro = enquadramento_bit_stuffing(dados)
            quadro_rx = desenquadramento_bit_stuffing(quadro)

        # DETECÇÃO OU CORREÇÃO DE ERRO (transmissor)
        err_tipo = self.err_combo.get_active_text()
        if err_tipo == "Paridade Par":
            quadro = aplicar_paridade_par(quadro)
        elif err_tipo == "CRC-32":
            quadro = aplicar_crc32(quadro)
        else:
            quadro = aplicar_hamming(quadro)

        # CONVERSÃO EM BITS PARA MODULAÇÃO
        bits = [int(b) for byte in quadro for b in f"{byte:08b}"]

        # MODULAÇÃO
        mod_tipo = self.combo.get_active_text()
        mod_func = {
            "NRZ-Polar": nrz_polar,
            "Manchester": manchester,
            "Bipolar": bipolar,
            "ASK": ask_modulation,
            "FSK": fsk_modulation,
            "8-QAM": qam8_modulation
        }[mod_tipo]

        t, s = mod_func(bits)

        # PLOTAR
        self.ax.clear()
        estilo = 'steps-post' if mod_tipo in ["NRZ-Polar", "Manchester", "Bipolar"] else 'default'
        self.ax.plot(t, s, drawstyle=estilo)
        self.ax.set_title(f"Transmissor: {mod_tipo} após {enq_tipo} + {err_tipo}")
        self.ax.set_xlabel("Tempo")
        self.ax.set_ylabel("Amplitude")
        self.ax.grid(True)
        self.canvas.draw()

        # EXIBIR MENSAGEM DECODIFICADA (simulação de recepção)
        print("Mensagem transmitida:", mensagem)
        print("Mensagem recebida:", quadro_rx.decode("utf-8", errors='ignore'))

if __name__ == '__main__':
    win = InterfaceModulador()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
