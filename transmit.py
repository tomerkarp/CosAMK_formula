import can

def check_pcan():
    try:
        # Try to open a connection to the PCAN virtual bus (e.g., PCAN_USBBUS1)
        bus = can.interface.Bus(channel='PCAN_USBBUS1', bustype='pcan')
        print(f"Successfully connected to PCAN channel: {bus.channel_info}")

    except can.CanError as e:
        print(f"Error connecting to PCAN: {e}")

if __name__ == "__main__":
    check_pcan()
