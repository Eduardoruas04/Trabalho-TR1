import gi
import numpy as np
from Camada_fisica import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas

# Carregar GTK3
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class InterfaceModulador(Gtk.Window):
    def __init__(self):
        super().__init__(title="Simulador de Camada Física")
        self.set_default_size(800, 600)

        # Layout principal
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        self.add(box)

        # Entrada de bits
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Digite os bits (ex: 1011001)")
        box.pack_start(self.entry, False, False, 0)

        # ComboBox para seleção de modulação
        self.combo = Gtk.ComboBoxText()
        self.combo.append_text("NRZ-Polar")
        self.combo.append_text("Manchester")
        self.combo.append_text("Bipolar")
        self.combo.append_text("ASK")
        self.combo.append_text("FSK")
        self.combo.append_text("8-QAM")
        self.combo.set_active(0)
        box.pack_start(self.combo, False, False, 0)

        # Botão
        botao = Gtk.Button(label="Executar Modulação")
        botao.connect("clicked", self.executar_modulacao)
        box.pack_start(botao, False, False, 0)

        # Área do gráfico
        self.figure, self.ax = plt.subplots(figsize=(8, 3))
        self.canvas = FigureCanvas(self.figure)
        box.pack_start(self.canvas, True, True, 0)

    def executar_modulacao(self, button):
        texto_bits = self.entry.get_text().strip()
        if not all(c in '01' for c in texto_bits):
            self.ax.clear()
            self.ax.set_title("Erro: Entrada inválida")
            self.canvas.draw()
            return

        bits = [int(b) for b in texto_bits]
        tipo = self.combo.get_active_text()

        # Seleciona modulação
        mod_func = {
            "NRZ-Polar": nrz_polar,
            "Manchester": manchester,
            "Bipolar": bipolar,
            "ASK": ask_modulation,
            "FSK": fsk_modulation,
            "8-QAM": qam8_modulation
        }[tipo]

        t, s = mod_func(bits)

        self.ax.clear()
        estilo = 'steps-post' if tipo in ["NRZ-Polar", "Manchester", "Bipolar"] else 'default'
        self.ax.plot(t, s, drawstyle=estilo)
        self.ax.set_title(f"Modulação {tipo}")
        self.ax.set_xlabel("Tempo")
        self.ax.set_ylabel("Amplitude")
        self.ax.grid(True)
        self.canvas.draw()

if __name__ == '__main__':
    win = InterfaceModulador()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
