import tkinter as tk
from tkinter import Canvas
import serial.tools.list_ports

class MotorControlApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AMK Motor Control")
        self.geometry("1100x800")
        
        # Create a main control section above the motor-specific sections
        self.main_controls = MainControlFrame(self)
        self.main_controls.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        
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
        
        # Label for the main control section
        self.label = tk.Label(self, text="Main Controls", font=("Arial", 16))
        self.label.pack(pady=5)

        # Transmitting COM port selection dropdown
        # Transmitting COM port selection dropdown
        self.comport_label = tk.Label(self, text="Select COM Port:")
        self.comport_label.pack()

        # Function to search for all available COM ports
        def get_com_ports():
            ports = serial.tools.list_ports.comports()
            return [port.device for port in ports]

        # Get the available COM ports dynamically
        com_ports = get_com_ports()

        # Fallback in case no COM ports are found
        if not com_ports:
            com_ports = ["No COM Ports Available"]

        # StringVar to hold the selected COM port
        self.comport_var = tk.StringVar(self)
        self.comport_var.set(com_ports[0])  # Default selection

        # Create the dropdown (OptionMenu) with dynamic COM port list
        self.comport_dropdown = tk.OptionMenu(self, self.comport_var, *com_ports)
        self.comport_dropdown.pack(pady=5)

        # # Create the dropdown (OptionMenu)
        # self.comport_dropdown = tk.OptionMenu(self, self.comport_var, *com_ports)
        # self.comport_dropdown.pack(pady=5)
        
        # Enable communication button
        self.enable_button = tk.Button(self, text="Enable Communication", width=20)
        self.enable_button.pack(pady=5)

        # Checkboxes
        self.checkbox_vars = []
        self.checkbox_frame = tk.Frame(self)  # Frame to hold checkboxes horizontally
        self.checkbox_frame.pack(pady=5)

        self.checkbox_vars = []
        for i in range(4):
            var = tk.IntVar()
            checkbox = tk.Checkbutton(self.checkbox_frame, text=f"Checkbox {i+1}", variable=var)
            checkbox.pack(side="left", padx=10)  # Pack horizontally
            self.checkbox_vars.append(var)

        # Open message log button
        self.log_button = tk.Button(self, text="Open Message Log", width=20)
        self.log_button.pack(pady=10)

class MotorFrame(tk.Frame):
    def __init__(self, parent, motor_number):
        super().__init__(parent, bd=2, relief=tk.RIDGE)
        self.motor_number = motor_number
        
        # Label for the motor
        self.label = tk.Label(self, text=f"Motor {motor_number}", font=("Arial", 16))
        self.label.pack(pady=20)
        
        # Placeholder buttons (e.g., for controlling speed, torque, etc.)
        self.start_button = tk.Button(self, text="Start", width=10)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(self, text="Stop", width=10)
        self.stop_button.pack(pady=10)

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

        
        
if __name__ == "__main__":
    app = MotorControlApp()
    app.mainloop()
