import serial
import socket
import select

# ================= ÅäÖÃ =================
SERIAL_PORT = "/dev/ttyUSB0"
SERIAL_BAUD = 57600

UDP_LISTEN_IP = "0.0.0.0"
UDP_LISTEN_PORT = 14550
# =======================================

def main():
    # 1. ´ò¿ª´®¿Ú£¨Pixhawk£©
    ser = serial.Serial(
        port=SERIAL_PORT,
        baudrate=SERIAL_BAUD,
        timeout=0,          # ·Ç×èÈû
    )
    print(f"Serial opened on {SERIAL_PORT} @ {SERIAL_BAUD}")

    # 2. ´ò¿ª UDP Ì×½Ó×Ö£¨¼àÌý QGC£©
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_LISTEN_IP, UDP_LISTEN_PORT))
    sock.setblocking(False)
    print(f"UDP listening on {UDP_LISTEN_IP}:{UDP_LISTEN_PORT}")

    qgc_addr = None  # ¼ÇÂ¼ QGC µÄ (ip, port)

    while True:
        rlist, _, _ = select.select([ser, sock], [], [], 0.01)

        # -------- ´®¿Ú -> UDP£ºPixhawk -> QGC --------
        if ser in rlist:
            data = ser.read(ser.in_waiting or 1)
            if data and qgc_addr is not None:
                sock.sendto(data, qgc_addr)

        # -------- UDP -> ´®¿Ú£ºQGC -> Pixhawk --------
        if sock in rlist:
            data, addr = sock.recvfrom(4096)
            # ¼ÇÂ¼ QGC µØÖ·
            qgc_addr = addr
            if data:
                ser.write(data)

if __name__ == "__main__":
    main()

