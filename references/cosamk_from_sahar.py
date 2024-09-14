import tkinter as tk
from tkinter import Canvas
from tkinter import ttk
import can
import threading
import struct
from datetime import datetime
import time

class CANBusMonitor:
    def __init__(self, master, bitrate=500000, oval_size=50):
        self.master = master
        self.bitrate = bitrate
        self.oval_size = oval_size

        self.reading_enabled = False
        self.transmitting_enabled = False
        self.sending_message = False

        # Configuration dictionary for frames, bits, and titles
        self.config = {
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

        # Make the window resizable
        self.master.geometry("1000x800")
        self.master.minsize(1000, 800)

        # Create frames for ovals
        self.frames = {}
        self.create_frames()

        # Dropdown for selecting reading COM port
        self.reading_com_label = tk.Label(master, text="Reading COM Port:")
        self.reading_com_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")

        self.reading_com_var = tk.StringVar(value="COM14")
        self.reading_com_dropdown = ttk.Combobox(master, textvariable=self.reading_com_var, values=["COM4", 0])
        self.reading_com_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.toggle_reading_button = tk.Button(master, text="Enable Reading", command=self.toggle_reading)
        self.toggle_reading_button.grid(row=0, column=2, padx=10, pady=10)

        # Dropdown for selecting transmitting COM port
        self.transmitting_com_label = tk.Label(master, text="Transmitting COM Port:")
        self.transmitting_com_label.grid(row=0, column=3, padx=10, pady=10, sticky="e")

        self.transmitting_com_var = tk.StringVar(value="COM14")
        self.transmitting_com_dropdown = ttk.Combobox(master, textvariable=self.transmitting_com_var, values=["COM4", 0])
        self.transmitting_com_dropdown.grid(row=0, column=4, padx=10, pady=10, sticky="w")

        self.toggle_transmit_button = tk.Button(master, text="Enable Transmit", command=self.toggle_transmit)
        self.toggle_transmit_button.grid(row=0, column=5, padx=10, pady=10)

        # Set up the entry for the address filters
        self.status_address_label = tk.Label(master, text="Status Address Filter:")
        self.status_address_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        
        self.status_address_entry = tk.Entry(master)
        self.status_address_entry.insert(0, "283")
        self.status_address_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        self.control_address_label = tk.Label(master, text="Control Address Filter:")
        self.control_address_label.grid(row=1, column=3, padx=10, pady=10, sticky="e")
        
        self.control_address_entry = tk.Entry(master)
        self.control_address_entry.insert(0, "285")
        self.control_address_entry.grid(row=1, column=4, padx=10, pady=10, sticky="w")

        # Target address entry for sending messages
        self.target_address_label = tk.Label(master, text="Target Address:")
        self.target_address_label.grid(row=2, column=0, padx=10, pady=10, sticky="e")

        self.target_address_entry = tk.Entry(master)
        self.target_address_entry.insert(0, "184")
        self.target_address_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # Set up specific bits and integers for the output message
        self.amk_inverter_on_label = tk.Label(master, text="AMK_bInverterOn:")
        self.amk_inverter_on_label.grid(row=3, column=0, padx=10, pady=10, sticky="e")

        self.amk_inverter_on_var = tk.IntVar()
        self.amk_inverter_on_checkbox = tk.Checkbutton(master, variable=self.amk_inverter_on_var)
        self.amk_inverter_on_checkbox.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        self.amk_dc_on_label = tk.Label(master, text="AMK_bDcOn:")
        self.amk_dc_on_label.grid(row=3, column=2, padx=10, pady=10, sticky="e")

        self.amk_dc_on_var = tk.IntVar()
        self.amk_dc_on_checkbox = tk.Checkbutton(master, variable=self.amk_dc_on_var)
        self.amk_dc_on_checkbox.grid(row=3, column=3, padx=10, pady=10, sticky="w")

        self.amk_enable_label = tk.Label(master, text="AMK_bEnable:")
        self.amk_enable_label.grid(row=3, column=4, padx=10, pady=10, sticky="e")

        self.amk_enable_var = tk.IntVar()
        self.amk_enable_checkbox = tk.Checkbutton(master, variable=self.amk_enable_var)
        self.amk_enable_checkbox.grid(row=3, column=5, padx=10, pady=10, sticky="w")

        self.amk_error_reset_label = tk.Label(master, text="AMK_bErrorReset:")
        self.amk_error_reset_label.grid(row=3, column=6, padx=10, pady=10, sticky="e")

        self.amk_error_reset_var = tk.IntVar()
        self.amk_error_reset_checkbox = tk.Checkbutton(master, variable=self.amk_error_reset_var)
        self.amk_error_reset_checkbox.grid(row=3, column=7, padx=10, pady=10, sticky="w")

        self.amk_target_velocity_label = tk.Label(master, text="AMK_TargetVelocity:")
        self.amk_target_velocity_label.grid(row=4, column=0, padx=10, pady=10, sticky="e")

        self.amk_target_velocity_entry = tk.Entry(master)
        self.amk_target_velocity_entry.grid(row=4, column=1, padx=10, pady=10, sticky="w")

        self.amk_torque_limit_positiv_label = tk.Label(master, text="AMK_TorqueLimitPositiv:")
        self.amk_torque_limit_positiv_label.grid(row=4, column=2, padx=10, pady=10, sticky="e")

        self.amk_torque_limit_positiv_entry = tk.Entry(master)
        self.amk_torque_limit_positiv_entry.grid(row=4, column=3, padx=10, pady=10, sticky="w")

        self.amk_torque_limit_negativ_label = tk.Label(master, text="AMK_TorqueLimitNegativ:")
        self.amk_torque_limit_negativ_label.grid(row=4, column=4, padx=10, pady=10, sticky="e")

        self.amk_torque_limit_negativ_entry = tk.Entry(master)
        self.amk_torque_limit_negativ_entry.grid(row=4, column=5, padx=10, pady=10, sticky="w")

        self.send_button = tk.Button(master, text="Start Sending", command=self.toggle_send_message)
        self.send_button.grid(row=4, column=6, padx=10, pady=10)

        # Button to open message log window
        self.open_log_button = tk.Button(master, text="Open Message Log", command=self.open_message_log_window)
        self.open_log_button.grid(row=5, column=0, columnspan=8, padx=10, pady=10)

        self.bus = None
        self.send_bus = None
        self.message_log_window = None
        self.message_send_thread = None

        self.listen_thread = threading.Thread(target=self.listen_to_can_bus)
        self.listen_thread.daemon = True
        self.listen_thread.start()

        self.message_cache = {}

    def create_frames(self):
        row = 6
        for frame_name, bits in self.config.items():
            frame = tk.Frame(self.master, bd=2, relief="sunken")
            frame.grid(row=row, column=0, columnspan=8, padx=10, pady=10, sticky="nsew")
            tk.Label(frame, text=frame_name, font=("Helvetica", 16)).pack(pady=10)
            self.frames[frame_name] = frame

            bit_frame = tk.Frame(frame)
            bit_frame.pack(pady=10)

            for bit, title in bits.items():
                bit_container = tk.Frame(bit_frame)
                bit_container.pack(side=tk.LEFT, padx=5, pady=5)

                label = tk.Label(bit_container, text=f"{title}({bit})")
                label.pack(pady=5)
                canvas = Canvas(bit_container, width=self.oval_size, height=self.oval_size)
                canvas.pack(pady=5)
                oval = canvas.create_oval(5, 5, self.oval_size - 5, self.oval_size - 5, fill='red')
                bits[bit] = (canvas, oval)
            row += 1

    def listen_to_can_bus(self):
        while True:
            if self.reading_enabled and self.bus is not None:
                message = self.bus.recv()
                if message is not None:
                    self.master.after(0, self.update_gui, message)
    
    def update_gui(self, message):
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

        try:
            status_address_filter = int(self.status_address_entry.get(), 16)
        except ValueError:
            status_address_filter = None

        try:
            control_address_filter = int(self.control_address_entry.get(), 16)
        except ValueError:
            control_address_filter = None

        for frame_name, bits in self.config.items():
            if frame_name == "AMK_Status":
                address_filter = status_address_filter
            else:
                address_filter = control_address_filter

            if address_filter is None or message.arbitration_id == address_filter:
                for bit, (canvas, oval) in bits.items():
                    bit_value = bit_values[bit]
                    self.update_circle_color(canvas, oval, bit_value)
        
        self.display_message(message)
    
    def update_circle_color(self, canvas, oval, bit_value):
        color = 'green' if bit_value == 1 else 'red'
        canvas.itemconfig(oval, fill=color)
    
    def display_message(self, message):
        timestamp = datetime.fromtimestamp(message.timestamp).strftime('%H:%M:%S.%f')[:-3]
        msg_id_hex = f'0x{message.arbitration_id:X}'
        data = ' '.join(format(byte, '02x') for byte in message.data)

        if self.message_log_window:
            if message.arbitration_id in self.message_cache:
                item_id = self.message_cache[message.arbitration_id]
                self.tree.item(item_id, values=(timestamp, msg_id_hex, data))
            else:
                item_id = self.tree.insert('', 'end', values=(timestamp, msg_id_hex, data))
                self.message_cache[message.arbitration_id] = item_id

            self.tree.yview_moveto(1)

    def open_message_log_window(self):
        if self.message_log_window is None or not self.message_log_window.winfo_exists():
            self.message_log_window = tk.Toplevel(self.master)
            self.message_log_window.title("Message Log")

            self.tree_frame = tk.Frame(self.message_log_window)
            self.tree_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

            columns = ('timestamp', 'id', 'data')
            self.tree = ttk.Treeview(self.tree_frame, columns=columns, show='headings')
            self.tree.heading('timestamp', text='Timestamp')
            self.tree.heading('id', text='ID')
            self.tree.heading('data', text='Data')

            self.tree.column('timestamp', anchor='center', width=200)
            self.tree.column('id', anchor='center', width=100)
            self.tree.column('data', anchor='center', width=400)

            self.tree.pack(expand=True, fill=tk.BOTH)
        else:
            self.message_log_window.lift()

    def send_message(self):
        try:
            target_address = int(self.target_address_entry.get(), 16)
            amk_inverter_on = self.amk_inverter_on_var.get()
            amk_dc_on = self.amk_dc_on_var.get()
            amk_enable = self.amk_enable_var.get()
            amk_error_reset = self.amk_error_reset_var.get()
            if int(self.amk_target_velocity_entry.get()) != 0:
                # Hard coded values that have proven to run the motor forward
                amk_target_velocity = 100
                amk_torque_limit_positiv = 9999
                amk_torque_limit_negativ = -2000
            else:
                amk_target_velocity = int(self.amk_target_velocity_entry.get())
                amk_torque_limit_positiv = int(self.amk_torque_limit_positiv_entry.get())
                amk_torque_limit_negativ = -int(self.amk_torque_limit_negativ_entry.get())

            data = bytearray(8)
            # not usind data[0] because it's reserved
            data[1] = (amk_inverter_on << 0) | (amk_dc_on << 1) | (amk_enable << 2) | (amk_error_reset << 3)
            struct.pack_into('<h', data, 2, amk_target_velocity)
            struct.pack_into('<h', data, 4, amk_torque_limit_positiv)
            struct.pack_into('<h', data, 6, amk_torque_limit_negativ)

            message = can.Message(arbitration_id=target_address, data=data, is_extended_id=False)
            self.send_bus.send(message)

            # Display sent message
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            msg_id_hex = f'0x{message.arbitration_id:X}'
            data = ' '.join(format(byte, '02x') for byte in message.data)
            self.display_sent_message(timestamp, msg_id_hex, data)

        except ValueError as e:
            print(f"Invalid input: {e}")

    def display_sent_message(self, timestamp, msg_id_hex, data):
        arbitration_id = int(msg_id_hex, 16)
        if self.message_log_window:
            if arbitration_id in self.message_cache:
                item_id = self.message_cache[arbitration_id]
                self.tree.item(item_id, values=(timestamp, msg_id_hex, data))
            else:
                item_id = self.tree.insert('', 'end', values=(timestamp, msg_id_hex, data))
                self.message_cache[arbitration_id] = item_id
            self.tree.yview_moveto(1)

    def toggle_reading(self):
        if self.reading_enabled:
            self.reading_enabled = False
            if self.bus is not None:
                self.bus.shutdown()
                self.bus = None
            self.toggle_reading_button.config(text="Enable Reading")
            print("Reading disabled.")
        else:
            com_port = self.reading_com_var.get()
            if com_port == self.transmitting_com_var.get() and self.transmitting_enabled:
                self.bus = self.send_bus
            else:
                self.bus = can.interface.Bus(bustype='slcan', channel=com_port, bitrate=self.bitrate)
            self.reading_enabled = True
            self.toggle_reading_button.config(text="Disable Reading")
            print(f"Reading enabled on {com_port}.")

    def toggle_transmit(self):
        if self.transmitting_enabled:
            self.transmitting_enabled = False
            if self.send_bus is not None:
                self.send_bus.shutdown()
                self.send_bus = None
            self.toggle_transmit_button.config(text="Enable Transmit")
            print("Transmitting disabled.")
        else:
            com_port = self.transmitting_com_var.get()
            if com_port == self.reading_com_var.get() and self.reading_enabled:
                self.send_bus = self.bus
            else:
                self.send_bus = can.interface.Bus(bustype='slcan', channel=com_port, bitrate=self.bitrate)
            self.transmitting_enabled = True
            self.toggle_transmit_button.config(text="Disable Transmit")
            print(f"Transmitting enabled on {com_port}.")

    def toggle_send_message(self):
        if self.sending_message:
            self.sending_message = False
            self.send_button.config(text="Start Sending")
            if self.message_send_thread is not None:
                self.message_send_thread = None
        else:
            self.sending_message = True
            self.send_button.config(text="Stop Sending")
            self.message_send_thread = threading.Thread(target=self.send_message_continuously)
            self.message_send_thread.daemon = True
            self.message_send_thread.start()

    def send_message_continuously(self):
        while self.sending_message:
            self.send_message()
            time.sleep(0.002) #NO FUCKING DELAY PLEASE



if __name__ == '__main__':
    root = tk.Tk()
    root.title("CAN Bus Monitor")
    monitor = CANBusMonitor(root)
    root.mainloop()
    




