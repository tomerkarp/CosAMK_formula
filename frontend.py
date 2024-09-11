import tkinter as tk
from tkinter import ttk
import threading

# Import the CAN bus communication backend
from backend import CANBusComm  # Assuming the backend is in a file called can_backend.py


class MainControlFrame(tk.Frame):
    def __init__(self, parent, backend):
        super().__init__(parent, bd=2, relief=tk.RIDGE)
        self.backend = backend  # The backend communication handler

        # Title
        self.title_label = tk.Label(self, text="Main Controls", font=("Calibri Bold", 16))
        self.title_label.grid(row=0, column=1, columnspan=3, pady=(1, 0), padx=300)

        # COM port dropdown
        self.comport_label = tk.Label(self, text="Select COM Port:")
        self.comport_label.grid(row=1, column=0, padx=(15, 0), sticky="e")
        self.comport_var = tk.StringVar(self)
        self.comport_dropdown = tk.OptionMenu(self, self.comport_var, "COM1", "COM2", "COM3")
        self.comport_dropdown.grid(row=1, column=1, padx=(0, 15), sticky="w")

        # Enable Communication Button
        self.enable_button = tk.Button(self, text="Enable Communication", command=self.toggle_communication)
        self.enable_button.grid(row=1, column=2, padx=10, sticky="w")

        # Open Message Log button
        self.log_button = tk.Button(self, text="Open Message Log", width=20, command=self.open_message_log)
        self.log_button.grid(row=1, column=3, padx=10, sticky="w")

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

    def toggle_communication(self):
        """Toggle the CAN bus communication on/off."""
        self.backend.toggle_txrx()
        if self.backend.enable:
            self.enable_button.config(text="Disable Communication")
        else:
            self.enable_button.config(text="Enable Communication")

    def open_message_log(self):
        """Open the message log window (optional)."""
        print("Message log opened")  # This can be connected to a message log GUI frame


class MotorFrame(tk.Frame):
    def __init__(self, parent, motor):
        super().__init__(parent, bd=2, relief=tk.RIDGE)
        self.motor = motor  # Reference to the motor backend

        # Label for motor name
        self.label = tk.Label(self, text=self.motor.name, font=("Calibri Bold", 16))
        self.label.grid(row=0, column=0, columnspan=2, pady=10)

        # AMK Status and Control LED-like indicators
        self.status_label = tk.Label(self, text="AMK Status")
        self.status_label.grid(row=1, column=0, padx=5)
        self.status_led = tk.Canvas(self, width=20, height=20)
        self.status_led.grid(row=1, column=1, padx=5)
        self.status_led_id = self.status_led.create_oval(5, 5, 20, 20, fill="red")

        self.control_label = tk.Label(self, text="AMK Control")
        self.control_label.grid(row=2, column=0, padx=5)
        self.control_led = tk.Canvas(self, width=20, height=20)
        self.control_led.grid(row=2, column=1, padx=5)
        self.control_led_id = self.control_led.create_oval(5, 5, 20, 20, fill="red")

        # Motor control sliders
        self.slider_frame = tk.Frame(self)
        self.slider_frame.grid(row=3, column=0, columnspan=2)

        for i in range(3):
            tk.Label(self.slider_frame, text=f"Parameter {i+1}").grid(row=i, column=0, padx=5)
            slider = tk.Scale(self.slider_frame, from_=0, to=100, orient=tk.HORIZONTAL)
            slider.grid(row=i, column=1, padx=5)

    def update_leds(self, status_color, control_color):
        """Update the LEDs for AMK Status and AMK Control."""
        self.status_led.itemconfig(self.status_led_id, fill=status_color)
        self.control_led.itemconfig(self.control_led_id, fill=control_color)


class MotorControlApp(tk.Tk):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend

        # Create main control frame
        self.main_frame = MainControlFrame(self, backend)
        self.main_frame.pack(pady=10)

        # Create motor frames
        for motor in backend.motors:
            motor_frame = MotorFrame(self, motor)
            motor_frame.pack(pady=10)

        # Periodically update GUI based on backend state
        self.update_gui()

    def update_gui(self):
        """Update the GUI elements based on backend status."""
        for motor_frame, motor in zip(self.winfo_children()[1:], self.backend.motors):
            status_color = "green" if sum(motor.amk_status) else "red"
            control_color = "green" if sum(motor.amk_control) else "red"
            motor_frame.update_leds(status_color, control_color)

        self.after(1000, self.update_gui)  # Update every second


# Initialize the CAN bus backend
backend = CANBusComm()

# Create and run the GUI app
app = MotorControlApp(backend)
app.mainloop()
