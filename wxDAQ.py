# wxDAQ.py - NI cDAQ Console using wxPython
#
# Initially, I created wxDAQ.py just to become familiar with NI cDAQ. I later improved it
# to handle situations where users make mistakes or encounter hardware problems.
# The productivity of Python is impressive, even though it might not be the best choice
# for core programming tasks.
#
# Application Architecture
# - GUI Part: The GUI layer is developed using the wxPython library, providing a user interface.
# - Data Acquisition Part: The nidaqmx library is utilized to communicate with and control the NI DAQ devices.
# - Data Visualization Part: The matplotlib library is integrated into the GUI for real-time visualization of acquired data.
# - Control Logic Part: This layer manages user interactions, data acquisition threads, and data visualization updates.
#
# Thread Management
# - Analog Data Collection: A separate thread collects analog data from specified channels using the nidaqmx library.
# - Digital Data Collection: Another thread collects digital data from the specified channel using the nidaqmx library.

import time  # Standard libraries
import threading  # Standard libraries
import wx  # GUI libraries
import nidaqmx.system  # Data acquisition library

# Data visualization libraries
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import (
    FigureCanvasWxAgg as FigureCanvas,
    NavigationToolbar2WxAgg as NavigationToolbar,
)
import matplotlib.animation as animation


class DAQConsoleFrame(wx.Frame):
    def __init__(self, parent, title):
        super(DAQConsoleFrame, self).__init__(parent, title=title, size=(850, 650))

        # Initialize data storage for analog and digital samples
        self.analog_sample_timestamps = []
        self.analog_samples = [[] for _ in range(4)]
        self.digital_sample_timestamps = []
        self.digital_samples = []

        self.setup_ui()
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def setup_ui(self):
        panel = wx.Panel(self)

        self.statusbar = self.CreateStatusBar()

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        if True:
            # Create a figure and canvas for data visualization
            self.figure = Figure()
            self.axes1 = self.figure.add_subplot(2, 1, 1)
            self.axes2 = self.figure.add_subplot(2, 1, 2)
            self.canvas = FigureCanvas(panel, -1, self.figure)
            self.toolbar = NavigationToolbar(self.canvas)

        if True:
            # Create a vertical box sizer for buttons and controls
            self.controls_vbox = wx.BoxSizer(wx.VERTICAL)

            if True:
                # Create a list control for displaying cDAQ module details
                self.list_ctrl = wx.ListCtrl(
                    panel, style=wx.LC_REPORT | wx.LC_EDIT_LABELS
                )
                self.list_ctrl.InsertColumn(0, "Device Name")
                self.list_ctrl.InsertColumn(1, "Product")
                self.list_ctrl.InsertColumn(2, "Serial #")
                self.list_cdaq_modules_with_details()

                self.copy_button = wx.Button(panel, label="Copy Device Name")
                self.copy_button.Bind(wx.EVT_BUTTON, self.on_copy_button_click)
                self.update_button = wx.Button(panel, label="Update")
                self.update_button.Bind(wx.EVT_BUTTON, self.on_update_button_click)
                device_info_hbox = wx.BoxSizer(wx.HORIZONTAL)
                device_info_hbox.Add(self.copy_button, 0, wx.ALL, 2)
                device_info_hbox.Add(self.update_button, 0, wx.ALL, 2)

                self.controls_vbox.Add(self.list_ctrl, 0, wx.EXPAND | wx.ALL, 2)
                self.controls_vbox.Add(device_info_hbox, 0, wx.ALL, 2)

            self.controls_vbox.Add(
                wx.StaticLine(panel, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.ALL, 8
            )
            if True:
                # Text input fields for default analog channel names
                self.axes1_chan1_text = wx.TextCtrl(panel, value="cDAQ1Mod1/ai0")
                self.axes1_chan2_text = wx.TextCtrl(panel, value="cDAQ1Mod1/ai1")
                self.axes1_chan3_text = wx.TextCtrl(panel, value="cDAQ1Mod5/ai0")
                self.axes1_chan4_text = wx.TextCtrl(panel, value="cDAQ1Mod5/ai1")
                self.controls_vbox.Add(
                    self.axes1_chan1_text, flag=wx.EXPAND | wx.ALL | wx.BOTTOM, border=2
                )
                self.controls_vbox.Add(
                    self.axes1_chan2_text, flag=wx.EXPAND | wx.ALL | wx.BOTTOM, border=2
                )
                self.controls_vbox.Add(
                    self.axes1_chan3_text, flag=wx.EXPAND | wx.ALL | wx.BOTTOM, border=2
                )
                self.controls_vbox.Add(
                    self.axes1_chan4_text, flag=wx.EXPAND | wx.ALL | wx.BOTTOM, border=2
                )

            self.controls_vbox.Add(
                wx.StaticLine(panel, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.ALL, 8
            )
            if True:
                self.axes2_chan1_text = wx.TextCtrl(
                    panel, value="cDAQ1Mod6/port0/line0:7"
                )
                self.controls_vbox.Add(
                    self.axes2_chan1_text, flag=wx.EXPAND | wx.ALL | wx.BOTTOM, border=2
                )

            self.controls_vbox.Add(
                wx.StaticLine(panel, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.ALL, 8
            )
            if True:
                self.controls_vbox.Add(
                    wx.StaticText(panel, label="AI -10 to +10 V"),
                    0,
                    wx.CENTER | wx.ALL,
                    0,
                )
                self.gauge = wx.Gauge(
                    panel, range=20, size=(200, 25)
                )  # -10..10 --> 0..20
                self.controls_vbox.Add(self.gauge, 0, wx.CENTER | wx.ALL, 2)

            self.controls_vbox.Add(
                wx.StaticLine(panel, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.ALL, 8
            )
            if True:
                run_control_hbox = wx.BoxSizer(wx.HORIZONTAL)
                self.sample_depth_text = wx.TextCtrl(panel, value="100", size=(60, 20))
                self.run_stop_toggle_button = wx.ToggleButton(panel, label="Run / Stop")
                self.run_stop_toggle_button.Bind(
                    wx.EVT_TOGGLEBUTTON, self.on_run_stop_toggle
                )
                run_control_hbox.Add(
                    wx.StaticText(panel, label="Sample Depth"), 0, wx.CENTER | wx.ALL, 2
                )
                run_control_hbox.Add(
                    self.sample_depth_text,
                    flag=wx.EXPAND | wx.ALL | wx.BOTTOM,
                    border=2,
                )
                run_control_hbox.Add(self.run_stop_toggle_button, 0, wx.ALL, 2)
                self.controls_vbox.Add(run_control_hbox, 0, wx.ALL, 2)

            self.controls_vbox.Add(
                wx.StaticLine(panel, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.ALL, 8
            )
            if True:
                self.digital_output_text = wx.TextCtrl(
                    panel, value="cDAQ1Mod7/port0/line0:3"
                )
                self.controls_vbox.Add(
                    self.digital_output_text,
                    flag=wx.EXPAND | wx.ALL | wx.BOTTOM,
                    border=2,
                )

                radio_button_hbox = wx.BoxSizer(wx.HORIZONTAL)
                self.radio_btn = []
                for index in range(4):
                    self.radio_btn.append(
                        [
                            wx.RadioButton(panel, label="", style=wx.RB_GROUP),
                            wx.RadioButton(panel, label="    "),
                        ]
                    )
                    self.radio_btn[index][0].Bind(
                        wx.EVT_RADIOBUTTON, self.on_radio_select
                    )
                    self.radio_btn[index][1].Bind(
                        wx.EVT_RADIOBUTTON, self.on_radio_select
                    )
                    radio_button_hbox.Add(
                        self.radio_btn[index][0], 0, wx.CENTER | wx.ALL, 0
                    )
                    radio_button_hbox.Add(
                        self.radio_btn[index][1], 0, wx.CENTER | wx.ALL, 2
                    )
                self.controls_vbox.Add(radio_button_hbox, 0, wx.ALL, 4)

        hbox.Add(self.canvas, proportion=1, flag=wx.EXPAND | wx.ALL, border=0)
        hbox.Add(self.controls_vbox, border=0)

        vbox.Add(self.toolbar, 0, wx.EXPAND)
        vbox.Add(hbox, 1, flag=wx.EXPAND | wx.ALL)

        panel.SetSizerAndFit(vbox)

        self.Centre()
        self.Show()

        # Initialize animation for real-time data update
        self.ani = animation.FuncAnimation(
            self.figure, self.ani_update_plot, interval=10, cache_frame_data=False
        )

    def ani_update_plot(self, frame):
        self.update_plot()

    def update_plot(self):
        self.axes1.clear()
        self.axes2.clear()

        for index in range(4):
            self.axes1.plot(self.analog_sample_timestamps, self.analog_samples[index])

        # self.axes1.set_ylabel("Current (A)")
        self.axes1.set_xlabel("Time (msec)")
        # self.axes1.set_title("NI cDAQ Graphs")
        self.axes1.grid(True, axis="y")  # self.axes.grid(True)

        self.axes2.set_ylim(-0.5, 4)
        bit_value = [[] for _ in range(4)]
        for index in range(4):
            for byte_value in self.digital_samples:
                offseted_value = ((byte_value >> index) & 1) * 0.5 + index
                bit_value[index].append(offseted_value)

            self.axes2.plot(self.digital_sample_timestamps, bit_value[index])

        self.axes2.grid(True, axis="y")  # self.axes.grid(True)

        self.canvas.draw()

    def list_cdaq_modules_with_details(self):
        self.list_ctrl.DeleteAllItems()

        system = nidaqmx.system.System.local()

        for index, device_name in enumerate(system.devices.device_names, start=1):
            device = system.devices[index - 1]
            product_type = device.product_type
            serial_number = device.serial_num
            self.list_ctrl.InsertItem(index - 1, device_name)
            self.list_ctrl.SetItem(index - 1, 1, product_type)
            self.list_ctrl.SetItem(index - 1, 2, str(serial_number)) # Uncomment when needed

    def on_copy_button_click(self, event):
        selected_items = []
        selected_indices = []

        index = self.list_ctrl.GetFirstSelected()
        if index != -1:
            while index != -1:
                selected_indices.append(index)
                index = self.list_ctrl.GetNextSelected(index)

            for index in selected_indices:
                item_text = self.list_ctrl.GetItemText(index)
                selected_items.append(item_text)

            if selected_items:
                text_to_copy = "\n".join(selected_items)
                clipboard = wx.Clipboard.Get()
                if clipboard.Open():
                    clipboard.SetData(wx.TextDataObject(text_to_copy))
                    clipboard.Close()

    def on_update_button_click(self, event):
        self.list_cdaq_modules_with_details()

    def on_run_stop_toggle(self, event):
        if self.run_stop_toggle_button.GetValue():
            self.run_stop_toggle_button.SetBackgroundColour(
                wx.Colour(0, 255, 0)
            )  # Set to green when pressed

            self.statusbar.SetStatusText(".", 0)
            self.statusbar_default_background_color = (
                self.statusbar.GetBackgroundColour()
            )
            self.statusbar.Refresh()

            self.sample_depth = int(self.sample_depth_text.GetValue())

            self.start_timestamp = round((time.time()) * 1000)  # with msec precision

            thread_a = threading.Thread(target=self.analog_data_collection_loop)
            thread_a.daemon = True
            thread_a.start()

            thread_d = threading.Thread(target=self.digital_data_collection_loop)
            thread_d.daemon = True
            thread_d.start()

            self.ani.event_source.start()
        else:
            # Run this code to make sure it ends smoothly and gracefully.
            self.ani.event_source.stop()
            time.sleep(0.1)  # Wait for the thread's exit

            self.statusbar.SetBackgroundColour(self.statusbar_default_background_color)

            self.run_stop_toggle_button.SetBackgroundColour(
                wx.NullColour
            )  # Reset to default color

    def analog_data_collection_loop(self):
        # Create a new NIDAQ task to read data
        with nidaqmx.Task() as task:
            self.add_ai_voltage_chan_failed = False

            def add_ai_voltage_chan(the_task, text_ctrl):
                try:
                    the_task.ai_channels.add_ai_voltage_chan(text_ctrl.GetValue())
                except nidaqmx.DaqError as e:
                    # Set the flag if there is a failure at least once.
                    self.add_ai_voltage_chan_failed = True
                    self.statusbar.SetBackgroundColour(wx.Colour(255, 255, 150))
                    self.statusbar.SetStatusText(
                        text_ctrl.GetValue() + " not available.", 0
                    )

            add_ai_voltage_chan(task, self.axes1_chan1_text)
            add_ai_voltage_chan(task, self.axes1_chan2_text)
            add_ai_voltage_chan(task, self.axes1_chan3_text)
            add_ai_voltage_chan(task, self.axes1_chan4_text)

            if self.add_ai_voltage_chan_failed:
                return None

            task.start()

            self.analog_sample_timestamps.clear()
            [self.analog_samples[i].clear() for i in range(4)]

            while self.run_stop_toggle_button.GetValue():
                # Read before timestamp update to simplify synchronization with update_plot()
                data = task.read()
                for i in range(4):
                    self.analog_samples[i].append(data[i])
                    self.analog_samples[i] = self.analog_samples[i][
                        -self.sample_depth :
                    ]

                # with msec precision
                self.analog_sample_timestamps.append(
                    round(time.time() * 1000) - self.start_timestamp
                )
                self.analog_sample_timestamps = self.analog_sample_timestamps[
                    -self.sample_depth :
                ]

                # self.update_plot()

                # // No need to worry about being out of range
                self.gauge.SetValue(int(data[0]) + 10)

                time.sleep(0.01)

            task.stop()

    def digital_data_collection_loop(self):
        # Create a new NIDAQ task to read data
        with nidaqmx.Task() as task:
            try:
                task.di_channels.add_di_chan(self.axes2_chan1_text.GetValue())
            except nidaqmx.DaqError as e:
                self.statusbar.SetBackgroundColour(wx.Colour(255, 255, 150))
                self.statusbar.SetStatusText(
                    self.axes2_chan1_text.GetValue() + " not available.", 0
                )
                return None

            task.start()

            self.digital_sample_timestamps.clear()
            self.digital_samples.clear()

            while self.run_stop_toggle_button.GetValue():
                # Read before timestamp update to simplify synchronization with update_plot()
                data = task.read()
                self.digital_samples.append(data)
                self.digital_samples = self.digital_samples[-self.sample_depth :]

                # with msec precision
                self.digital_sample_timestamps.append(
                    round(time.time() * 1000) - self.start_timestamp
                )
                self.digital_sample_timestamps = self.digital_sample_timestamps[
                    -self.sample_depth :
                ]

                time.sleep(0.01)

            task.stop()

    def on_radio_select(self, event):
        bit_values = 0b00000000

        for index in range(4):
            # print(self.radio_btn[index][0].GetValue(),self.radio_btn[index][1].GetValue())
            if self.radio_btn[index][1].GetValue():
                bit_values |= 0b00000001 << index
            else:
                bit_values &= ~(0b00000001 << index)

        with nidaqmx.Task() as task:
            self.statusbar.SetStatusText(".", 0)
            try:
                task.do_channels.add_do_chan(self.digital_output_text.GetValue())
            except nidaqmx.DaqError as e:
                self.statusbar.SetStatusText(
                    self.digital_output_text.GetValue() + " not available.", 0
                )
                return None

            task.start()
            task.write(bit_values)
            time.sleep(0.01)
            task.stop()

    def on_close(self, event):
        # Run this code to make sure it ends smoothly and gracefully.
        self.ani.event_source.stop()
        time.sleep(0.1)

        self.Destroy()
        time.sleep(0.1)

        wx.Exit()  # We really need to force exit here


if __name__ == "__main__":
    app = wx.App(False)
    frame = DAQConsoleFrame(None, "wxDAQ - NI cDAQ Console using wxPython")
    app.MainLoop()
