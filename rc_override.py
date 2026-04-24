import select
import socket
import struct
import sys
import time


#DRONE_IP = "127.0.0.1"
DRONE_IP = "10.0.20.15"
DRONE_PORT = 14550   # MAVProxy udpin port (--out=udpin:0.0.0.0:14552)
MY_IP = "0.0.0.0"
MY_PORT = 0          # ephemeral port, MAVProxy replies back to us

# 1000 = Source 1 (GPS)
# 1500 = Source 2 (Non-GPS)
# 2000 = Source 3
PWM_CH6 = 2000
PWM_CH7 = 1500
INTERVAL = 0.02  # 20 ms


def mavlink_crc(data: bytes, crc_extra: int) -> int:
    crc = 0xFFFF
    for b in data:
        tmp = b ^ (crc & 0xFF)
        tmp ^= (tmp << 4) & 0xFF
        crc = ((crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)) & 0xFFFF

    tmp = crc_extra ^ (crc & 0xFF)
    tmp ^= (tmp << 4) & 0xFF
    crc = ((crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)) & 0xFFFF
    return crc


def build_rc_override_packet(seq: int, pwm_ch7: int) -> bytes:
    # MAVLink v2: uint16 fields before uint8 (field reordering)
    payload = struct.pack("<8H", 0, 0, 0, 0, 0, PWM_CH6, PWM_CH7, 0) + struct.pack("<BB", 1, 1)
    header = struct.pack("BBBBBBBBBB", 0xFD, len(payload), 0, 0, seq & 0xFF, 255, 0, 70, 0, 0)
    crc = mavlink_crc(header[1:] + payload, 124)
    return header + payload + struct.pack("<H", crc)


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((MY_IP, MY_PORT))
    sock.setblocking(False)

    seq = 0
    rx_count = 0

    print(f"RC Override CH7={PWM_CH7} -> {DRONE_IP}:{DRONE_PORT}")
    sample = build_rc_override_packet(0, PWM_CH7)
    print(f"[PKT] {sample.hex(' ').upper()}")
    print(f"      len={len(sample)}  msgid=70  sysid=255  compid=0  target_sys=1  target_comp=1")

    try:
        while True:
            readable, _, _ = select.select([sock], [], [], 0)
            for ready_sock in readable:
                try:
                    data, addr = ready_sock.recvfrom(65535)
                    rx_count += 1
                    print(f"[RX] #{rx_count} from {addr[0]}:{addr[1]} bytes={len(data)}")
                except OSError:
                    pass  # Windows ICMP port-unreachable (10054), MAVProxy not ready yet

            packet = build_rc_override_packet(seq, PWM_CH7)
            try:
                sock.sendto(packet, (DRONE_IP, DRONE_PORT))
            except OSError:
                pass  # Windows ICMP port-unreachable, skip and retry
            seq += 1

            if seq % 50 == 0:
                print(f"  tx_sent={seq}  rx={rx_count}  CH7={PWM_CH7}")

            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        sock.close()


if __name__ == "__main__":
    try:
        main()
    except OSError as exc:
        print(f"Socket error: {exc}", file=sys.stderr)
        sys.exit(1)
