import threading
import queue
import time
import random
import signal
import sys
import serial.tools.list_ports


def get_com_ports():
    ports = serial.tools.list_ports.comports()
    port_list = [port.device for port in ports]
    return port_list

print(get_com_ports())
