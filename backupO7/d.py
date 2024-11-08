from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QSizePolicy, QSlider, QSpacerItem, QVBoxLayout, QWidget
from pyqtgraph.Qt import QtCore, QtWidgets
import pyqtgraph as pg
import numpy as np
import threading
import sys
import socket
from scipy.signal import butter, lfilter, iirnotch
import time

class Slider(QWidget):
    def __init__(self, minimum, maximum, initial_value, parent=None):
        super(Slider, self).__init__(parent=parent)
        self.verticalLayout = QVBoxLayout(self)
        self.label = QLabel(self)
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout = QHBoxLayout()
        self.spacerItem = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addSpacerItem(self.spacerItem)
        self.slider = QSlider(self)
        self.slider.setOrientation(Qt.Vertical)
        self.slider.setValue(int(initial_value))  # Convertir initial_value a entero
        self.horizontalLayout.addWidget(self.slider)
        self.spacerItem1 = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addSpacerItem(self.spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.resize(self.sizeHint())

        self.minimum = minimum
        self.maximum = maximum
        self.slider.valueChanged.connect(self.setLabelValue)
        self.x = None
        self.setLabelValue(self.slider.value())

    def setLabelValue(self, value):
        self.x = self.minimum + (float(value) / (self.slider.maximum() - self.slider.minimum())) * (
                self.maximum - self.minimum)
        self.label.setText("{0:.4g}".format(self.x))

class Scope(QWidget):
    def __init__(self, host, port):
        super(Scope, self).__init__()

        # Main layout
        self.horizontalLayout = QHBoxLayout(self)

        # Add sliders
        self.xRange_slider = Slider(1, 1000, 100)  # Lowpass slider, initial value should not be a fraction
        self.horizontalLayout.addWidget(self.xRange_slider)

        self.lowpass_slider = Slider(1, 150, 100)  # Lowpass slider, initial value should not be a fraction
        self.horizontalLayout.addWidget(self.lowpass_slider)
        self.highpass_slider = Slider(0.00001, 10, 0.00001)  # Highpass slider, initial value should not be a fraction
        self.horizontalLayout.addWidget(self.highpass_slider)
        self.notch_slider = Slider(10, 100, 20)  # Notch filter slider
        self.horizontalLayout.addWidget(self.notch_slider)

        # PyQtGraph window
        self.win = pg.GraphicsLayoutWidget(show=True, title="ECG Scope")
        self.verticalLayoutgraphs = QHBoxLayout(self)
        self.verticalLayoutgraphs.addWidget(self.win)
        self.horizontalLayout.addLayout(self.verticalLayoutgraphs)
        self.win.resize(1280, 720)
        self.win.setWindowTitle('Real-time ECG Data')

        # Add Real-time plot
        self.main_plot = self.win.addPlot(title="ECG Signal")
        self.y_min = 1.26  # Initial value
        self.y_max = 2.35  # Initial value
        self.Fs = 300
        self.sample_interval = 1 / self.Fs

        self.win.nextRow()
        self.fft_plot = self.win.addPlot(title="FFT of Raw Data")

        # Main plot setup
        self.main_plot.setYRange(self.y_min, self.y_max)
        self.main_plot.setLabel('left', 'ECG Value', '')
        self.main_plot.setLabel('bottom', 'Time', 's')

        # Create the plot
        self.graph = self.main_plot.plot()
        self.graph_pos = 0

        # Add FFT plot
        self.fft_plot.setLabel('left', 'Magnitude', '')
        self.fft_plot.setLabel('bottom', 'Frequency', 'Hz')

        # Variables for storing data
        self.buffer_size = 1000
        self.data = np.zeros(self.buffer_size)
        self.ptr = 0

        # FFT variables
        self.fft_sample_size = 1000
        self.fft_padding = 5
        self.fft_freq = np.fft.rfftfreq(self.fft_sample_size * self.fft_padding, 1 / self.Fs)
        self.fft_graph = self.fft_plot.plot()
        self.fft_graph_fft_mag = np.zeros(int((self.fft_sample_size * self.fft_padding) / 2) + 1)

        # Socket for data collection
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.socket_thread = threading.Thread(target=self.socket_read, daemon=True)

        # Timer to update graph
        self.plot_timer = QtCore.QTimer()
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(100)  # 2 ms timer

        # Connect sliders to update function
        self.xRange_slider.slider.valueChanged.connect(self.update_x_range)
        self.lowpass_slider.slider.valueChanged.connect(self.update_filters)
        self.highpass_slider.slider.valueChanged.connect(self.update_filters)
        self.notch_slider.slider.valueChanged.connect(self.update_filters)

        self.b_low, self.a_low = [0.06951437, 0.13902873, 0.06951437], [1, -1.1283145, 0.40637196]
        self.b_high, self.a_high = [0.06951437, 0.13902873, 0.06951437], [1, -1.1283145, 0.40637196]
        self.b_notch, self.a_notch = [0.06951437, 0.13902873, 0.06951437], [1, -1.1283145, 0.40637196]
        self.update_filters()
        self.last_time = time.perf_counter()
        self.current_time = time.perf_counter()

    def start(self):
        # Start thread to read data from socket
        self.socket_thread.start()

        # Main Loop
        app.exec_()

    def socket_read(self):
        self.socket.settimeout(1)
        start_time = time.time()
        data_count = 0
        data_oneth=0
        while True:

            try:
                data = self.socket.recv(1024).decode().strip()


                for value in data.split(','):
                    try:
                        value = float(value)
                        if data_oneth < 1000:
                            print(value)
                            data_oneth += 1
                        if self.ptr < self.buffer_size:
                            self.data[self.ptr] = value
                            self.ptr += 1
                            data_count += 1
                        else:
                            self.data[:-1] = self.data[1:]
                            self.data[-1] = value
                            data_count += 1
                    except ValueError:
                        pass
            except socket.timeout:
                pass
            elapsed_time = time.time() - start_time
            if elapsed_time >= 1.0:
                if data_oneth >= 1000:
                    print(f"Tasa de datos: {data_count} por segundo")

                data_count = 0
                start_time = time.time()

    def update_plot(self):
        filtered_data = self.apply_filters(
            self.data[:self.ptr] if self.ptr < self.buffer_size else self.data)
        self.graph.setData(filtered_data)
        self.main_plot.setXRange(max(0, self.ptr - self.buffer_size), self.ptr)

        if self.ptr >= self.fft_sample_size:
            self.calc_fft(filtered_data[-self.fft_sample_size:])

    def update_x_range(self):
        new_buffer_size = int(self.xRange_slider.x)
        if new_buffer_size != self.buffer_size:
            self.buffer_size = new_buffer_size
            self.fft_sample_size = new_buffer_size
            self.data = np.zeros(self.buffer_size)
            self.ptr = 0
            self.fft_padding = 5
            self.fft_freq = np.fft.rfftfreq(self.fft_sample_size * self.fft_padding, 1 / self.Fs)
            self.fft_graph_fft_mag = np.zeros(int((self.fft_sample_size * self.fft_padding) / 2) + 1)

    def update_filters(self):
        self.lowpass_cutoff = self.lowpass_slider.x
        self.highpass_cutoff = self.highpass_slider.x
        self.notch_freq = self.notch_slider.x

        # Ensure that the cutoff frequencies are within the valid range
        if 0 < self.lowpass_cutoff < 0.5 * self.Fs and 0 < self.highpass_cutoff < 0.5 * self.Fs:
            self.b_low, self.a_low = butter(2, self.lowpass_cutoff / (0.5 * self.Fs), btype='low')
            self.b_high, self.a_high = butter(2, self.highpass_cutoff / (0.5 * self.Fs), btype='high')
            self.b_notch, self.a_notch = iirnotch(self.notch_freq / (0.5 * self.Fs), 30)

    def apply_filters(self, data):
        try:
            filtered_data = lfilter(self.b_low, self.a_low, data)
            filtered_data = lfilter(self.b_high, self.a_high, filtered_data)
            filtered_data = lfilter(self.b_notch, self.a_notch, filtered_data)
        except:
            filtered_data = lfilter(self.b_low, self.a_low, data)
            filtered_data = lfilter(self.b_notch, self.a_notch, filtered_data)
        return filtered_data

    def calc_fft(self, data):
        # Remove DC offset
        data = data - np.mean(data)

        # FFT calculations
        ham = np.hamming(self.fft_sample_size)
        y_ham = data * ham
        self.fft_graph_fft_mag = 4 / self.fft_sample_size * np.abs(
            np.fft.rfft(y_ham, self.fft_sample_size * self.fft_padding))

        # Set FFT data
        self.fft_graph.setData(self.fft_freq, self.fft_graph_fft_mag)

    def exit(self):
        self.socket.close()
        sys.exit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    host = '192.168.4.1'  # Dirección IP del AP del ESP32
    port = 80
    scope = Scope(host, port)
    scope.show()
    scope.start()
