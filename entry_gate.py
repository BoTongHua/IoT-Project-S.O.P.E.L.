import time
from datetime import datetime
import paho.mqtt.client as mqtt
from mfrc522 import MFRC522
import RPi.GPIO as GPIO

BROKER = "10.108.33.121"
TOPIC_ENTRY = "parking/entry"
TOPIC_RESPONSE = "parking/response"

# GPIO and RFID setup
GPIO.setmode(GPIO.BOARD)
reader = MFRC522()

# Function to read RFID
def read_rfid():
    while True:
        (status, _) = reader.MFRC522_Request(reader.PICC_REQIDL)
        if status == reader.MI_OK:
            (status, uid) = reader.MFRC522_Anticoll()
            if status == reader.MI_OK:
                card_id = "".join([str(x) for x in uid])
                return card_id

# Function to handle entry
def handle_entry(client, card_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client.publish(TOPIC_ENTRY, f"{card_id},{now}")
    print(f"Entry request sent for card: {card_id}")

# MQTT connection handler
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker.")
    client.subscribe(TOPIC_RESPONSE)  # Subscribe to the response topic

# MQTT message handler
def on_message(client, userdata, msg):
    if msg.topic == TOPIC_RESPONSE:
        response = msg.payload.decode()
        print(f"Server response: {response}")  # Print the server's response

# Setting up MQTT client
client = mqtt.Client(client_id=None, clean_session=True)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER)

if __name__ == "__main__":
    client.loop_start()
    try:
        while True:
            card_id = read_rfid()
            handle_entry(client, card_id)
            time.sleep(5)  # Wait before the next RFID scan
    except KeyboardInterrupt:
        GPIO.cleanup()
        client.loop_stop()
