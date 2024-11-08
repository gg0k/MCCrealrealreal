from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QSizePolicy, QSlider, QSpacerItem, QVBoxLayout, QWidget
from pyqtgraph.Qt import QtCore, QtWidgets
import pyqtgraph as pg
import numpy as np
import threading
import sys
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
    def __init__(self):
        super(Scope, self).__init__()

        # Main layout
        self.horizontalLayout = QHBoxLayout(self)

        # Add sliders
        self.xRange_slider = Slider(1, 1000, 300)  # Lowpass slider, initial value should not be a fraction
        self.horizontalLayout.addWidget(self.xRange_slider)


        self.lowpass_slider = Slider(1, 150, 50)  # Lowpass slider, initial value should not be a fraction
        self.horizontalLayout.addWidget(self.lowpass_slider)
        self.highpass_slider = Slider(0.00001, 1, 0.00001)  # Highpass slider, initial value should not be a fraction
        self.horizontalLayout.addWidget(self.highpass_slider)
        self.notch_slider = Slider(40, 60, 50)  # Notch filter slider
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
        self.fft_plot.setYRange(0, 0.5)

        # Variables for storing data
        self.buffer_size = 1000
        self.data = np.zeros(self.buffer_size)
        self.c = 0
        self.elapsed_time = 0.0033
        # FFT variables
        self.fft_sample_size = 1000
        self.fft_padding = 5
        self.fft_freq = np.fft.rfftfreq(self.fft_sample_size * self.fft_padding, self.elapsed_time)
        self.fft_graph = self.fft_plot.plot()
        self.fft_graph_fft_mag = np.zeros(int((self.fft_sample_size * self.fft_padding) / 2) + 1)

        # 1000 data list
        self.lista_data = [1.62, 1.61, 1.45, 1.33, 1.38, 1.5, 1.64, 1.58, 1.38, 1.33, 1.44, 1.62, 1.61, 1.38, 1.33, 1.38, 1.57, 1.63, 1.52, 1.38, 1.33, 1.44, 1.62, 1.61, 1.51, 1.33, 1.35, 1.51, 1.64, 1.61, 1.44, 1.32, 1.38, 1.58, 1.64, 1.51, 1.33, 1.35, 1.45, 1.63, 1.57, 1.37, 1.33, 1.44, 1.62, 1.56, 1.44, 1.32, 1.39, 1.58, 1.63, 1.56, 1.37, 1.33, 1.45, 1.63, 1.63, 1.5, 1.33, 1.35, 1.52, 1.63, 1.61, 1.43, 1.33, 1.39, 1.52, 1.64, 1.56, 1.36, 1.34, 1.39, 1.59, 1.62, 1.5, 1.33, 1.34, 1.45, 1.63, 1.6, 1.42, 1.33, 1.36, 1.53, 1.64, 1.6, 1.42, 1.32, 1.39, 1.59, 1.64, 1.56, 1.36, 1.34, 1.46, 1.63, 1.6, 1.42, 1.33, 1.4, 1.36, 1.36, 1.46, 1.63, 1.59, 1.41, 1.32, 1.36, 1.53, 1.64, 1.55, 1.35, 1.32, 1.4, 1.6, 1.62, 1.48, 1.33, 1.34, 1.47, 1.64, 1.6, 1.41, 1.33, 1.36, 1.54, 1.64, 1.55, 1.41, 1.33, 1.41, 1.6, 1.62, 1.55, 1.35, 1.34, 1.48, 1.64, 1.62, 1.47, 1.32, 1.37, 1.55, 1.64, 1.54, 1.35, 1.34, 1.41, 1.64, 1.59, 1.4, 1.33, 1.37, 1.55, 1.64, 1.54, 1.4, 1.33, 1.41, 1.61, 1.59, 1.4, 1.33, 1.42, 1.61, 1.64, 1.54, 1.35, 1.34, 1.49, 1.64, 1.59, 1.39, 1.33, 1.37, 1.56, 1.64, 1.54, 1.34, 1.33, 1.42, 1.62, 1.62, 1.53, 1.34, 1.35, 1.49, 1.64, 1.62, 1.46, 1.32, 1.37, 1.56, 1.64, 1.58, 1.39, 1.33, 1.43, 1.56, 1.64, 1.5, 1.64, 1.52, 1.34, 1.35, 1.43, 1.62, 1.61, 1.45, 1.32, 1.35, 1.5, 1.64, 1.58, 1.45, 1.32, 1.38, 1.62, 1.63, 1.52, 1.33, 1.35, 1.5, 1.64, 1.58, 1.45, 1.32, 1.38, 1.57, 1.63, 1.57, 1.37, 1.33, 1.44, 1.63, 1.61, 1.51, 1.33, 1.35, 1.51, 1.64, 1.61, 1.44, 1.32, 1.39, 1.58, 1.64, 1.57, 1.37, 1.33, 1.45, 1.58, 1.63, 1.51, 1.33, 1.36, 1.45, 1.63, 1.61, 1.43, 1.33, 1.35, 1.52, 1.64, 1.57, 1.44, 1.33, 1.39, 1.59, 1.63, 1.56, 1.37, 1.34, 1.46, 1.64, 1.61, 1.5, 1.33, 1.36, 1.52, 1.64, 1.56, 1.43, 1.33, 1.4, 1.59, 1.63, 1.56, 1.37, 1.34, 1.46, 1.63, 1.63, 1.49, 1.33, 1.36, 1.53, 1.63, 1.6, 1.42, 1.55, 1.36, 1.34, 1.46, 1.64, 1.6, 1.42, 1.33, 1.36, 1.54, 1.64, 1.55, 1.41, 1.33, 1.41, 1.6, 1.64, 1.55, 1.35, 1.34, 1.47, 1.64, 1.63, 1.48, 1.33, 1.36, 1.54, 1.64, 1.54, 1.41, 1.33, 1.41, 1.61, 1.62, 1.48, 1.33, 1.36, 1.48, 1.64, 1.59, 1.41, 1.33, 1.37, 1.55, 1.64, 1.54, 1.4, 1.33, 1.41, 1.61, 1.62, 1.54, 1.35, 1.34, 1.48, 1.64, 1.59, 1.4, 1.33, 1.37, 1.56, 1.64, 1.54, 1.4, 1.33, 1.42, 1.62, 1.62, 1.53, 1.34, 1.34, 1.49, 1.64, 1.62, 1.47, 1.33, 1.37, 1.56, 1.64, 1.59, 1.39, 1.33, 1.38, 1.56, 1.64, 1.53, 1.34, 1.33, 1.43, 1.62, 1.62, 1.46, 1.34, 1.35, 1.5, 1.64, 1.58, 1.46, 1.33, 1.38, 1.33, 1.44, 1.62, 1.61, 1.45, 1.33, 1.35, 1.5, 1.64, 1.57, 1.38, 1.33, 1.38, 1.57, 1.63, 1.52, 1.38, 1.33, 1.44, 1.62, 1.61, 1.51, 1.34, 1.35, 1.51, 1.64, 1.57, 1.44, 1.33, 1.39, 1.58, 1.64, 1.51, 1.34, 1.35, 1.51, 1.64, 1.57, 1.38, 1.33, 1.44, 1.58, 1.63, 1.51, 1.33, 1.36, 1.45, 1.63, 1.6, 1.44, 1.33, 1.39, 1.58, 1.64, 1.56, 1.37, 1.34, 1.45, 1.59, 1.63, 1.5, 1.33, 1.36, 1.53, 1.64, 1.56, 1.43, 1.33, 1.4, 1.59, 1.64, 1.56, 1.37, 1.34, 1.46, 1.59, 1.63, 1.5, 1.33, 1.36, 1.46, 1.63, 1.6, 1.43, 1.33, 1.37, 1.53, 1.64, 1.56, 1.37, 1.33, 1.4, 1.59, 1.62, 1.49, 1.33, 1.34, 1.47, 1.64, 1.6, 1.54, 1.64, 1.55, 1.36, 1.34, 1.47, 1.6, 1.62, 1.49, 1.33, 1.37, 1.47, 1.64, 1.59, 1.41, 1.33, 1.41, 1.6, 1.64, 1.55, 1.36, 1.34, 1.48, 1.61, 1.62, 1.48, 1.33, 1.37, 1.48, 1.64, 1.59, 1.41, 1.33, 1.41, 1.54, 1.64, 1.54, 1.35, 1.35, 1.48, 1.61, 1.62, 1.47, 1.33, 1.37, 1.55, 1.64, 1.54, 1.4, 1.33, 1.42, 1.61, 1.64, 1.54, 1.35, 1.34, 1.49, 1.61, 1.62, 1.47, 1.33, 1.37, 1.55, 1.63, 1.58, 1.4, 1.33, 1.42, 1.61, 1.64, 1.47, 1.33, 1.35, 1.49, 1.64, 1.58, 1.39, 1.33, 1.38, 1.56, 1.64, 1.53, 1.39, 1.33, 1.43, 1.62, 1.62, 1.53, 1.34, 1.35, 1.5, 1.62, 1.61, 1.46, 1.33, 1.38, 1.5, 1.64, 1.58, 1.39, 1.64, 1.45, 1.34, 1.35, 1.51, 1.64, 1.58, 1.45, 1.33, 1.38, 1.57, 1.63, 1.58, 1.38, 1.33, 1.44, 1.63, 1.61, 1.45, 1.32, 1.39, 1.51, 1.65, 1.58, 1.38, 1.33, 1.38, 1.58, 1.63, 1.51, 1.38, 1.33, 1.58, 1.63, 1.57, 1.38, 1.34, 1.45, 1.63, 1.63, 1.51, 1.33, 1.36, 1.52, 1.63, 1.61, 1.44, 1.33, 1.39, 1.52, 1.64, 1.57, 1.37, 1.34, 1.39, 1.58, 1.63, 1.5, 1.37, 1.33, 1.45, 1.63, 1.6, 1.5, 1.33, 1.36, 1.52, 1.64, 1.61, 1.43, 1.32, 1.39, 1.53, 1.65, 1.56, 1.37, 1.34, 1.4, 1.59, 1.63, 1.5, 1.33, 1.34, 1.46, 1.63, 1.6, 1.5, 1.33, 1.36, 1.53, 1.64, 1.6, 1.42, 1.33, 1.4, 1.6, 1.64, 1.56, 1.36, 1.34, 1.42, 1.33, 1.4, 1.6, 1.63, 1.49, 1.36, 1.34, 1.47, 1.64, 1.6, 1.48, 1.33, 1.36, 1.54, 1.64, 1.6, 1.42, 1.33, 1.41, 1.61, 1.65, 1.55, 1.35, 1.34, 1.48, 1.64, 1.59, 1.41, 1.33, 1.41, 1.61, 1.63, 1.55, 1.35, 1.35, 1.48, 1.64, 1.62, 1.48, 1.33, 1.37, 1.48, 1.64, 1.59, 1.41, 1.33, 1.42, 1.56, 1.65, 1.54, 1.35, 1.34, 1.48, 1.61, 1.62, 1.47, 1.33, 1.37, 1.49, 1.65, 1.59, 1.4, 1.33, 1.37, 1.56, 1.64, 1.54, 1.4, 1.33, 1.42, 1.62, 1.63, 1.55, 1.34, 1.34, 1.49, 1.65, 1.63, 1.47, 1.32, 1.37, 1.57, 1.65, 1.54, 1.34, 1.32, 1.42, 1.63, 1.63, 1.54, 1.34, 1.34, 1.5, 1.66, 1.63, 1.47, 1.32, 1.37, 1.57, 1.32, 1.43, 1.63, 1.63, 1.46, 1.32, 1.37, 1.58, 1.66, 1.53, 1.38, 1.32, 1.43, 1.64, 1.66, 1.46, 1.32, 1.37, 1.58, 1.65, 1.59, 1.38, 1.32, 1.43, 1.64, 1.66, 1.53, 1.33, 1.34, 1.5, 1.66, 1.59, 1.45, 1.32, 1.37, 1.58, 1.65, 1.59, 1.37, 1.32, 1.43, 1.59, 1.66, 1.53, 1.33, 1.34, 1.51, 1.65, 1.63, 1.45, 1.31, 1.34, 1.51, 1.66, 1.59, 1.37, 1.31, 1.37, 1.59, 1.66, 1.52, 1.32, 1.34, 1.44, 1.65, 1.63, 1.44, 1.32, 1.37, 1.52, 1.67, 1.59, 1.36, 1.31, 1.38, 1.6, 1.66, 1.52, 1.36, 1.32, 1.44, 1.65, 1.63, 1.51, 1.32, 1.34, 1.53, 1.67, 1.63, 1.36, 1.31, 1.38, 1.6, 1.66, 1.51, 1.36, 1.32, 1.45, 1.65, 1.63, 1.66, 1.58, 1.42, 1.31, 1.38, 1.61, 1.66, 1.58, 1.35, 1.32, 1.45, 1.66, 1.63, 1.5, 1.32, 1.34, 1.62, 1.67, 1.51, 1.32, 1.34, 1.46, 1.67, 1.63, 1.42, 1.31, 1.34, 1.54, 1.68, 1.58, 1.35, 1.31, 1.39, 1.62, 1.66, 1.58, 1.34, 1.34, 1.46, 1.67, 1.63, 1.41, 1.31, 1.34, 1.55, 1.68, 1.57, 1.34, 1.31, 1.39, 1.63, 1.66, 1.49, 1.34, 1.32, 1.47, 1.67, 1.63, 1.49, 1.31, 1.34, 1.56, 1.68, 1.63, 1.4, 1.31, 1.4, 1.63, 1.66, 1.49, 1.31, 1.32, 1.48, 1.67, 1.62, 1.48, 1.31, 1.35, 1.56, 1.67, 1.62, 1.4, 1.31, 1.4, 1.64, 1.68, 1.56, 1.33, 1.32, 1.49, 1.64, 1.66, 1.47, 1.31, 1.35, 1.57, 1.67, 1.56, 1.39, 1.31]



        # Serial and graphing variables
        self.simulation_thread = threading.Thread(target=self.simulate_data, daemon=True)

        # Timer to update graph
        self.plot_timer = QtCore.QTimer()
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(2)  # 2 ms timer

        # Timer to save data
        self.save_timer = QtCore.QTimer()
        self.save_timer.timeout.connect(self.save_data)
        self.save_timer.start(5000)  # Save data every 5 seconds

        # Connect sliders to update function
        self.xRange_slider.slider.valueChanged.connect(self.update_x_range)
        self.lowpass_slider.slider.valueChanged.connect(self.update_filters)
        self.highpass_slider.slider.valueChanged.connect(self.update_filters)
        self.notch_slider.slider.valueChanged.connect(self.update_filters)


        self.update_filters()
        self.time=3.3
        self.last_time = time.perf_counter()
        self.current_time = time.perf_counter()
    def start(self):
        # Start thread to simulate data
        self.simulation_thread.start()

        # Main Loop
        app.exec_()

    def simulate_data(self):
        while True:
            self.current_time = time.perf_counter()
            # Simulate data read
            if self.graph_pos < self.buffer_size:
                value = self.lista_data[self.c]
                self.data[self.graph_pos] = value
                self.graph_pos += 1
                self.c += 1
            else:
                self.data[:-1] = self.data[1:]
                self.data[-1] = self.lista_data[self.c]
                self.c += 1
            # Sleep to simulate data rate (2 ms interval)
            if self.c >= 1000:
                self.c = 0
            QtCore.QThread.msleep(2)
            self.last_time = time.perf_counter()
            time_diff =  self.last_time-self.current_time


    def update_plot(self):
        filtered_data = self.apply_filters(
            self.data[:self.graph_pos] if self.graph_pos < self.buffer_size else self.data)

        try:
            self.graph.setData((np.arange(self.graph_pos))/(1/0.0033)+self.time,filtered_data)
        except:
            pass

        self.main_plot.setXRange(self.time+0.33, self.time+3.3*(self.buffer_size/1000))
        self.main_plot.getAxis('bottom').setLabel('Time', units='s')

        x_ticks = np.arange(0+self.time, 10+self.time, 1)
        self.time+=3.3
        self.main_plot.getAxis('bottom').setTicks([[(tick, f"{tick/1000:.2f}") for tick in x_ticks]])

        if self.graph_pos >= self.fft_sample_size:
            x_ticks = x_ticks[100:]
            self.calc_fft(filtered_data[-self.fft_sample_size:])
        if self.c % 100 == 0:
            top_indices = np.argsort(self.fft_graph_fft_mag)[-10:][::-1]
            top_frequencies = self.fft_freq[top_indices]
            for freq in top_frequencies:
                pass

    def update_x_range(self):
        new_buffer_size = int(self.xRange_slider.x)
        if new_buffer_size != self.buffer_size:
            self.buffer_size = new_buffer_size
            self.fft_sample_size = new_buffer_size
            self.data = np.zeros(self.buffer_size)
            self.graph_pos = 0
            self.fft_freq = np.fft.rfftfreq(self.fft_sample_size * self.fft_padding, self.elapsed_time)
            self.fft_graph_fft_mag = np.zeros(int((self.fft_sample_size * self.fft_padding) / 2) + 1)

    def update_filters(self):
        from scipy.signal import butter, iirnotch

        self.lowpass_cutoff = self.lowpass_slider.x
        self.highpass_cutoff = self.highpass_slider.x
        self.notch_freq = self.notch_slider.x

        if 0 < self.lowpass_cutoff < 1/(self.elapsed_time*2) and 0 < self.highpass_cutoff < 1/(self.elapsed_time*2):
            self.b_low, self.a_low = butter(5, self.lowpass_cutoff *self.elapsed_time*2, btype='low')
            self.b_high, self.a_high = butter(5, self.highpass_cutoff *self.elapsed_time*2, btype='high')
            self.b_notch, self.a_notch = iirnotch(self.notch_freq *self.elapsed_time*2, 30)

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
        data = data - np.mean(data)
        ham = np.hamming(self.fft_sample_size)
        y_ham = data * ham
        self.fft_graph_fft_mag = 4 / self.fft_sample_size * np.abs(
            np.fft.rfft(y_ham, self.fft_sample_size * self.fft_padding))
        self.fft_graph.setData(self.fft_freq, self.fft_graph_fft_mag)

    def save_data(self):
        data_to_save = self.data.tolist()
        with open('ecg_data.txt', 'a') as file:
            file.write(str(data_to_save) + '\n')

    def exit(self):
        sys.exit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    scope = Scope()
    scope.show()
    try:
        scope.start()
    except:
        pass
