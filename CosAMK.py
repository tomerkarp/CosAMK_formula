import tkinter as tk
from tkinter import Canvas
import serial.tools.list_ports
import can
import struct
from scrollable_frame import VerticalScrolledFrame as ScrollableFrame
import threading
import time


# CAN Operation Suite for AMK motor control
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
    "AMK_Actual values": {
        16: "AMK_ActualVelocity",
        32: "AMK_TorqueCurrent",
        48: "AMK_MagnetizingCurrent",
    },
    "AMK_Control": {
        8: "AMK_bInverterOn",
        9: "AMK_bDcOn",
        10: "AMK_bEnable",
        11: "AMK_bErrorReset",
    },
    "AMK_Setpoint": {
        16: "AMK_TargetVelocity",
        32: "AMK_TorqueLimitPositiv",
        48: "AMK_TorqueLimitNegativ",
    }    
}   
motor_config = {
    "Rear Left": {
        "status_address": 283,
        "control_address": 285,
        "target_address": 184,

    },
    "Rear Right": {
        "status_address": 284,
        "control_address": 286,
        "target_address": 185,

    },
    "Front Left": {
        "status_address": 287,
        "control_address": 289,
        "target_address": 188,

    },
    "Front Right": {
        "status_address": 288,
        "control_address": 290,
        "target_address": 189,
    }
}

class MotorControlApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Motor Control")
        self.geometry("1400x800")
        self.height = self.winfo_screenheight()
        self.communication_enabled = False
        self.checkbox_vars = { }
        self.comport_var = None
        self.bus : can.BusABC = None


        self.motors = [Motor(name, self.bus) for name in motor_config.keys()]
        self.create_main_frame()
        self.motor_frames = []
        i = 1
        for motor in self.motors:
            frame = tk.Frame(self, height=600)
            frame.grid(row=0, column=i, padx=5, pady=5, sticky="w")
            scrollable_frame = ScrollableFrame(frame, width=250, height=800)
            scrollable_frame.pack(fill="both", padx=0, pady=0, anchor="center")
            frame = MotorFrame(scrollable_frame, name = motor.name)
            frame.pack(fill="both", expand=True, padx=0, pady=0, anchor="center")
            i += 1

        
    def create_main_frame(self):
        self.main_frame = tk.Frame(self)
        self.main_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nw")
        self.comport_frame = tk.Frame(self.main_frame)
        self.comport_frame.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.comport_label = tk.Label(self.comport_frame, text="COM Port:")
        self.comport_label.pack(side="left", padx=5, pady=5)

        self.comport_var = tk.StringVar(self)
        self.comport_var.set("No COM Port Available")
        self.comport_dropdown = tk.OptionMenu(self.comport_frame, self.comport_var, "No COM Port Available")
        self.comport_dropdown.pack(side="left", padx=5, pady=5)


        self.enable_button = tk.Button(self.main_frame, text="Enable communication", command=self.toggle_communication)
        self.enable_button.grid(row=1, column=0, padx=5, pady=5, sticky="w")


        self.log_button = tk.Button(self.main_frame, text="Open Message Log", command=self.open_message_log)
        self.log_button.grid(row=2, column=0, padx=5, pady=5, sticky="w")



        self.create_amk_control_checkbox("AMK Status")

        self.update_comports()
        self.debug()

    

    def toggle_communication(self):
        if self.communication_enabled:
            self.disable_communication()
        else:
            self.enable_communication()

    def enable_communication(self):
        # Add your code to enable communication here
        # Return True if communication is successfully enabled
        # Return False if communication cannot be enabled
        print("Communication enabled")
        self.communication_enabled = True
        self.enable_button.config(text="Disable communication")

    def disable_communication(self):
        # Add your code to disable communication here
        print("Communication disabled")
        self.communication_enabled = False
        self.enable_button.config(text="Enable communication")

    def open_message_log(self):
        print("Message log opened")

    def create_amk_control_checkbox(self, text):
        self.checkbox_frame = tk.LabelFrame(self.main_frame, text=text, padx=10, pady=10)
        self.checkbox_frame.grid(row=4, column=0, rowspan=4, padx=5, pady=5, sticky="ew")

        for bit, control_name in config["AMK_Control"].items():
            var = tk.IntVar()
            checkbox = tk.Checkbutton(self.checkbox_frame, text=control_name, variable=var) #TODO: command=toggle_control   
            checkbox.pack(anchor='w', pady=2)
            self.checkbox_vars[bit] = var
    
    
    def update_comports(self):

        com_ports = self.get_com_ports()

        menu = self.comport_dropdown["menu"]
        menu.delete(0, "end")
        if com_ports:
            for port in com_ports:
                menu.add_command(label=port, command=tk._setit(self.comport_var, port))
            self.comport_var.set(com_ports[0])
        else:
            self.comport_var.set("No COM Port Available")

        self.after(1000, self.update_comports)

    def get_com_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    
    def debug(self):

        print("{", end="")
        print(",".join([f" {config['AMK_Control'][bit]} : {var.get()}" for bit, var in self.checkbox_vars.items()]), end="")
        print("}")
        self.after(5000, self.debug)



class Motor:
    def __init__(self, name, bus):
        self.name = name
        self.amk_status = config["AMK_Status"]
        self.amk_control = config["AMK_Control"]
        self.status_address = 111
        self.control_address = 111
        self.target_address = 111
        self.amk_gains = [0,0,0]
        self.bus = bus

class MotorFrame(tk.Frame):
    def __init__(self, parent, name):
        super().__init__(parent, bd=2, relief=tk.RIDGE)
        self.name = name
        self.label = tk.Label(self, text=self.name, font=("Calibri Bold", 16))
        self.label.pack(pady=10)

        self.amk_status_frame = tk.LabelFrame(self, text="AMK Status", font=("Calibri Bold", 12), padx=10, pady=10)
        self.amk_status_frame.pack(fill="x",pady=5)
        
        self.amk_control_frame = tk.LabelFrame(self, text="AMK Control", font=("Calibri Bold", 12), padx=10, pady=10)

        self.amk_control_frame.pack(fill="x",pady=5)

        self.led_widgets = {}
        self.create_leds(config["AMK_Status"], self.amk_status_frame)
        self.create_leds(config["AMK_Control"], self.amk_control_frame)


        self.sliders_frame = tk.Frame(self)
        self.sliders_frame.pack(fill="x", pady=5)

        self.slider_vars = []
        for i in range(3):
            label = tk.Label(self.sliders_frame, text=config["AMK_Setpoint"][16 + 16*i])
            label.grid(row=2*i, column=0, padx=1)
            slider = tk.Scale(self.sliders_frame, from_=0, to=100, orient="horizontal") #TODO: command=update_setpoint 

            slider.grid(row=2*i+1, column=0, padx=1)
            
            entry_var = tk.StringVar()
            entry = tk.Entry(self.sliders_frame, textvariable=entry_var, width=10)
            entry.grid(row=2*i+1, column=1, padx=1)

            self.after(100, lambda s=slider, v=entry_var: v.trace_add("write", lambda *args: self.update_slider(s, v)))
            self.slider_vars.append(entry_var)
    
        self.sliders_frame.pack(fill="x", pady=5)

        self.amk_vals_frame = tk.LabelFrame(self, text="AMK Actual values", font=("Calibri Bold", 12), padx=10, pady=10)
        self.amk_vals_frame.pack(fill="x",pady=5)
        self.amk_vals = {}
        self.create_amk_vals(config["AMK_Actual values"], self.amk_vals_frame)

        self.dropdown_frame = tk.Frame(self)
        self.dropdown_frame.pack(fill="x", pady=5)

        


    def create_leds(self, section, frame):
        for bit, control_name in section.items():
            led_frame = tk.Frame(frame)
            led_frame.pack(fill="x", pady=5)
            label = tk.Label(led_frame, text=control_name)
            label.pack(side="left")
            led = tk.Canvas(led_frame, width=20, height=20)
            led.pack(side="right")
            led_id = led.create_oval(5, 5, 20, 20, fill="red")
            self.led_widgets[bit] = (led, led_id)

    def update_slider(self, slider, entry_var):
        try:
            value = int(entry_var.get())
            slider.set(value)
        except ValueError:
            pass
    
    def create_amk_vals(self, section, frame):
        for bit, control_name in section.items():
            val_frame = tk.Frame(frame)
            val_frame.pack(fill="x", pady=5)
            label = tk.Label(val_frame, text=control_name)
            label.pack(side="left", padx=5)
            entry = tk.Entry(val_frame ,width=10)
            entry.insert(0, "100")
            entry.config(state="disabled", disabledbackground="lightgrey", disabledforeground="black")
            entry.pack(side="left", padx=5)
            self.amk_vals[bit] = entry

if __name__ == "__main__":
    app = MotorControlApp()
    app.mainloop()