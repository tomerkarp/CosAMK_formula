import threading 
import can
import threading
from datetime import datetime
import time
import struct



import threading 
import can
from datetime import datetime
import time
import struct

class CANBusComm:
    def __init__(self, bitrate=500000):
        self.amk_status = [0]*8
        self.amk_control = [0]*4
        self.amk_target = [0]*3
        self.amk_set = [0]*3
        self.bus = None
        self.com_port = 0
        self.bitrate = bitrate

        self.sending_thread = None
        self.listen_thread = None
        self.lock = threading.Lock()  # Added a lock for thread safety
        
        motor_names = ["Rear Left", "Rear Right", "Front Left", "Front Right"]
        self.motors = [Motor(name) for name in motor_names]
        
        self.enable = False
        self.is_sending = False

        # Start listener thread
        self.listen_thread = threading.Thread(target=self.listen_to_can_bus)
        self.listen_thread.daemon = True
        self.listen_thread.start()
    
    def receive_message(self, message: can.message):
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
    
    def toggle_txrx(self):
        if self.enable:
            self.enable = False
            self.is_sending = False  # Stop sending messages when disabling
            if self.bus is not None:
                self.bus.shutdown()  # Shut down the CAN bus connection
                self.bus = None
            for motor in self.motors:
                motor.bus = None
            print("TXRX disabled")
        else:
            self.bus = can.interface.Bus(bustype='virtual', channel=self.com_port, bitrate=self.bitrate)
            self.enable = True
            for motor in self.motors:
                motor.bus = self.bus
            print("TXRX enabled")
    
    def start_sending_messages(self):
        if not self.is_sending:
            self.is_sending = True
            self.sending_thread = threading.Thread(target=self._send_continuously)
            self.sending_thread.start()
    
    def _send_continuously(self):
        while self.is_sending:
            with self.lock:  # Lock to ensure thread-safe access to motors
                for motor in self.motors:
                    motor.send_message()
            time.sleep(0.1)

    def stop_sending_messages(self):
        self.is_sending = False
        if self.sending_thread:
            self.sending_thread.join()  # Ensure sending thread stops cleanly

    def listen_to_can_bus(self):
        while True:
            if self.enable and self.bus is not None:
                message = self.bus.recv()  # Receive CAN messages
                if message:
                    print(f"Message received: {message}")  # Added more detailed message printing
                    self.recieve_message(message)
    
    # Graceful shutdown added
    def stop(self):
        self.is_sending = False
        self.enable = False
        if self.sending_thread:
            self.sending_thread.join()  # Wait for the sending thread to finish
        if self.bus is not None:
            self.bus.shutdown()  # Shutdown the CAN bus connection
            self.bus = None
        print("CANBusComm stopped.")


class Motor:
    def __init__(self, motor_name):
        self.name = motor_name
        self.amk_status = [0]*8
        self.amk_control = [0]*4
        self.status_address = 111 
        self.control_address = 11
        self.target_address = 111
        self.amk_gains = [0,0,0]
        self.bus = None

    def recieve_update(self, message: can.Message, bits):
        if message.arbitration_id == self.status_address:
            for i, bit in enumerate(bits.values()):
                self.amk_status[i] = bit
        elif message.arbitration_id == self.control_address:
            for i, bit in enumerate(bits.values()):  # Updated: should use bits.values(), not bit.values()
                self.amk_control[i] = bit  # Fixed: now updates amk_control, not amk_status
        else:
            print(f"{self.name}: Not receiving relevant messages")
    
    def send_message(self):
        try:
            data = bytearray(8)
            
            data[1] = sum((target << i) for i, target in enumerate(self.amk_target))

            for i, value in enumerate(self.amk_gains):    
                struct.pack_into('<h', data, 2 * i, value)
            
            message = can.Message(arbitration_id=self.target_address, data=data, is_extended_id=False)
            
            self.bus.send(message)
            print(f"Message sent from {self.name}: {message}")  # Added detailed logging of sent messages

        except ValueError as e:
            print(f"Invalid input: {e}")

            

# Add functions to map terminal commands to CANBusComm functionality
can_comm = CANBusComm()

def toggle_comm():
    """Enable CAN bus communication."""
    can_comm.toggle_txrx()
    return "CAN communication enabled."

def disable_comm():
    """Disable CAN bus communication."""
    can_comm.toggle_txrx()
    return "CAN communication disabled."

def start_sending():
    """Start sending CAN messages to the motors."""
    can_comm.start_sending_messages()
    return "Started sending messages."

def stop_sending():
    """Stop sending CAN messages to the motors."""
    can_comm.stop_sending_messages()
    return "Stopped sending messages."

def help():
    """Display available commands."""
    return "Available commands: enable_comm, disable_comm, start_sending, stop_sending, quit"

# Terminal shell function
def shell():
    print("Welcome to the CAN bus control terminal!")
    print("Type 'help' to see available commands.")
    
    # Dictionary to map commands to functions
    commands = {
        'toggle_comm': toggle_comm,
        'disable_comm': disable_comm,
        'start_sending': start_sending,
        'stop_sending': stop_sending,
        'help': help
    }
    # 
    while True:
        # Prompt user for input
        command = input(">> ").strip()
        
        if command == 'quit':
            print("Exiting the shell.")
            break  # Exit the loop and program
        
        # Check if the command is in the dictionary
        if command in commands:
            # Call the function associated with the command
            result = commands[command]()
            print(result)
        else:
            print(f"Unknown command: {command}. Type 'help' for a list of commands.")



if __name__ == "__main__":
    
    shell()
