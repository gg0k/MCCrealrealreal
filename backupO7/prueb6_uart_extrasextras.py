from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QSizePolicy, QSlider, QSpacerItem, QVBoxLayout, QWidget
from pyqtgraph.Qt import QtCore, QtWidgets
import pyqtgraph as pg
import numpy as np
import threading
import sys
from scipy.signal import butter, lfilter, iirnotch


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
        self.xRange_slider = Slider(1, 1000, 100)  # Lowpass slider, initial value should not be a fraction
        self.horizontalLayout.addWidget(self.xRange_slider)

        self.lowpass_slider = Slider(1, 299, 100)  # Lowpass slider, initial value should not be a fraction
        self.horizontalLayout.addWidget(self.lowpass_slider)
        self.highpass_slider = Slider(0.00001, 0.0001,
                                      0.00001)  # Highpass slider, initial value should not be a fraction
        self.horizontalLayout.addWidget(self.highpass_slider)
        self.notch_slider = Slider(45, 60, 50)  # Notch filter slider
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



        # Main plot setup
        self.main_plot.setYRange(self.y_min, self.y_max)
        self.main_plot.setLabel('left', 'ECG Value', '')
        self.main_plot.setLabel('bottom', 'Time', 's')

        # Create the plot
        self.graph = self.main_plot.plot()
        self.graph_pos = 0

        # Add FFT plot


        # Variables for storing data
        self.buffer_size = 481
        self.data = np.zeros(self.buffer_size)
        self.c = 0



        # 1000 data list


        self.lista_data = [1,1.64855, 1.714177, 1.782992, 1.782992, 1.819743, 1.87112, 1.880495, 1.846369, 1.805118, 1.722803, 1.655863, 1.590049, 1.542797, 1.542797, 1.501171, 1.477733, 1.494983, 1.536984, 1.601674, 1.675364, 1.752428, 1.819368, 1.907121, 1.916683, 1.916683, 1.888933, 1.850307, 1.761054, 1.691864, 1.62305, 1.570548, 1.521046, 1.499858, 1.499858, 1.506421, 1.54486, 1.613112, 1.689614, 1.762366, 1.831556, 1.865119, 1.912558, 1.923246, 1.923246, 1.899433, 1.852931, 1.766679, 1.698614, 1.620237, 1.568298, 1.535297, 1.497608, 1.503233, 1.503233, 1.539235, 1.606924, 1.677051, 1.748678, 1.810743, 1.863994, 1.905808, 1.921746, 1.904496, 1.904496, 1.858369, 1.770617, 1.705552, 1.633737, 1.577111, 1.531922, 1.499858, 1.509984, 1.536609, 1.536609, 1.608799, 1.675926, 1.750928, 1.825368, 1.852182, 1.922684, 1.919496, 1.906558, 1.906558, 1.865682, 1.782429, 1.723178, 1.653988, 1.603549, 1.551047, 1.504358, 1.498171, 1.537172, 1.537172, 1.608612, 1.676864, 1.759366, 1.835306, 1.863807, 1.897933, 1.887245, 1.832681, 1.727303, 1.727303, 1.585736, 1.457482, 1.335791, 1.265664, 1.248226, 1.244851, 1.244475, 1.244475, 1.245413, 1.245413, 1.249913, 1.270914, 1.439106, 1.669363, 1.788992, 1.786555, 1.763116, 1.748116, 1.767991, 1.767991, 1.790867, 1.79818, 1.909558, 2.000874, 2.0395, 2.081688, 2.113189, 2.172441, 2.172441, 2.227755, 2.269569, 2.308946, 2.347384, 2.37626, 2.36726, 2.329571, 2.258131, 2.139065, 2.139065, 2.03575, 1.933934, 1.847869, 1.768554, 1.697302, 1.653988, 1.643863, 1.673301, 1.740053, 1.740053, 1.794992, 1.863244, 1.888558, 1.919871, 1.945559, 1.924934, 1.87937, 1.798742, 1.72374, 1.72374, 1.64555, 1.574861, 1.527984, 1.48467, 1.470982, 1.499483, 1.55386, 1.6313, 1.694302, 1.694302, 1.770617, 1.80193, 1.856869, 1.879932, 1.87787, 1.832681, 1.744178, 1.671801, 1.671801, 1.590799, 1.531547, 1.486733, 1.433856, 1.427856, 1.461232, 1.510546, 1.589861, 1.660551, 1.660551, 1.730678, 1.79293, 1.832493, 1.857807, 1.836619, 1.805118, 1.739491, 1.667488, 1.585361, 1.585361, 1.519171, 1.47342, 1.425231, 1.407605, 1.438544, 1.497421, 1.580298, 1.637675, 1.72599, 1.72599, 1.769491, 1.806055, 1.839806, 1.839994, 1.805492, 1.727115, 1.649675, 1.570173, 1.505483, 1.505483, 1.466857, 1.413981, 1.401605, 1.433856, 1.48467, 1.557235, 1.630925, 1.712677, 1.759929, 1.759929, 1.802118, 1.832493, 1.840931, 1.794617, 1.71849, 1.643863, 1.580298, 1.506984, 1.506984, 1.462732, 1.414543, 1.407418, 1.431606, 1.47867, 1.56361, 1.621362, 1.698989, 1.741928, 1.741928, 1.790867, 1.821993, 1.821993, 1.790117, 1.709302, 1.640488, 1.555735, 1.496858, 1.464607, 1.464607, 1.396355, 1.391855, 1.414168, 1.459357, 1.542985, 1.610299, 1.695802, 1.749991, 1.789929, 1.789929, 1.816555, 1.818056, 1.785617, 1.721303, 1.63955, 1.558548, 1.484108, 1.443607, 1.394105, 1.394105, 1.371979, 1.384542, 1.435919, 1.519171, 1.582923, 1.659801, 1.709865, 1.758429, 1.758429, 1.783554, 1.799867, 1.761241, 1.698239, 1.616487, 1.542047, 1.457294, 1.40948, 1.362792, 1.362792, 1.342353, 1.355291, 1.392043, 1.459545, 1.534359, 1.618549, 1.663926, 1.705364, 1.745678, 1.745678, 1.737053, 1.716802, 1.654363, 1.567735, 1.490296, 1.410043, 1.368417, 1.327916, 1.31554, 1.31554, 1.326603, 1.360916, 1.441356, 1.509421, 1.598674, 1.656988, 1.702927, 1.747741, 1.754116, 1.754116, 1.710052, 1.646488, 1.57261, 1.495358, 1.426544, 1.371604, 1.326228, 1.31179, 1.31179, 1.326603, 1.362417, 1.430106, 1.513921, 1.595674, 1.654738, 1.696177, 1.735928, 1.753928, 1.753928, 1.727865, 1.662988, 1.585173, 1.512046, 1.432919, 1.407418, 1.343104, 1.345353, 1.350979, 1.350979, 1.39223, 1.478858, 1.549172, 1.633362, 1.700677, 1.745491, 1.794617, 1.804555, 1.780179, 1.780179, 1.72149, 1.641237, 1.575423, 1.497608, 1.456544, 1.406106, 1.383042, 1.404793, 1.445669, 1.445669, 1.524234, 1.597549, 1.675551, 1.744928, 1.785992, 1.835118, 1.848619, 1.814493, 1.814493, 1.769679, 1.691489, 1.617987, 1.534359, 1.490858, 1.452607, 1.413606, 1.436669, 1.472107, 1.472107, 1.552922, 1.62155, 1.698989, 1.771179, 1.806243, 1.857619, 1.858932, 1.836619, 1.788805, 1.788805, 1.671051, 1.619487, 1.536234, 1.490858, 1.467045, 1.456544, 1.458795, 1.500796, 1.564548, 1.564548, 1.624175, 1.702552, 1.761991, 1.799867, 1.845806, 1.864182, 1.833618, 1.797055, 1.704427, 1.704427, 1.633362, 1.55986, 1.500983, 1.466857, 1.445294, 1.437981, 1.46967, 1.54711, 1.621174, 1.621174, 1.694489, 1.757866, 1.80493, 1.854057, 1.86737, 1.836619, 1.79443, 1.705927, 1.705927, 1.6388, 1.553297, 1.494608, 1.453544, 1.431419, 1.431981, 1.46292, 1.533047, 1.617987, 1.617987, 1.685114, 1.752428, 1.79668, 1.853682, 1.864182, 1.845619, 1.783367, 1.713802, 1.641425, 1.641425, 1.55611, 1.495546, 1.455982, 1.410418, 1.424106, 1.460482, 1.529484, 1.596986, 1.678176, 1.678176, 1.755991, 1.80193, 1.845994, 1.860619, 1.838869, 1.79143, 1.706865, 1.633737, 1.553297, 1.553297, 1.512609, 1.453544, 1.413043, 1.417168, 1.455419, 1.514109, 1.586673, 1.658488, 1.733115, 1.733115, 1.769116, 1.825931, 1.841494, 1.825556, 1.789555, 1.703115, 1.629237, 1.541484, 1.541484, 1.494796, 1.449419, 1.408731, 1.407605, 1.442669, 1.509984, 1.565298, 1.655301, 1.721678, 1.721678, 1.766304, 1.817868, 1.840931, 1.835118, 1.793117, 1.705364, 1.628112, 1.552735, 1.489545, 1.489545, 1.443232, 1.403668, 1.40273, 1.437044, 1.492358, 1.574673, 1.646675, 1.71174, 1.771742, 1.771742, 1.821243, 1.834369, 1.827993, 1.792367, 1.71474, 1.6328, 1.557047, 1.493108, 1.453732, 1.453732, 1.412856, 1.399918, 1.427106, 1.48092, 1.568673, 1.623237, 1.713802, 1.762741, 1.762741, 1.808493, 1.835494, 1.828556, 1.778492, 1.703677, 1.630925, 1.559673, 1.488233, 1.439294, 1.439294, 1.38623, 1.388292, 1.423731, 1.481483, 1.560798, 1.627925, 1.700677, 1.751678, 1.79218, 1.79218, 1.816555, 1.805868, 1.763491, 1.688676, 1.605236, 1.521234, 1.444732, 1.396918, 1.352104, 1.352104, 1.348166, 1.38098, 1.422981, 1.506608, 1.575423, 1.647988, 1.701427, 1.737428, 1.783179, 1.783179, 1.775117, 1.73124, 1.656801, 1.586111, 1.513171, 1.448482, 1.40498, 1.356604, 1.356604, 1.355479, 1.38623, 1.445669, 1.532484, 1.603362, 1.687551, 1.739678, 1.794617, 1.827993, 1.827993, 1.826868, 1.786367, 1.714365, 1.642925, 1.571673, 1.496108, 1.446794, 1.403668, 1.396918, 1.396918, 1.423356, 1.469482, 1.55536, 1.624175, 1.70799, 1.760679, 1.80493, 1.836056, 1.838681, 1.838681, 1.79968, 1.734803, 1.659426, 1.569798, 1.507546, 1.458607, 1.408168, 1.38473, 1.423356, 1.423356, 1.467795, 1.549547, 1.622112, 1.703115, 1.752241, 1.792555, 1.831743, 1.832868, 1.792367, 1.792367, 1.73049, 1.659988, 1.584048, 1.509984, 1.460857, 1.418856, 1.404043, 1.421293, 1.421293, 1.470982, 1.55461, 1.617799, 1.698802, 1.748303, 1.79368, 1.837931, 1.841681, 1.803243, 1.803243, 1.741741, 1.658863, 1.580673, 1.514296, 1.459732, 1.408355, 1.38698, 1.410793, 1.458607, 1.458607, 1.545235, 1.616112, 1.705364, 1.768742, 1.822181, 1.861369, 1.857244, 1.812243, 1.745491, 1.745491, 1.670114, 1.600924, 1.537359, 1.495733, 1.453169, 1.419981, 1.407605, 1.412668, 1.438544, 1.438544, 1.456357, 1.473607, 1.481295, 1.466482, 1.440231, 1.384542, 1.303352, 1.263414, 1.263414, 1.247101, 1.243538, 1.243163, 1.243538, 1.249351, 1.260038, 1.261913, 1.261163, 1.316103, 1.316103, 1.47117, 1.660738, 1.839806, 2.060688, 2.248381, 2.333696, 2.352634, 2.29282, 2.201505, 2.201505, 2.124253, 2.032375, 1.947059, 1.890433, 1.860807, 1.853682, 1.87337, 1.905996, 1.944622, 1.944622, 2.000124, 2.042125, 2.050375, 2.068751, 2.03725, 1.878995, 1.760679, 1.665238, 1.57186, 1.501358, 1.501358, 1.436481, 1.40573, 1.411731, 1.437419, 1.512984, 1.579548, 1.65305, 1.715115, 1.750366, 1.750366, 1.797055, 1.801555, 1.770054, 1.714552, 1.624925, 1.547485, 1.461045, 1.406293, 1.406293, 1.353791, 1.327165, 1.334666, 1.371229, 1.443794, 1.522359, 1.601111, 1.664488, 1.699552, 1.699552, 1.742303, 1.749991, 1.721115, 1.661113, 1.566235, 1.517859, 1.447732, 1.38548, 1.333916, 1.333916, 1.300915, 1.306352, 1.343104, 1.416606, 1.48692, 1.558173, 1.621362, 1.665238, 1.72449, 1.72449, 1.733115, 1.709302, 1.659988, 1.560423, 1.496296, 1.419418, 1.362417, 1.317603, 1.290414, 1.290414, 1.296227, 1.334103, 1.400855, 1.467607, 1.546735, 1.623425, 1.659988, 1.700114, 1.700114, 1.70724, 1.693739, 1.6508, 1.555547, 1.488233, 1.411543, 1.360354, 1.32379, 1.290414, 1.290414, 1.290039, 1.32529, 1.393917, 1.46217, 1.541672, 1.609362, 1.643113, 1.676301, 1.692802, 1.692802, 1.663551, 1.621737, 1.523672, 1.436856, 1.346104, 1.29754, 1.273726, 1.267914, 1.284039, 1.284039, 1.30279, 1.362042, 1.431419, 1.515796, 1.597549, 1.659613, 1.687551, 1.721303, 1.698614, 1.698614, 1.628487, 1.53961, 1.464607, 1.382105, 1.327541, 1.292477, 1.263226, 1.263414, 1.263414, 1.260976, 1.348354, 1.431419, 1.495546, 1.548985, 1.581986, 1.658488, 1.680239, 1.671426, 1.671426, 1.607674, 1.541484, 1.429544, 1.341041, 1.289664, 1.270539, 1.257976, 1.274101, 1.29454, 1.29454, 1.304477, 1.368979, 1.436481, 1.489358, 1.54711, 1.627925, 1.630925, 1.601111, 1.570548, 1.570548, 1.46067, 1.422606, 1.31329, 1.274101, 1.252726, 1.253663, 1.251788, 1.256288, 1.265851, 1.265851, 1.306915, 1.386417, 1.479983, 1.512046, 1.550672, 1.562673, 1.527609, 1.519921, 1.429544, 1.429544, 1.344979, 1.282727, 1.257038, 1.250288, 1.246538, 1.246726, 1.2456, 1.250288, 1.250288, 1.264351, 1.346666, 1.416793, 1.444357, 1.479795, 1.483545, 1.503233, 1.512421, 1.384167, 1.384167, 1.405355, 1.380792, 1.290977, 1.263414, 1.253476, 1.249913, 1.246726, 1.248601, 1.261163, 1.261163, 1.303352, 1.39748, 1.443419, 1.524421, 1.55386, 1.575236, 1.559673, 1.510921, 1.396918, 1.396918, 1.422606, 1.368604, 1.334291, 1.302602, 1.261913, 1.263414, 1.260601, 1.260788, 1.267539, 1.267539, 1.291727, 1.335416, 1.403668, 1.468357, 1.443982, 1.448482, 1.389417, 1.349104, 1.349104, 1.364479, 1.346291, 1.333541, 1.364667, 1.333541, 1.407605, 1.396918, 1.532859, 1.56886, 1.56886, 1.619674, 1.731615, 1.742116, 1.71249, 1.639738, 1.672551, 1.679676, 1.54636, 1.473982, 1.473982, 1.427106, 1.356979]

        print(len(self.lista_data))
        # Serial and graphing variables
        self.simulation_thread = threading.Thread(target=self.simulate_data, daemon=True)

        # Timer to update graph
        self.plot_timer = QtCore.QTimer()
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(2)  # 2 ms timer

        self.lowpass_slider.slider.valueChanged.connect(self.update_filters)
        self.highpass_slider.slider.valueChanged.connect(self.update_filters)
        self.notch_slider.slider.valueChanged.connect(self.update_filters)

        self.b_low, self.a_low = [0.06951437, 0.13902873, 0.06951437], [1, -1.1283145, 0.40637196]
        self.b_high, self.a_high = [0.06951437, 0.13902873, 0.06951437], [1, -1.1283145, 0.40637196]
        self.b_notch, self.a_notch = [0.06951437, 0.13902873, 0.06951437], [1, -1.1283145, 0.40637196]
        self.update_filters()

    def start(self):
        # Start thread to simulate data
        self.simulation_thread.start()

        # Main Loop
        app.exec_()

    def simulate_data(self):
        while True:
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

    def update_plot(self):
        data =(self.data[:self.graph_pos] if self.graph_pos < self.buffer_size else self.data)
        self.graph.setData(data)
        self.main_plot.setXRange(100, self.buffer_size)




    def update_filters(self):
        from scipy.signal import butter, iirnotch

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
        # Set FFT data
        self.fft_graph.setData(self.fft_freq, self.fft_graph_fft_mag)

    def exit(self):
        sys.exit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    scope = Scope()
    scope.show()
    scope.start()
