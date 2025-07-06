from interface_gui import InterfaceModulador
from gi.repository import Gtk

if __name__ == '__main__':
    app = InterfaceModulador()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()
