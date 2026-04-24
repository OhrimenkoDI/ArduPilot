# меняем источник EKF через pymavlink → MAVProxy → дрон
from pymavlink import mavutil
import time

# PWM для RC7 (RC7_OPTION=90):
#   1000 = Source 1 (GPS)
#   1500 = Source 2 (Non-GPS)  
#   2000 = Source 3
PWM_CH7 = 1000

# подключаемся к MAVProxy (он слушает udpin:14553)
mav = mavutil.mavlink_connection('udpout:127.0.0.1:14553')
mav.wait_heartbeat(timeout=5)
print(f"Heartbeat получен: sys={mav.target_system} comp={mav.target_component}")

# RC Override канал 7, остальные = 0 (игнорируются)
mav.mav.rc_channels_override_send(
    mav.target_system,
    mav.target_component,
    0, 0, 0, 0, 0, 0,  # ch1-6
    PWM_CH7,            # ch7 ← EKF Pos Source
    0                   # ch8
)
print(f"RC Override CH7={PWM_CH7} отправлен")
time.sleep(0.5)