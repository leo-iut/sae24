# processeur_mqtt.py (Version finale avec magnétisme à la grille)
import paho.mqtt.client as mqtt
import json
import math
import time
import mysql.connector
from datetime import datetime
import sys

# --- Configurations (inchangées) ---
DB_CONFIG = {'unix_socket': '/opt/lampp/var/mysql/mysql.sock', 'user': 'sae24', 'password': 'leo', 'database': 'sae24'}
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC_TO_SUBSCRIBE = "SAE24/E103/amplitudes"
MICROS = { 1: {"pos": (0.25, 0.25)}, 2: {"pos": (0.25, 7.75)}, 3: {"pos": (7.75, 7.75)} }
K_FACTOR = 1000.0
GRID_SIZE = 16
CASE_SIZE_M = 0.5
NUM_BITS = 10
MAX_AMPLITUDE = 5000.0 # Augmenté pour être plus réaliste

def bits_to_amplitude(bits_string):
    value_on_10_bits = int(bits_string, 2)
    return (value_on_10_bits / (2**NUM_BITS - 1)) * MAX_AMPLITUDE

# --- Fonctions de traitement ---
amplitude_map = {}
def precompute_amplitude_map():
    print("Pré-calcul de la carte des amplitudes...")
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            case_x = i * CASE_SIZE_M + (CASE_SIZE_M / 2)
            case_y = j * CASE_SIZE_M + (CASE_SIZE_M / 2)
            amplitudes_for_case = []
            for mic_id in sorted(MICROS.keys()):
                mic_pos = MICROS[mic_id]["pos"]
                dist = math.sqrt((case_x - mic_pos[0])**2 + (case_y - mic_pos[1])**2)
                amp = K_FACTOR / (dist**2) if dist > 0.1 else K_FACTOR / (0.1**2)
                amplitudes_for_case.append(amp)
            amplitude_map[(case_x, case_y)] = amplitudes_for_case
    print(f"Carte pré-calculée avec {len(amplitude_map)} points.")

def find_closest_position(received_amplitudes):
    amps = [received_amplitudes.get(1,0), received_amplitudes.get(2,0), received_amplitudes.get(3,0)]
    best_match_pos, min_error = None, float('inf')
    for pos, map_amplitudes in amplitude_map.items():
        error = sum([(map_amp - rec_amp)**2 for map_amp, rec_amp in zip(map_amplitudes, amps)])
        if error < min_error:
            min_error, best_match_pos = error, pos
    return best_match_pos

# --- NOUVELLE FONCTION CRUCIALE ---
def snap_to_grid(position):
    """Arrondit une position (x, y) au centre de la case la plus proche."""
    if not position:
        return None
    
    # 1. Trouver l'indice de la case la plus proche
    # Ex: x=4.3 -> i = 4.3 / 0.5 = 8.6 -> round(8.6) = 9
    i = round(position[0] / CASE_SIZE_M - 0.5)
    j = round(position[1] / CASE_SIZE_M - 0.5)

    # 2. Recalculer les coordonnées du centre de cette case
    snapped_x = i * CASE_SIZE_M + (CASE_SIZE_M / 2)
    snapped_y = j * CASE_SIZE_M + (CASE_SIZE_M / 2)

    return (snapped_x, snapped_y)

def save_position_to_db(position, db_connection): # ... (inchangée)
    # ... code de la fonction ...
    if not position: return
    cursor = db_connection.cursor()
    sql_query = "INSERT INTO positions (pos_x, pos_y, timestamp) VALUES (%s, %s, %s)"
    try:
        cursor.execute(sql_query, (position[0], position[1], datetime.now()))
        db_connection.commit()
        print(f"  -> Position ({position[0]:.2f}, {position[1]:.2f}) enregistrée en BDD.")
    except mysql.connector.Error as err:
        print(f"Erreur d'insertion en BDD : {err}")
    finally:
        cursor.close()

# --- Callbacks MQTT (MODIFIÉ) ---
received_data_buffer = {}
def on_connect(client, userdata, flags, rc): # ... (inchangée)
    if rc == 0: client.subscribe(MQTT_TOPIC_TO_SUBSCRIBE)
    else: print(f"Échec connexion MQTT, code: {rc}")

def on_message(client, userdata, msg):
    db_connection = userdata['db_connection']
    try:
        data = json.loads(msg.payload.decode())
        amplitude = bits_to_amplitude(data["amplitude_bits"])
        batch_key = int(time.time()) # On groupe par seconde entière
        if batch_key not in received_data_buffer: received_data_buffer[batch_key] = {}
        received_data_buffer[batch_key][data["mic_id"]] = amplitude
        
        if len(received_data_buffer[batch_key]) == 3:
            print(f"\n--- Batch de 3 msg MQTT reçu ---")
            
            # Étape 1 : Estimation brute
            estimated_pos = find_closest_position(received_data_buffer[batch_key])
            print(f"  Position brute estimée : {estimated_pos}")
            
            # Étape 2 : Magnétisme à la grille (la correction !)
            snapped_pos = snap_to_grid(estimated_pos)
            print(f"==> Position alignée sur la grille : {snapped_pos}")
            
            # Étape 3 : Sauvegarde de la position corrigée
            save_position_to_db(snapped_pos, db_connection)
            
            del received_data_buffer[batch_key]
    except Exception as e:
        print(f"Erreur traitement message: {e}")

def main(): # ... (inchangée)
    # ... code de la fonction ...
    precompute_amplitude_map()
    try:
        db_connection = mysql.connector.connect(**DB_CONFIG)
        print("Connecté à la BDD MySQL.")
    except mysql.connector.Error as err:
        print(f"ERREUR connexion BDD : {err}"); sys.exit(1)
    client = mqtt.Client(client_id="processeur_mqtt_sae24")
    client.user_data_set({'db_connection': db_connection}) 
    client.on_connect = on_connect; client.on_message = on_message
    try:
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"ERREUR connexion broker : {e}")
    finally:
        db_connection.close(); print("\nConnexion BDD fermée."); sys.exit(0)

if __name__ == "__main__":
    main()
