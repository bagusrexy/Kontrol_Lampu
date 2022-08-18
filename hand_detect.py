import cv2
import numpy as np
import HandTrackingModule as htm
import math
import time
import random
from paho.mqtt import client as mqtt_client

#variabel setting koneksi mqtt dengan broker
broker = 'broker.emqx.io'
port = 1883
topic = "skripsimuro1/ruangan/v1"
#client ID dengan pub prefix secara random
client_id = f'python-mqtt-{random.randint(0,1000)}'
username = 'emqx'
password = 'public'

# Function koneksi status mqtt
def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def publish(client):
    while True:
        time.sleep(1)
        msg = int(volPer)
        result = client.publish(topic, msg)
        status = result[0]
        if status == 0:
            print(f"Send `{msg}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")

################################
wCam, hCam = 640, 480
################################

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0

detector = htm.HandDetector(detectionCon=0.7)

#devices = AudioUtilities.GetSpeakers()
#nterface = devices.Activate(
    #IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
#volume = cast(interface, POINTER(IAudioEndpointVolume))
# volume.GetMute()
# volume.GetMasterVolumeLevel()
#volRange = volume.GetVolumeRange()
minVol = [0]
maxVol = [1]
vol = 0
volBar = 400
volPer = 0
def deteksi():
    while True:
        success, img = cap.read()
        img = detector.findHands(img)
        lmList = detector.findPosition(img, draw=False)
        if len(lmList) != 0:
        # print(lmList[4], lmList[8])

            x1, y1 = lmList[4][1], lmList[4][2]
            x2, y2 = lmList[8][1], lmList[8][2]
            x3, y3 = lmList[12][1], lmList[12][2]
            cx, cy, cz = (x1 + x2) // 2, (y1 + y2) // 2

            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)

            length = math.hypot(x2 - x1, y2 - y1)
            # print(length)

        # Hand range 50 - 300
        # Volume Range -65 - 0

            vol = np.interp(length, [50, 300], [0, 0])
            volBar = np.interp(length, [50, 300], [400, 150])
            volPer = np.interp(length, [50, 300], [0, 100])
        #print(int(length), vol)
        #volume.SetMasterVolumeLevel(vol, None)

            if length < 50:
                cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)

        cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
        cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)
        cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,
                1, (255, 0, 0), 3)
        print(int(volPer))

        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX,
                1, (255, 0, 0), 3)


        cv2.imshow("Img", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def run():
    client = connect_mqtt()
    deteksi()
    client.loop_start()
    publish(client)

if __name__ == '__main__':
    run()
