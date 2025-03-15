import sqlite3
import paho.mqtt.client as mqtt
from datetime import datetime
import os

BROKER = "10.108.33.121"
TOPIC_ENTRY = "parking/entry"
TOPIC_EXIT = "parking/exit"
DB_FILE = 'parking_db.sqlite'

# Function to create the database and tables
def create_database():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print("An old database removed.")
    
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS aktualne_wjazdy (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfid_id TEXT NOT NULL,
        data_wjazdu DATETIME NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS archiwum (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfid_id TEXT NOT NULL,
        data_wjazdu DATETIME NOT NULL,
        data_wyjazdu DATETIME NOT NULL
    );
    """)

    connection.commit()
    connection.close()
    print("The database and tables are ready.")

# Function to check if the RFID ID exists in the aktualne_wjazdy table
def check_if_rfid_exists(rfid_id):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM aktualne_wjazdy WHERE rfid_id = ?", (rfid_id,))
    row = cursor.fetchone()
    
    connection.close()
    
    if row:
        return True  # RFID exists
    return False  # RFID does not exist

# Function to process the entry
def process_entry(rfid_id, entry_time):
    # First, check if the RFID ID already exists
    if check_if_rfid_exists(rfid_id):
        return f"RFID ID {rfid_id} already exists in the database. Entry not registered."
    
    # If not, insert the entry
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO aktualne_wjazdy (rfid_id, data_wjazdu) VALUES (?, ?)", (rfid_id, entry_time))
    connection.commit()
    connection.close()
    return f"Entry registered for RFID: {rfid_id} at {entry_time}"

# Function to process the exit
def process_exit(rfid_id, exit_time):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    cursor.execute("SELECT data_wjazdu FROM aktualne_wjazdy WHERE rfid_id = ?", (rfid_id,))
    row = cursor.fetchone()
    if row:
        entry_time = row[0]
        cursor.execute("INSERT INTO archiwum (rfid_id, data_wjazdu, data_wyjazdu) VALUES (?, ?, ?)",
                       (rfid_id, entry_time, exit_time))
        cursor.execute("DELETE FROM aktualne_wjazdy WHERE rfid_id = ?", (rfid_id,))
        connection.commit()
        return f"Exit processed for RFID: {rfid_id} at {exit_time}"
    connection.close()
    return f"RFID ID {rfid_id} not found in the current entries. Exit not processed."

# MQTT message handler
def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    if msg.topic == TOPIC_ENTRY:
        rfid_id, entry_time = payload.split(",")
        result_message = process_entry(rfid_id, entry_time)
        client.publish("parking/response", result_message)  # Send a response back to the client
    elif msg.topic == TOPIC_EXIT:
        rfid_id, exit_time = payload.split(",")
        result_message = process_exit(rfid_id, exit_time)
        client.publish("parking/response", result_message)  # Send a response back to the client

# MQTT connection handler
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker.")
    client.subscribe([(TOPIC_ENTRY, 0), (TOPIC_EXIT, 0)])

# Setting up MQTT client
client = mqtt.Client(client_id=None, clean_session=True)
client.on_connect = on_connect
client.on_message = on_message

if __name__ == "__main__":
    create_database()
    client.connect(BROKER)
    client.loop_forever()
