# simulateur_rpe_rpr.py (Simule les RPi écouteurs et le RPi récepteur)
import paho.mqtt.client as mqtt
import json
import time
import os
import sys

# --- Configuration ---
FIFO_PATH = "sae24_signal_pipe"
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "SAE24/E103/amplitudes"

# --- Configuration de la "numérisation" (ADC/FSK) ---
# Slide 15: "Déterminer nombre de bits nécessaire"
# On choisit 10 bits, ce qui donne des valeurs de 0 à 1023.
NUM_BITS = 10
# On doit définir une amplitude maximale pour faire la conversion.
# On estime que l'amplitude ne dépassera jamais 2000.
MAX_AMPLITUDE = 2000.0 

def amplitude_to_bits(amplitude):
    """Simule la conversion CAN + préparation FSK."""
    # 1. Borner l'amplitude pour qu'elle soit entre 0 et MAX_AMPLITUDE
    amplitude = max(0, min(amplitude, MAX_AMPLITUDE))
    
    # 2. Convertir en une valeur entière sur la plage 0-1023
    # C'est la simulation du Convertisseur Analogique-Numérique
    value_on_10_bits = int((amplitude / MAX_AMPLITUDE) * (2**NUM_BITS - 1))
    
    # 3. Formater en une chaîne de bits de longueur fixe (10 ici)
    # C'est la donnée qui serait envoyée via FSK
    # ex: format(5, '010b') -> '0000000101'
    return format(value_on_10_bits, f'0{NUM_BITS}b')

def main():
    # Connexion au broker MQTT
    client = mqtt.Client(client_id="simulateur_rpr")
    try:
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        client.loop_start()
        print("Simulateur RPr connecté au broker MQTT.")
    except Exception as e:
        print(f"Erreur connexion MQTT: {e}"); sys.exit(1)

    print("Simulateur RPe prêt. En attente de signaux sonores...")
    try:
        with open(FIFO_PATH, 'rb') as fifo:
            print("Émetteur détecté. Démarrage de la capture...")
            while True:
                line = fifo.readline()
                if not line: break
                
                # 1. Lire les 3 amplitudes depuis le "milieu de propagation"
                parts = line.decode('utf-8').strip().split(':')
                amplitudes = [float(p) for p in parts]
                print(f"\nAmplitudes reçues: {amplitudes[0]:.2f}, {amplitudes[1]:.2f}, {amplitudes[2]:.2f}")

                # 2. Pour chaque micro (RPe), simuler la conversion et publier
                for i in range(3):
                    mic_id = i + 1
                    amplitude_val = amplitudes[i]
                    
                    # 3. Logique RPe: Convertir l'amplitude en bits (FSK)
                    amplitude_bits = amplitude_to_bits(amplitude_val)
                    
                    # 4. Logique RPr: Publier sur MQTT
                    payload = {"mic_id": mic_id, "amplitude_bits": amplitude_bits}
                    client.publish(MQTT_TOPIC, json.dumps(payload))
                    print(f"  -> RPe{mic_id}: Amp -> Bits: {amplitude_bits}. Publié sur MQTT.")
    
    except KeyboardInterrupt: print("\nArrêt manuel du simulateur RPe/RPr.")
    finally:
        client.loop_stop(); client.disconnect()
        print("Simulateur RPe/RPr arrêté.")
        sys.exit(0)

if __name__ == "__main__":
    main()
