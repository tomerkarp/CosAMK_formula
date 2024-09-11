import socket
import json

def receive_can_messages():
    """Receive CAN messages over UDP."""
    # Setup UDP socket
    udp_ip = "127.0.0.1"  # Localhost
    udp_port = 5005       # Port number
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((udp_ip, udp_port))

    print(f"Listening for messages on {udp_ip}:{udp_port}...")

    while True:
        # Receive the message
        data, addr = sock.recvfrom(1024)  # Buffer size is 1024 bytes
        message = json.loads(data.decode())
        print(f"Received message: {message} from {addr}")

if __name__ == "__main__":
    receive_can_messages()
