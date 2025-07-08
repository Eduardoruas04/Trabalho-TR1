
from interface_gui import InterfaceTransmissor
from gi.repository import Gtk

if __name__ == '__main__':
    app = InterfaceTransmissor()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()