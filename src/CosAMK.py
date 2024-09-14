import tkinter as tk
from tkinter import Canvas
from tkinter import ttk
import serial.tools.list_ports
import can
import struct
from scrollable_frame import VerticalScrolledFrame as ScrollableFrame
import threading
import time
import os
from datetime import datetime
import random
import logging

logging.basicConfig(filename="can_comm.log", level=logging.INFO)

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
        16: ("AMK_TargetVelocity",(-5000, 5000)),
        32: ("AMK_TorqueLimitPositiv", (0,10000)),
        48: ("AMK_TorqueLimitNegativ",(0,10000)),
    }    
}   
motor_config = {
    "Rear Left": {
        "status_address": 0x283,
        "control_address": 0x285,
        "target_address": 0x184,
    },
    "Rear Right": {
        "status_address": 0x284,
        "control_address": 0x286,
        "target_address": 0x185,

    },
    "Front Left": {
        "status_address": 0x287,
        "control_address": 0x289,   
        "target_address": 0x188,

    },
    "Front Right": {
        "status_address": 0x288,
        "control_address": 0x290,
        "target_address": 0x189,

    }
}

class CanComm:
    def __init__(self, bitrate=500000):
        self.is_sending = False
        self.enable = False
        self.bus = None
        self.bitrate = bitrate
        self.sending_thread = None 
        self.lock = threading.Lock()
        self.comm_enable = False
        self.msg_log = None
        self.comm_port = None
        

        self.amk_control_out = None


        self.motors = [Motor(name, self) for name in motor_config.keys()]

        self.control_app = MotorControlApp(self)
        self.listen_thread = threading.Thread(target=self.listen_to_can_bus)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        
    def update_bus(self, com_port):
        if self.bus is not None:
            self.bus.shutdown()
            self.bus = None
        print(com_port)
        self.comm_port = com_port
        try:
            if com_port == "Virtual":
                self.bus = can.interface.Bus(channel="vcan0", interface="virtual", bitrate=self.bitrate)
            else:
                self.bus = can.interface.Bus(channel=com_port, interface="slcan", bitrate=self.bitrate)
            test_message = can.Message(arbitration_id=0x7df, data=[0x02, 0x01, 0x00], is_extended_id=False)
            self.bus.send(test_message) 

        except Exception as e:
            print(e)
            self.bus = None
        

    def listen_to_can_bus(self):
        while True:
            if not self.comm_enable:
                time.sleep(1)
                continue    
            if self.comm_port == "Virtual":       
                # time.sleep(1)
                # print("test message")
                # test_arbitration_id = random.choice([0x283, 0x284, 0x287, 0x288])
                # test_data = [0x01, random.randint(0, 127), 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF] 
                # test_message = can.Message(arbitration_id=test_arbitration_id, data=test_data, is_extended_id=False)
                # self.receive_message(test_message)
                pass
            elif self.bus is not None:
                message = self.bus.recv(timeout=2)
                if message is not None:
                    self.receive_message(message)
                else:
                    for motor in self.motors:
                        motor.reset()
                
                
                
            

    
    def disable_communication(self):
        self.comm_enable = False
        for motor in self.motors:
            motor.reset()
        
                
    def receive_message(self, message: can.Message):
        if message is None:
            return
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

        
        
        # Using lock for thread-safe access to motor updates
        
        
        with self.lock:
            for motor in self.motors:
                motor.recieve_update(message, bit_values)
                # print(motor.amk_configs)
                # print(motor.amk_actual_values)
            self.update_log(message)
    
    def update_log(self, message):
        if self.control_app.msg_log is None or not self.control_app.msg_log.winfo_exists():
            return
        self.control_app.msg_log.add_message(message)

    def start_sending_messages(self) -> bool:
        self.update_bus(self.control_app.comport_var.get())
        if self.bus is None:
            return False
        if not self.is_sending:
            self.is_sending = True
            self.sending_thread = threading.Thread(target=self._send_continuously)
            self.sending_thread.start()
        return True

    
    def _send_continuously(self):
        counter = 0
        start_time = time.time()
        while self.is_sending:
            with self.lock:
                self.motors[0].send_message()
                self.motors[1].send_message()
                self.motors[2].send_message()
                self.motors[3].send_message()
                elapsed_time = (time.time() - start_time)*1000
                logging.info(f"------------------------Message {counter} sent after{elapsed_time:.2f} ms---------------------------------")
            counter += 1
            start_time = time.time()
            time.sleep(0.01)

    def stop_sending_messages(self):
        self.is_sending = False
        if self.sending_thread:
            self.sending_thread.join()

    
    def main_loop(self):
        self.control_app.mainloop()

class Motor:
    def __init__(self, name, parent: CanComm):
        self.name = name
        self.amk_status = {bit: 0 for bit in config["AMK_Status"]}
        self.amk_control = {bit: 0 for bit in config["AMK_Control"]}
        self.amk_configs = {"AMK_Status": self.amk_status, "AMK_Control": self.amk_control}
        self.amk_actual_values = {bit: 0 for bit in config["AMK_Actual values"]}
        self.status_address = motor_config[name]["status_address"]
        self.control_address = motor_config[name]["control_address"]    
        self.target_address = motor_config[name]["target_address"]  
        self.amk_gains = [0,0,0]
        self.parent = parent
        self.data = bytearray(8)
        self.data[0] = 0

        self.message = can.Message(arbitration_id=self.target_address, data=self.data, is_extended_id=False)



    def recieve_update(self, message: can.Message, bit_values):
        if not self.parent.comm_enable:
            return
        if message.arbitration_id == self.status_address:
            self.update_amk_actual_values(message)
            for key, bit in bit_values.items():
                self.amk_status[key] = bit
        elif message.arbitration_id == self.control_address:
            for key, bit in bit_values.items(): 
                self.amk_control[key] = bit 
        else:
            pass
    
    def reset(self):
        self.__init__(self.name, self.parent)

    def send_message(self):
        try:
            start_time = time.time()
            control_out = self.amk_control 
            self.data[1] = (control_out[8] << 0) | \
                        (control_out[9] << 1) | \
                        (control_out[10] << 2) | \
                        (control_out[11] << 3)
            
            struct.pack_into('<hhh', self.data, 2, self.amk_gains[0], self.amk_gains[1], self.amk_gains[2])

            self.message.data = self.data

            if self.parent.bus is not None:
                self.parent.bus.send(self.message)
            
            elapsed_time = (time.time() - start_time)*1000
            logging.info(f"Message sent to {self.name} in {elapsed_time:.2f} ms")

        except Exception as e:
            print(e)
    
    def update_amk_actual_values(self, message):
        self.amk_actual_values[16] = struct.unpack('<h', message.data[2:4])[0]
        self.amk_actual_values[32] = struct.unpack('<h', message.data[4:6])[0]
        self.amk_actual_values[48] = struct.unpack('<h', message.data[6:8])[0]

class MotorControlApp(tk.Tk):
    def __init__(self, parent: CanComm):
        super().__init__()
        self.title("Motor Control")
        self.geometry("1400x800")
        self.height = self.winfo_screenheight()
        self.checkbox_vars = { }
        self.comport_var = None
        self.bus : can.BusABC = None
        self.parent = parent
        self.msg_log = self.parent.msg_log
        self.protocol("WM_DELETE_WINDOW", self.on_exit)



        self.motors = self.parent.motors
        self.create_main_frame()
        self.motor_frames = []
        i = 1
        for motor in self.motors:
            frame = tk.Frame(self, height=600)
            frame.grid(row=0, column=i, padx=5, pady=5, sticky="w")
            scrollable_frame = ScrollableFrame(frame, width=250, height=800)
            scrollable_frame.pack(fill="both", padx=0, pady=0, anchor="center")
            frame = MotorFrame(scrollable_frame, motor_parent=motor)
            frame.pack(fill="both", expand=True, padx=0, pady=0, anchor="center")
            i += 1
        
        self.update_master()

        
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



        self.create_amk_control_checkbox("AMK Control")

        self.update_comports()
        # self.debug()

    

    def toggle_communication(self):
        if self.parent.comm_enable:
            self.disable_communication()
        else:
            self.enable_communication()

    def enable_communication(self):
        print("Communication enabled")
        self.parent.comm_enable = True
        if not self.parent.start_sending_messages():
            self.parent.comm_enable = False
        else:
            self.enable_button.config(text="Disable communication")

    def disable_communication(self):
        print("Communication disabled")
        self.parent.disable_communication()
        self.parent.stop_sending_messages()
        self.enable_button.config(text="Enable communication")

    def open_message_log(self):
        if self.msg_log is None or not self.msg_log.winfo_exists():
            print("Message log opened")
            self.msg_log = MessageLog()
        else:
            self.msg_log.lift()

    def create_amk_control_checkbox(self, text):
        self.checkbox_frame = tk.LabelFrame(self.main_frame, text=text, padx=10, pady=10)
        self.checkbox_frame.grid(row=4, column=0, rowspan=4, padx=5, pady=5, sticky="ew")

        for bit, control_name in config["AMK_Control"].items():
            var = tk.IntVar()
            checkbox = tk.Checkbutton(self.checkbox_frame, text=control_name, variable=var)
            checkbox.pack(anchor='w', pady=2)
            self.checkbox_vars[bit] = var
    
    
    def update_comports(self):

        com_ports = self.get_com_ports()

        current_selection = self.comport_var.get()

        menu = self.comport_dropdown["menu"]
        menu.delete(0, "end")

        com_ports.append("Virtual")

        if com_ports:
            for port in com_ports:
                menu.add_command(label=port, command=tk._setit(self.comport_var, port))
        
        if current_selection in com_ports:
            self.comport_var.set(current_selection)
        else:
            self.comport_var.set("Not Available")

        self.after(2000, self.update_comports)

    def get_com_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    
    def update_master(self):
        self.parent.amk_control_out = {bit: var.get() for bit, var in self.checkbox_vars.items()}
        self.after(1000, self.update_master)
        

    def debug(self):

        # print("{", end="")
        # print(",".join([f" {config['AMK_Control'][bit]} : {var.get()}" for bit, var in self.checkbox_vars.items()]), end="")
        # print("}")
        print(self.parent.amk_control_out)
        print(self.parent.comm_enable)
        self.after(5000, self.debug)
    
    def on_exit(self):
        self.parent.disable_communication()
        self.destroy()
        os._exit(0)
    

    
    


    
        
    
     

class MotorFrame(tk.Frame):
    def __init__(self, parent, motor_parent):
        super().__init__(parent, bd=2, relief=tk.RIDGE)
        self.name = motor_parent.name
        self.motor_parent = motor_parent    
        self.label = tk.Label(self, text=self.name, font=("Calibri Bold", 16))
        self.label.pack(pady=10)

        self.amk_status_frame = tk.LabelFrame(self, text="AMK Status", font=("Calibri Bold", 12), padx=10, pady=10)
        self.amk_status_frame.pack(fill="x",pady=5)
        
        self.amk_control_frame = tk.LabelFrame(self, text="AMK Control", font=("Calibri Bold", 12), padx=10, pady=10)

        self.amk_control_frame.pack(fill="x",pady=5)

        self.led_widgets = {"AMK_Status": {}, "AMK_Control": {}}
        self.create_leds("AMK_Status", self.amk_status_frame)
        self.create_leds("AMK_Control", self.amk_control_frame)


        self.sliders_frame = tk.Frame(self)
        self.sliders_frame.pack(fill="x", pady=5)

        self.slider_vars = []
        for i in range(3):
            slide_config = config["AMK_Setpoint"][16 + 16*i]
            label = tk.Label(self.sliders_frame, text=slide_config[0])
            label.grid(row=2*i, column=0, padx=1)
            slider = tk.Scale(self.sliders_frame, from_=slide_config[1][0], to=slide_config[1][1], orient="horizontal") 
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
        self.create_amk_vals("AMK_Actual values", self.amk_vals_frame)
        
        self.dropdown_active = tk.BooleanVar(value=False)
        self.dropdown_checkbox = tk.Checkbutton(self, text="Chnage default filters", command=self.toggle_dropdown, variable = self.dropdown_active)
        self.dropdown_checkbox.pack(fill="x", pady=5, padx=10, side="left")

        

        


    def create_leds(self, section_name, frame):
        for bit, control_name in config[section_name].items():
            led_frame = tk.Frame(frame)
            led_frame.pack(fill="x", pady=5)
            label = tk.Label(led_frame, text=control_name)
            label.pack(side="left")
            led = tk.Canvas(led_frame, width=20, height=20)
            led.pack(side="right")
            # if self.motor_parent.amk_configs[section_name][bit]:
            #     led_id = led.create_oval(5, 5, 20, 20, fill="green")
            # else:
            led_id = led.create_oval(5, 5, 20, 20, fill="red")
            self.led_widgets[section_name][bit] = (led, led_id)
        self.after(100, lambda s=section_name: self.update_leds(s))
    
    def update_leds(self, section_name):
        for bit, control_name in config[section_name].items():
            led, led_id = self.led_widgets[section_name][bit]
            if self.motor_parent.amk_configs[section_name][bit]:
                led.itemconfig(led_id, fill="green")
            else:
                led.itemconfig(led_id, fill="red")
        self.after(100, lambda s=section_name: self.update_leds(s))


    def update_slider(self, slider, entry_var):
        try:
            value = int(entry_var.get())
            slider.set(value)
        except ValueError:
            pass
    
    def create_amk_vals(self, section_name, frame):
        for bit, control_name in config[section_name].items():
            val_frame = tk.Frame(frame)
            val_frame.pack(fill="x", pady=5)
            label = tk.Label(val_frame, text=control_name)
            label.pack(side="left", padx=5)
            entry = tk.Entry(val_frame ,width=10)
            entry.insert(0, str(self.motor_parent.amk_actual_values[bit]))
            entry.config(state="disabled", disabledbackground="lightgrey", disabledforeground="black")
            entry.pack(side="right", padx=5, anchor="e")
            self.amk_vals[bit] = entry
        self.after(100, lambda s=section_name: self.update_amk_vals(s))
    
    def update_amk_vals(self, section_name):
        for bit, control_name in config[section_name].items():
            entry = self.amk_vals[bit]
            entry.config(state="normal") 
            entry.delete(0, "end")
            new_value = self.motor_parent.amk_actual_values[bit]
            entry.insert(0, str(new_value))
            entry.config(state="disabled")
        self.after(100, lambda s=section_name: self.update_amk_vals(s))
    
    def create_dropdown(self):
        self.dropdown_frame = tk.Frame(self)
        self.dropdown_frame.pack(fill="x", pady=5)
        


        self.filter_list = list(motor_config[self.name].keys())
        self.selected_filter = tk.StringVar()
        self.selected_filter.set(self.filter_list[0])  
        self.filter_dropdown = tk.OptionMenu(self.dropdown_frame, self.selected_filter, *self.filter_list, command=self.update_filter_val)

        self.filter_dropdown.pack(side="left", padx=5)

        self.filter_val = tk.StringVar()
        self.filter_val_entry = tk.Entry(self.dropdown_frame, textvariable=self.filter_val, width=10)
        self.filter_val_entry.insert(0, f"{motor_config[self.name][self.selected_filter.get()]}")
        self.filter_val_entry.pack(side="left", padx=10, anchor="e") 


    def update_filter_val(self, value):
        self.filter_val.set(f"{motor_config[self.name][value]}")

    def toggle_dropdown(self):#TODO: still buggy with GUI
        if self.dropdown_active.get():
            self.create_dropdown()
        else:
            self.dropdown_frame.pack_forget()
    

class MessageLog(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title("Message Log")

        self.log_frame = tk.Frame(self)
        self.log_frame.pack(fill="both", expand=True)

        columns = ("Time", "Id", "Data")
        self.tree = ttk.Treeview(self.log_frame, columns=columns, show="headings")
        self.tree.heading("Time", text="Time")
        self.tree.heading("Id", text="ID")
        self.tree.heading("Data", text="Data")

        self.tree.column("Time", width=100, anchor="center")
        self.tree.column("Id", width=100, anchor="center")
        self.tree.column("Data", width=400, anchor="center")

        self.tree.pack(fill="both", expand=True)
        self.message_cache = {}
    
    def add_message(self, message):
        time = datetime.fromtimestamp(message.timestamp).strftime("%H:%M:%S")
        msg_id = f"0x{message.arbitration_id:X}"
        data = " ".join(format(byte, '02x') for byte in message.data)
        if message.arbitration_id in self.message_cache:
            item_id = self.message_cache[message.arbitration_id]
            self.tree.item(item_id, values=(time, msg_id, data))
        else:
            item_id = self.tree.insert("", "end", values=(time, msg_id, data))
            self.message_cache[message.arbitration_id] = item_id
        
        self.tree.yview_moveto(1)
        





if __name__ == "__main__":
    app = CanComm()
    app.main_loop()