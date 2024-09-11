import tkinter as tk
from tkinter import Canvas
import serial.tools.list_ports
import can
import struct
from scrollable_frame import *
import threading
import time

# # config = {
#     "AMK_Status": {
#         8: ("AMK_bSystemReady", 0),   
#         9: ("AMK_bError",0),              
#         10: ("AMK_bWarn",0),
#         11: ("AMK_bQuitDcOn",0),
#         12: ("AMK_bDcOn",0),
#         13: ("AMK_bQuitInverterOn",0),
#         14: ("AMK_bInverterOn",0),
#         15: ("AMK_bDerating",0)
#     },
#     "AMK_Control": {
#         8: ("AMK_bInverterOn",0),
#         9: ("AMK_bDcOn",0),
#         10: ("AMK_bEnable",0),
#         11: ("AMK_bErrorReset",0)
#     }
# }
config = {
    "AMK_Status": {
        8: "AMK_bSystemReady",
        9: "AMK_bError",
        10: "AMK_bWarn",
        11: "AMK_bQuitDcOn",
        12: "AMK_bDcOn",
        13: "AMK_bQuitInverterOn",
        14: "AMK_bInverterOn",
        15: "AMK_bDerating"
    },
    "AMK_Control": {
        8: "AMK_bInverterOn",
        9: "AMK_bDcOn",
        10: "AMK_bEnable",
        11: "AMK_bErrorReset"
    }
}

class MotorControlApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AMK Motor Control")
        self.geometry("1100x800")
        
        # # Create a main control section above the motor-specific sections
        # self.main_controls = MainControlFrame(self)
        # self.main_controls.grid(row=0, column=0, columnspan=8, padx=10, pady=10, sticky="nsew")
        
        # Example CAN bus setup (modify this to suit your actual configuration)
        self.bus = None

        # Define motor names
        motor_names = ["Rear Left", "Rear Right", "Front Left", "Front Right"]
        
        # Create 4 motor sections, each with a different set of CAN addresses and a name
        self.motor_frames = []  # List to store the motor frames

        # Create 4 motor sections, each with a different set of CAN addresses and a name
        self.motor_frames = []
        for i, motor_name in enumerate(motor_names):
            status_address = f"0x{600+i}"   # Example status addresses
            control_address = f"0x{200+i}"  # Example control addresses
            target_address = f"0x{300+i}"   # Example target addresses
            scrollable_frame = ScrollableFrame(self)
            frame = MotorFrame(scrollable_frame.scrollable_frame, motor_name=motor_name, motor_number=i+1, 
                            status_address=status_address, control_address=control_address, 
                            target_address=target_address, can_bus=self.bus)
            frame.pack(fill="both", expand=True, padx=10, pady=10)
            scrollable_frame.grid(row=1, column=i, padx=10, pady=10, sticky="nsew")

        # Create the main control section, passing the motor frames list
        self.main_controls = MainControlFrame(self, self.motor_frames)
        self.main_controls.grid(row=0, column=0, columnspan=8, padx=10, pady=10, sticky="nsew")
        
        # Configure grid layout to split into 4 vertical sections
        self.grid_rowconfigure(1, weight=1)
        for i in range(4):
            self.grid_columnconfigure(i, weight=1)


    
    def toggle_txrx(self):
        if self.enable:
            self.enable = False
            if self.bus is not None:
                self.bus.shutdown()
                self.bus = None
            for motor_frame in self.motor_frames:
                motor_frame.motor_comm.stop_sending_messages()
            print("TXRX disabled")
        else:
            self.bus = can.interface.Bus(bustype='slcan', channel=self.com_port, bitrate=self.bitrate)
            self.enable = True
            for motor_frame in self.motor_frames:
                motor_frame.motor_comm.start_sending_messages()
            print("TXRX enabled")


class MainControlFrame(tk.Frame):
    def __init__(self, parent, motor_frames):
        super().__init__(parent, bd=2, relief=tk.RIDGE)

        self.motor_frames = motor_frames  # Reference to all motor frames

        # Title row
        self.title_label = tk.Label(self, text="Main Controls", font=("Calibri Bold", 16))
        self.title_label.grid(row=0, column=1, columnspan=3, pady=(1, 0), padx=300)


        # COM port label and dropdown on the second row
        self.comport_label = tk.Label(self, text="Select COM Port:")
        self.comport_label.grid(row=1, column=0, padx=(15, 0), sticky="e", pady=(0, 0))
        self.comport_var = tk.StringVar(self)
        self.comport_var.set("No COM Ports Available")  # Default selection
        self.comport_dropdown = tk.OptionMenu(self, self.comport_var, "No COM Ports Available")
        self.comport_dropdown.grid(row=1, column=1, padx=(0, 15), sticky="w", pady=(0, 0))


        # Enable communication button
        self.enable_button = tk.Button(self, text="Enable Communication", width=20)
        self.enable_button.grid(row=1, column=2, padx=10, sticky="w", pady=(0, 0))


        # Open Message Log button
        self.log_button = tk.Button(self, text="Open Message Log", width=20)
        self.log_button.grid(row=1, column=3, padx=10, sticky="w", pady=(0, 0))

        # Create checkboxes for AMK Control (all motors)
        self.checkbox_vars = {}  # Store references to checkbox IntVars
        self.create_amk_control_checkboxes()


        # Call function to update COM ports
        self.update_com_ports()

    def create_amk_control_checkboxes(self):
        self.checkbox_frame = tk.LabelFrame(self, text="AMK Control", padx=10, pady=10)
        self.checkbox_frame.grid(row=0, column=4, rowspan=2, padx=10, pady=(0, 5), sticky="n")

        # Create a checkbox for each AMK Control flag
        for bit, control_name in config["AMK_Control"].items():
            var = tk.IntVar()  # Use IntVar to track the checkbox state
            checkbox = tk.Checkbutton(self.checkbox_frame, text=control_name, variable=var, command=lambda b=bit, v=var: self.update_all_motors_control(b, v))
            checkbox.pack(anchor='w', pady=2)
            self.checkbox_vars[bit] = var

    # Function to get available COM ports and update the dropdown
    def update_com_ports(self):
        com_ports = self.get_com_ports()

        # Update the dropdown with available COM ports
        menu = self.comport_dropdown["menu"]
        menu.delete(0, "end")  # Clear existing menu options
        if com_ports:
            for port in com_ports:
                menu.add_command(label=port, command=lambda p=port: self.comport_var.set(p))
            self.comport_var.set(com_ports[0])  # Default to the first available COM port
        else:
            self.comport_var.set("No COM Ports Available")

    # Helper function to retrieve available COM ports
    def get_com_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    
    def get_chosen_com_port(self) -> str:
        selected_port = self.comport_var.get()
        if selected_port == "No COM Ports Available":
            return None  # Or return an appropriate value indicating no port is selected
        return selected_port
    
    def get_enable(self) -> bool:
        return self.enable_button.getboolean()

    def update_all_motors_control(self, bit, var):
        # Propagate checkbox state to all motors' AMK Control flags
        for motor_frame in self.motor_frames:
            motor_frame.motor_comm.amk_control[bit] = var.get()  # Update AMK control value


class MotorFrame(tk.Frame):
    def __init__(self, parent, motor_name, motor_number, status_address, control_address, target_address, can_bus):
        super().__init__(parent, bd=2, relief=tk.RIDGE)
        self.motor_name = motor_name
        self.motor_number = motor_number
        
        # Initialize MotorCommunication for this motor
        self.motor_comm = MotorCommunication(status_address, control_address, target_address, [0, 0, 0], can_bus)

        # Label for the motor with the motor name
        self.label = tk.Label(self, text=f"Motor: {motor_name}", font=("Calibri Bold", 12))  # Reduced font size
        self.label.pack(pady=10)  # Reduced padding

        # Create frames (boxes) for AMK Status and AMK Control without LEDs for the titles
        self.amk_status_frame = tk.LabelFrame(self, text="AMK Status", font=("Calibri Bold", 12), padx=10, pady=10)
        self.amk_status_frame.pack(fill="x", pady=5)  # Fill horizontally and reduce padding

        self.amk_control_frame = tk.LabelFrame(self, text="AMK Control", font=("Calibri Bold", 12), padx=10, pady=10)
        self.amk_control_frame.pack(fill="x", pady=5)  # Fill horizontally and reduce padding

        # Dynamically create LED-like circles inside the AMK Status and Control frames using grid layout
        self.led_widgets = {}
        self.create_leds(config["AMK_Status"], self.amk_status_frame)
        self.create_leds(config["AMK_Control"], self.amk_control_frame)

        # Sliders and numerical inputs
        self.sliders_frame = tk.Frame(self)
        self.sliders_frame.pack(pady=10)

        # Create 3 sliders and associated numerical inputs for control values
        self.slider_vars = []
        for i in range(3):
            # Slider label
            label = tk.Label(self.sliders_frame, text=f"Parameter {i+1}")
            label.grid(row=i, column=0, padx=5)
            
            # Slider (0 to 100 as an example range)
            slider = tk.Scale(self.sliders_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=lambda value, i=i: self.update_motor_control(i, value))
            slider.grid(row=i, column=1, padx=5)
            
            # Entry for numerical input
            entry_var = tk.StringVar()
            entry = tk.Entry(self.sliders_frame, textvariable=entry_var, width=5)
            entry.grid(row=i, column=2, padx=5)
            
            # Connect entry to slider updates
            entry_var.trace_add("write", lambda *args, slider=slider, entry_var=entry_var: self.update_slider(slider, entry_var))
            
            self.slider_vars.append(entry_var)

        self.sliders_frame.pack(fill="x", pady=5)

        # Address selection (Dropdown)
        self.dropdown_frame = tk.Frame(self)
        self.dropdown_frame.pack(pady=10)

        # Dropdown options
        filter_options = ["Status Address Filter", "Control Address Filter", "Target Address"]
        self.selected_filter = tk.StringVar(self)
        self.selected_filter.set(filter_options[0])  # Default selection

        # Create dropdown (OptionMenu)
        self.filter_dropdown = tk.OptionMenu(self.dropdown_frame, self.selected_filter, *filter_options)
        self.filter_dropdown.grid(row=0, column=0, padx=5)

        # Entry for inputting the number
        self.filter_value_var = tk.StringVar()
        self.filter_value_entry = tk.Entry(self.dropdown_frame, textvariable=self.filter_value_var, width=10)
        self.filter_value_entry.grid(row=0, column=1, padx=5)

    def create_leds(self, config_section, parent_frame):
        # Create LEDs for each item in the config section within the parent frame (either AMK Status or Control)
        for i, (bit, label_name) in enumerate(config_section.items()):
            led_label = tk.Label(parent_frame, text=label_name, font=("Calibri", 10))  # Reduced font size
            led_label.grid(row=i, column=0, padx=5, pady=5, sticky="w")  # Place label in grid
            
            led_canvas = Canvas(parent_frame, width=10, height=10)  # Smaller canvas for LEDs
            led_canvas.grid(row=i, column=1, padx=5, pady=5)  # Place canvas in grid
            led_circle = led_canvas.create_oval(2, 2, 10, 10, fill="red")  # Smaller LED circle

            # Store the LED canvas and circle for future updates
            self.led_widgets[label_name] = (led_canvas, led_circle)

    def update_slider(self, slider, entry_var):
        try:
            value = int(entry_var.get())
            slider.set(value)
        except ValueError:
            pass  # Handle invalid input (non-numeric)

    def update_motor_control(self, parameter_index, value):
        # Update the motor control parameter and send a CAN message
        self.motor_comm.amk_set[parameter_index] = int(value)
        self.motor_comm.send_message()


class MotorCommunication:
    def __init__(self, status_address, control_address, target_address, amk_set: list, bus: can.BusABC):
        self.status_address = int(status_address, 16)
        self.control_address = int(control_address, 16)
        self.target_address = int(target_address, 16)
        self.amk_status = {key : 0 for key in config["AMK_Status"].keys()}
        self.amk_control = {key : 0 for key in config["AMK_Control"].keys()}
        self.amk_target = {key :0 for key in config["AMK_Control"].keys()}
        self.amk_set = amk_set
        self.bus = bus
        self.sending_thread = None
        self.is_sending = False
    

    def recive_message(self, message: can.Message):
        bit_values = {
            8: (message.data[1] >> 0) & 1 if len(message.data) > 1 else 0,
            9: (message.data[1] >> 1) & 1 if len(message.data) > 1 else 0,
            10: (message.data[1] >> 2) & 1 if len(message.data) > 1 else 0,
            11: (message.data[1] >> 3) & 1 if len(message.data) > 1 else 0,
            12: (message.data[1] >> 4) & 1 if len(message.data) > 1 else 0,
            13: (message.data[1] >> 5) & 1 if len(message.data) > 1 else 0,
            14: (message.data[1] >> 6) & 1 if len(message.data) > 1 else 0,
            15: (message.data[1] >> 7) & 1 if len(message.data) > 1 else 0
        }
        if message.arbitration_id == self.status_address:
            for bit in self.amk_status.keys():
                self.amk_status[bit] = bit_values[bit]
        elif message.arbitration_id == self.control_address:
            for bit in self.amk_control.keys():
                self.amk_control[bit] = bit_values[bit]
        else:
            print("Not recieving messages")
    
    def send_message(self):
        try:
            data = bytearray(8)
            
            data[1] = sum((self.amk_target[bit]<< bit-8) for bit in self.amk_target.keys())
            for i, value in enumerate(self.amk_set):    
                struct.pack_into('<h', data, 2*i, value)
            
            message = can.Message(arbitration_id=self.target_address, data=data, is_extended_id=False)
            
            self.bus.send(message)

        except ValueError as e:
            print(f"Invalid input: {e}")

    def start_sending_messages(self):
        if not self.is_sending:
            self.is_sending = True
            self.sending_thread = threading.Thread(target=self._send_continuously)
            self.sending_thread.start()
    
    def stop_sending_messages(self):
        self.is_sending = False
        if self.sending_thread:
            self.sending_thread.join()
    
    def _send_continuously(self):
        while self.is_sending:
            self.send_message()
            time.sleep(1)  # Adjust the delay as needed (1 second between messages)

        
if __name__ == "__main__":
    app = MotorControlApp()
    app.mainloop()
