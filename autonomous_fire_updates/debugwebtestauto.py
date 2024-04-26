from flask import Flask, render_template, jsonify
import subprocess
import pickle
import numpy as np
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time
import sys

app = Flask(__name__)
app.secret_key = 'jack'


model = pickle.load(open('/home/jack/model.pkl', 'rb'))
scaler = pickle.load(open('/home/jack/scaler.pkl', 'rb'))
label_encoder = pickle.load(open('/home/jack/label_encoder.pkl', 'rb'))

last_run_time = 0  

class FileWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        global last_run_time
        current_time = time.time()
        if event.src_path == '/home/jack/weather_info.txt' and (current_time - last_run_time > 1):  
            print("File changed, triggering prediction.")
            last_run_time = current_time
            self.handle_prediction(event.src_path)

    def handle_prediction(self, file_path):
        result, probability, lon, lat = perform_prediction(file_path)
        if result and result.lower() == 'fire':
            run_fire_script()
            app.logger.info(f"Prediction and Confidence: {result}, {probability:.2%}")
            app.logger.info(f"Location of ignition - Longitude: {lon}, Latitude: {lat}")
  


def perform_prediction(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        data = lines[0].strip().split('\t')
        
        center_info = lines[1].strip()
        center_lon = center_info.split('--center_lon=')[1].split()[0]
        center_lat = center_info.split('--center_lat=')[1].split('\\')[0]

        ndvi, lst, burned_area = map(float, data)
        input_data = np.array([[ndvi, lst, burned_area]])
        input_scaled = scaler.transform(input_data)
        prediction = model.predict(input_scaled)
        predicted_class = label_encoder.inverse_transform(prediction)[0]
        probability = model.predict_proba(input_scaled)[0][prediction[0]]
        return predicted_class, probability, center_lon, center_lat
    except Exception as e:
        app.logger.error(f"Error during prediction: {e}")
        return None, None, None, None


def run_fire_script():
    try:
        subprocess.run(['python3', '/home/jack/elmfire/tutorials/Custom/Automated_drone/autofiremap.py'], check=True)
        app.logger.info("Fire prediction script executed successfully.")
        sys.exit()
    except subprocess.CalledProcessError as e:
        app.logger.error(f"Failed to execute the fire prediction script: {str(e)}")

@app.route('/')
def index():
    return render_template('new.html')

@app.route('/trigger_prediction')
def trigger_prediction():
    predicted_class, probability, center_lon, center_lat = perform_prediction('/home/jack/weather_info.txt')
    if predicted_class is None:
        
        return jsonify({'error': 'Prediction failed'}), 500
    return jsonify({
        'prediction': predicted_class,
        'probability': probability,
        'lon': center_lon,
        'lat': center_lat
    })

def start_watching():
    event_handler = FileWatcher()
    observer = Observer()
    observer.schedule(event_handler, path='/home/jack/', recursive=False)
    observer.start()
    observer.join()

if __name__ == '__main__':

    watcher_thread = threading.Thread(target=start_watching, daemon=True)
    watcher_thread.start()

    app.run(debug=True, use_reloader=False)
