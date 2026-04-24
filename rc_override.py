# меняем источник позиционирования EKF на дроне (GPS/Non-GPS) 
# через MAVLink RC Override

import socket
import struct

# ── настройки ──────────────────────────────────────────
DRONE_IP   = "127.0.0.1"   # ← MAVProxy на локалхосте (было 10.0.20.15)
DRONE_PORT = 14551           # ← порт udpin MAVProxy 
MY_IP      = "10.0.20.177"  # ваш ПК (для bind)

# PWM для RC7 (option=90, EKF Pos Source):
#   1000 = Source 1 (GPS)
#   1500 = Source 2 (Non-GPS)
#   2000 = Source 3
PWM_CH7 = 1500   # ← меняйте на 1000 или 2000
# ───────────────────────────────────────────────────────

def pack_rc_override(pwm_ch7: int) -> bytes:
    """
    MAVLink v1, message ID=70 RC_CHANNELS_OVERRIDE
    8 каналов, остальные = 0 (игнорируются ArduPilot)
    """
    # Заголовок MAVLink v1
    # STX, LEN, SEQ, SYS_ID, COMP_ID, MSG_ID
    payload = struct.pack('<8H',
        0,        # ch1  — не трогаем
        0,        # ch2
        0,        # ch3
        0,        # ch4
        0,        # ch5
        0,        # ch6
        pwm_ch7,  # ch7  ← EKF Pos Source
        0,        # ch8
    )
    # target_system=1, target_component=1 (2 байта перед каналами)
    payload = struct.pack('<BB', 1, 1) + payload

    stx     = 0xFE
    length  = len(payload)   # 18
    seq     = 0
    sys_id  = 255            # GCS
    comp_id = 0
    msg_id  = 70             # RC_CHANNELS_OVERRIDE

    header = struct.pack('BBBBBB', stx, length, seq, sys_id, comp_id, msg_id)
    packet = header + payload

    # CRC (MAVLink CRC-16/MCRF4XX + CRC_EXTRA)
    CRC_EXTRA_RC_OVERRIDE = 124
    crc = mavlink_crc(packet[1:], CRC_EXTRA_RC_OVERRIDE)
    return packet + struct.pack('<H', crc)


def mavlink_crc(data: bytes, crc_extra: int) -> int:
    crc = 0xFFFF
    for b in data:
        tmp = b ^ (crc & 0xFF)
        tmp ^= (tmp << 4) & 0xFF
        crc = ((crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)) & 0xFFFF
    # добавляем CRC_EXTRA
    tmp = crc_extra ^ (crc & 0xFF)
    tmp ^= (tmp << 4) & 0xFF
    crc = ((crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)) & 0xFFFF
    return crc


# ── отправка ───────────────────────────────────────────
# RC Override нужно слать непрерывно — ArduPilot сбрасывает его через ~100–500 мс тишины.
# Ctrl+C для остановки (дрон вернётся к пульту).
import time
import sys

INTERVAL = 0.05  # 50 мс → 20 пакетов/сек

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
seq  = 0
print(f"RC Override CH7={PWM_CH7} → {DRONE_IP}:{DRONE_PORT}  (Ctrl+C для остановки)")
try:
    while True:
        # пересобираем пакет с инкрементным seq
        payload = struct.pack('<BB', 1, 1) + struct.pack('<8H', 0, 0, 0, 0, 0, 0, PWM_CH7, 0)
        header  = struct.pack('BBBBBB', 0xFE, len(payload), seq & 0xFF, 255, 0, 70)
        raw     = header + payload
        crc     = mavlink_crc(raw[1:], 124)
        packet  = raw + struct.pack('<H', crc)
        sock.sendto(packet, (DRONE_IP, DRONE_PORT))
        seq += 1
        if seq % 20 == 0:
            print(f"  seq={seq}  CH7={PWM_CH7}", end='\r')
        time.sleep(INTERVAL)
except KeyboardInterrupt:
    print("\nОстановлено.")
finally:
    sock.close()
