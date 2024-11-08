import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QFileDialog, QComboBox, QSlider
from PyQt5.QtCore import Qt, QTimer

class SerialSimulatorApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Estado inicial de variables
        self.serial_port = None
        self.serial_ports = []  # Lista de puertos serial disponibles
        self.simulation_data = []
        self.simulation_index = 0
        self.timer = QTimer(self)

        # Configuración de la interfaz
        self.initUI()

    def initUI(self):
        # Botón para refrescar puertos USB disponibles
        self.refresh_button = QPushButton('Refrescar Puertos', self)
        #self.refresh_button.setFixedSize(20,20)

        self.refresh_button.clicked.connect(self.refresh_ports)

        # ComboBox para seleccionar el puerto serial
        self.port_selector = QComboBox(self)
        self.port_selector.activated[str].connect(self.select_port)

        # Botón para seleccionar archivo de simulación
        self.file_button = QPushButton('Seleccionar Archivo', self)
        self.file_button.clicked.connect(self.select_file)

        # Etiqueta para mostrar información sobre el puerto seleccionado
        self.port_label = QLabel('Puerto seleccionado: Ninguno', self)

        # Slider de la línea de tiempo para la simulación
        self.timeline_slider = QSlider(Qt.Horizontal, self)
        self.timeline_slider.setMinimum(0)
        self.timeline_slider.setTickPosition(QSlider.TicksBelow)
        self.timeline_slider.setTickInterval(1)
        self.timeline_slider.sliderMoved.connect(self.slider_moved)

        # Botón para iniciar la simulación
        self.start_button = QPushButton('Iniciar Simulación', self)
        self.start_button.clicked.connect(self.start_simulation)

        # Layouts de la interfaz
        vbox = QVBoxLayout()
        vbox.addWidget(self.refresh_button)
        vbox.addWidget(self.port_selector)
        vbox.addWidget(self.file_button)
        vbox.addWidget(self.port_label)
        vbox.addWidget(self.timeline_slider)
        vbox.addWidget(self.start_button)

        # Configurar el widget central
        widget = QWidget()
        widget.setLayout(vbox)
        self.setCentralWidget(widget)

        self.setWindowTitle('Simulador Serial')
        self.setGeometry(100, 100, 400, 200)

    def refresh_ports(self):
        # Refrescar la lista de puertos serial disponibles
        self.serial_ports = serial.tools.list_ports.comports()
        self.port_selector.clear()
        for port in self.serial_ports:
            self.port_selector.addItem(port.device)

    def select_port(self, port_name):
        # Seleccionar el puerto serial a utilizar
        self.port_label.setText(f'Puerto seleccionado: {port_name}')
        self.serial_port = port_name

    def select_file(self):
        # Seleccionar un archivo para simulación
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo de simulación", "", "Archivos de texto (*.txt);;Todos los archivos (*)", options=options)
        if file_name:
            self.port_label.setText(f'Archivo seleccionado: {file_name}')
            with open(file_name, 'r') as file:
                self.simulation_data = file.readlines()
            self.timeline_slider.setMaximum(len(self.simulation_data) - 1)
            self.simulation_index = 0

    def start_simulation(self):
        # Iniciar la simulación si se ha seleccionado un archivo o puerto
        if self.simulation_data:
            self.timer.timeout.connect(self.update_simulation)
            self.timer.start(1000)  # Actualizar cada segundo
        else:
            print("No se ha seleccionado un archivo de simulación.")

    def update_simulation(self):
        # Actualizar la simulación, mostrando la línea correspondiente
        if self.simulation_index < len(self.simulation_data):
            data = self.simulation_data[self.simulation_index]
            print(f"Simulando datos: {data.strip()}")
            self.simulation_index += 1
            self.timeline_slider.setValue(self.simulation_index)
        else:
            self.timer.stop()

    def slider_moved(self, position):
        # Cambiar la posición de la simulación cuando se mueve el slider
        self.simulation_index = position
        print(f"Posición de simulación cambiada a: {position}")
        if self.simulation_data:
            data = self.simulation_data[self.simulation_index]
            print(f"Simulando datos: {data.strip()}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SerialSimulatorApp()
    window.show()
    sys.exit(app.exec_())
