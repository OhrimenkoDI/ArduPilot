import socket
import sys
import time
from collections import Counter

try:
    from pymavlink import mavutil
except ImportError:
    mavutil = None


LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 14551
BUFFER_SIZE = 65535
PRINT_EVERY_SEC = 2.0


def build_parser():
    if mavutil is None:
        return None
    mav = mavutil.mavlink.MAVLink(None)
    mav.robust_parsing = True
    return mav


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_IP, LISTEN_PORT))
    sock.settimeout(0.5)

    parser = build_parser()
    started_at = time.time()
    last_report = started_at
    packet_count = 0
    byte_count = 0
    message_count = 0
    by_sender = Counter()
    by_type = Counter()

    print(f"Listening UDP on {LISTEN_IP}:{LISTEN_PORT}")
    if parser is None:
        print("pymavlink not found, showing UDP packets only")
    else:
        print("MAVLink decode enabled")
    print("Press Ctrl+C to stop")

    try:
        while True:
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                data = None

            now = time.time()
            if data is not None:
                packet_count += 1
                byte_count += len(data)
                by_sender[f"{addr[0]}:{addr[1]}"] += 1

                print(
                    f"[UDP] from {addr[0]}:{addr[1]} bytes={len(data)} "
                    f"head={data[:8].hex(' ')}"
                )

                if parser is not None:
                    for byte in data:
                        msg = parser.parse_char(bytes([byte]))
                        if msg is None:
                            continue
                        msg_type = msg.get_type()
                        message_count += 1
                        by_type[msg_type] += 1

                        if msg_type == "HEARTBEAT":
                            print(
                                "[MAV] HEARTBEAT "
                                f"sys={msg.get_srcSystem()} comp={msg.get_srcComponent()} "
                                f"base_mode={getattr(msg, 'base_mode', None)} "
                                f"custom_mode={getattr(msg, 'custom_mode', None)}"
                            )

            if now - last_report >= PRINT_EVERY_SEC:
                elapsed = max(now - started_at, 0.001)
                top_senders = ", ".join(
                    f"{name} x{count}" for name, count in by_sender.most_common(3)
                ) or "-"
                top_types = ", ".join(
                    f"{name} x{count}" for name, count in by_type.most_common(5)
                ) or "-"
                print(
                    f"[STAT] {elapsed:.1f}s packets={packet_count} bytes={byte_count} "
                    f"msgs={message_count} rate={packet_count / elapsed:.1f} pkt/s"
                )
                print(f"[STAT] senders: {top_senders}")
                print(f"[STAT] mav types: {top_types}")
                last_report = now

    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        sock.close()


if __name__ == "__main__":
    try:
        main()
    except OSError as exc:
        print(f"Socket error: {exc}", file=sys.stderr)
        sys.exit(1)
