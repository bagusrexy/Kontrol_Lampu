import cv2
import time
import numpy as np
import HandTrackingModule as htm
import random
from paho.mqtt import client as mqtt_client

#setting MQTT
import mqtt_out

broker = 'broker.emqx.io'
port = 1883
topic = "skripsimuro1/ruangan/v1"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 1000)}'
username = 'emqx'
password = 'public'

################################
wCam, hCam = 640, 480
################################

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0

detector = htm.handDetector(detectionCon=0.7, maxHands=1)

vol = 0
volBar = 400
volPer = 0
area = 0
colorVol = (255, 0, 0)

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

def mqttout(client, volPer):
    time.sleep(10)
    msg = int(volPer)
    result = client.publish(topic, msg)
    # result: [0, 1]
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")

def run():
    client = connect_mqtt()
    client.loop_start()
    mqttout(client, volPer)

while True:
    success, img = cap.read()
    # Find Hand
    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img, draw=True)
    if len(lmList) != 0:

        # Filter based on size
        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) // 100
        # print(area)
        if 250 < area < 1000:

            # Find Distance between index and Thumb
            length, img, lineInfo = detector.findDistance(4, 8, img)
            # print(length)

            # Convert Volume
            volBar = np.interp(length, [50, 200], [400, 150])
            volPer = np.interp(length, [50, 200], [0, 100])

            # Reduce Resolution to make it smoother
            smoothness = 10
            volPer = smoothness * round(volPer / smoothness)

            # Check fingers up
            fingers = detector.fingersUp()
            # print(fingers)

            # If pinky is down set volume
            if not fingers[4]:
                #volume.SetMasterVolumeLevelScalar(volPer / 100, None)
                cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                colorVol = (0, 255, 0)
                mqttout(client, volPer)
            else:
                colorVol = (255, 0, 0)

    # Drawings
    cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
    cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)
    cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,
                1, (255, 0, 0), 3)
    cv2.putText(img, f'Lamp: {int(volPer)} %', (400, 50), cv2.FONT_HERSHEY_COMPLEX,
                1, colorVol, 3)

    # Frame rate
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX,
                1, (255, 0, 0), 3)

    cv2.imshow("Img", img)
    cv2.waitKey(1)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

if __name__ == '__main__':
    run()