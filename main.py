import tkinter as tk
from tkinter import Canvas
import serial.tools.list_ports
import can

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
        
        # Create a main control section above the motor-specific sections
        self.main_controls = MainControlFrame(self)
        self.main_controls.grid(row=0, column=0, columnspan=8, padx=10, pady=10, sticky="nsew")
        
        # Create 4 motor sections in a vertical split
        self.motor_frames = []
        for i in range(4):
            frame = MotorFrame(self, motor_number=i+1)
            frame.grid(row=1, column=i, padx=10, pady=10, sticky="nsew")
            self.motor_frames.append(frame)
        
        # Configure grid layout to split into 4 vertical sections
        self.grid_rowconfigure(1, weight=1)
        for i in range(4):
            self.grid_columnconfigure(i, weight=1)

class MainControlFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bd=2, relief=tk.RIDGE)

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


        # Checkboxes box that spans across two rows
        self.checkbox_frame = tk.LabelFrame(self, text="Options", padx=10, pady=10)
        self.checkbox_frame.grid(row=0, column=4, rowspan=2, padx=10, pady=(0, 5), sticky="n")


        # Vertical checkboxes inside the box
        self.checkbox_vars = []
        for i in range(4):
            var = tk.IntVar()
            checkbox = tk.Checkbutton(self.checkbox_frame, text=f"Checkbox {i+1}", variable=var)
            checkbox.pack(anchor='w', pady=2)
            self.checkbox_vars.append(var)

        # Call function to update COM ports
        self.update_com_ports()

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


class MotorFrame(tk.Frame):
    def __init__(self, parent, motor_number):
        super().__init__(parent, bd=2, relief=tk.RIDGE)
        self.motor_number = motor_number
        
        # Label for the motor
        self.label = tk.Label(self, text=f"Motor {motor_number}", font=("Calibri Bold", 16))
        self.label.pack(pady=20)

        # Frame to hold AMK status and control indicators
        self.status_frame = tk.Frame(self)
        self.status_frame.pack(pady=10)

        # AMK Status LED-like circle
        self.amk_status_label = tk.Label(self.status_frame, text="AMK Status")
        self.amk_status_label.grid(row=0, column=0, padx=5)
        self.amk_status_canvas = Canvas(self.status_frame, width=20, height=20)
        self.amk_status_canvas.grid(row=0, column=1, padx=5)
        self.amk_status_led = self.amk_status_canvas.create_oval(5, 5, 20, 20, fill="red")  # Default: red (off)

        # AMK Control LED-like circle
        self.amk_control_label = tk.Label(self.status_frame, text="AMK Control")
        self.amk_control_label.grid(row=1, column=0, padx=5)
        self.amk_control_canvas = Canvas(self.status_frame, width=20, height=20)
        self.amk_control_canvas.grid(row=1, column=1, padx=5)
        self.amk_control_led = self.amk_control_canvas.create_oval(5, 5, 20, 20, fill="red")  # Default: red (off)

        # Function to change AMK Status LED color
        def change_amk_status_color(self, color):
            self.amk_status_canvas.itemconfig(self.amk_status_led, fill=color)

        # Function to change AMK Control LED color
        def change_amk_control_color(self, color):
            self.amk_control_canvas.itemconfig(self.amk_control_led, fill=color)
        # Add this inside the MotorFrame class, after the AMK status and control LED code

        # Frame for sliders and numerical input
        self.sliders_frame = tk.Frame(self)
        self.sliders_frame.pack(pady=10)

        # Function to update the slider when number is entered
        def update_slider(slider, entry_var):
            try:
                value = int(entry_var.get())
                slider.set(value)
            except ValueError:
                pass  # Handle invalid input (non-numeric)

        # Function to update number entry when slider is moved
        def update_entry(entry_var, value):
            entry_var.set(int(value))

        # Create 3 sliders and associated numerical inputs
        self.slider_vars = []
        for i in range(3):
            # Slider label
            label = tk.Label(self.sliders_frame, text=f"Parameter {i+1}")
            label.grid(row=i, column=0, padx=5)
            
            # Slider (0 to 100 as an example range)
            slider = tk.Scale(self.sliders_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=lambda value, i=i: update_entry(self.slider_vars[i], value))
            slider.grid(row=i, column=1, padx=5)
            
            # Entry for numerical input
            entry_var = tk.StringVar()
            entry = tk.Entry(self.sliders_frame, textvariable=entry_var, width=5)
            entry.grid(row=i, column=2, padx=5)
            
            # Connect entry to slider updates
            entry_var.trace_add("write", lambda *args, slider=slider, entry_var=entry_var: update_slider(slider, entry_var))
            
        # Store the StringVar for future reference
        self.slider_vars.append(entry_var)
        
        # Frame for dropdown and input
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

        # Example to retrieve selected filter and value
        def get_selected_filter_value():
            selected_filter = self.selected_filter.get()
            filter_value = self.filter_value_var.get()
            print(f"Selected Filter: {selected_filter}, Value: {filter_value}")

        # Example usage: You can call get_selected_filter_value() to get the current selection and input


class MotorCommunication:
    def __init__(self, status_address, control_address, target_address):
        self.status_address = status_address
        self.control_address = control_address
        self.target_address = target_address
        self.amk_status = config["AMK_Status"]
        self.amk_control = config["AMK_Status"]

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
        for frame_name, bits in config.items():
            if frame_name == "AMK_Status":
                address_filter = self.status_address
            else:
                address_filter = self.control_address

            if address_filter is None or message.arbitration_id == address_filter:
                for bit, (canvas, oval) in bits.items():
                    bit_value = bit_values[bit]
                    self.update_circle_color(canvas, oval, bit_value)
        
if __name__ == "__main__":
    app = MotorControlApp()
    app.mainloop()
