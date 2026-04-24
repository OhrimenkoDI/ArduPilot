import sys
import time

from pymavlink import mavutil

MAVPROXY_IP = "10.0.20.15"
MAVPROXY_PORT = 14550  # MAVProxy: --out=udpin:0.0.0.0:14552

# CH7 values for GPS source selection (RC7_OPTION=90 in ArduPilot)
# 1000 = Source 1 (primary GPS)
# 1500 = Source 2
# 2000 = Source 3
PWM_CH6 = 2000
PWM_CH7 = 1500

INTERVAL = 0.02  # 50 Hz — keeps override active (RC_OVERRIDE_TIME = 3 sec default)


def send_ch7(conn, pwm6: int, pwm7: int) -> None:
    conn.mav.rc_channels_override_send(
        1, 1,              # target_system, target_component
        0, 0, 0, 0, 0,   # CH1-CH5: 0 = do not override
        pwm6,              # CH6
        pwm7,              # CH7
        0,                 # CH8
    )


def main() -> None:
    conn = mavutil.mavlink_connection(
        f"udpout:{MAVPROXY_IP}:{MAVPROXY_PORT}",
        force_connected=True,
    )

    print(f"Sending RC_OVERRIDE CH7={PWM_CH7} -> {MAVPROXY_IP}:{MAVPROXY_PORT}")
    print("Ctrl+C to stop and release channel")

    sent = 0
    try:
        while True:
            send_ch7(conn, PWM_CH6, PWM_CH7)
            sent += 1
            if sent % 50 == 0:
                print(f"  sent={sent}  CH6={PWM_CH6}  CH7={PWM_CH7}")
            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print("\nReleasing CH7 override...")
        # Send CH7=0 several times so FC gets the release before timeout
        for _ in range(5):
            send_ch7(conn, 0, 0)
            time.sleep(INTERVAL)

    finally:
        conn.close()
        print("Closed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
