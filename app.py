import threading
from flask import Flask, render_template, jsonify, request, flash
import subprocess
import pickle
import numpy as np
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from firedata import launch_gui_not_a_fire

app = Flask(__name__, template_folder='./', static_url_path='/', static_folder='/')
app.secret_key = '%$6£&^&^HDIO76%^%£"^7'

model = pickle.load(open('./models/model.pkl', 'rb'))
scaler = pickle.load(open('./models/scaler.pkl', 'rb'))
label_encoder = pickle.load(open('./models/label_encoder.pkl', 'rb'))

last_run_time = 0
last_lon = None


prediction_file = "prediction_result.txt"
prediction_event = threading.Event()
prediction_lock = threading.Lock()

class FileWatcher(threading.Thread):
    def __init__(self):
        super(FileWatcher, self).__init__()
        self.event_handler = None

    def run(self):
        observer = Observer()
        self.event_handler = CustomFileSystemEventHandler()
        observer.schedule(self.event_handler, path='./out', recursive=False)
        observer.start()
        observer.join()

class CustomFileSystemEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        global last_run_time
        current_time = time.time()
        if event.src_path == './out/weather_info.txt' and (current_time - last_run_time > 1):
            print("File changed, triggering prediction.")
            last_run_time = current_time
            threading.Thread(target=self.handle_prediction, args=(event.src_path,)).start()

    def handle_prediction(self, file_path):
        global last_lon
        result, probability, lon, lat = perform_prediction(file_path)

        if result and (result.lower() == 'fire' or probability < 0.75):
            app.logger.info(f"Prediction and Confidence: {result}, {probability:.2%}")
            app.logger.info(f"Location of ignition - Longitude: {lon}, Latitude: {lat}")
            info = "Lower layer Drone advancing towards fire to capture image"
            time.sleep(1)
            launch_gui_not_a_fire(info)
            run_tkinter_app()
            time.sleep(8)
            with open(prediction_file, 'r') as file:
                resnet_prediction = file.read().strip()

            if resnet_prediction == 'fire':
                print('HERE')
                run_fire_script()


        last_lon = lon

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
        env = os.environ.copy()
        env['ELMFIRE_SCRATCH_BASE'] = '/home/jack/scratch'
        env['ELMFIRE_BASE_DIR'] = '/home/jack/elmfire'
        env['ELMFIRE_INSTALL_DIR'] = f"{env['ELMFIRE_BASE_DIR']}/build/linux/bin"
        env['CLOUDFIRE_SERVER'] = '172.92.17.198'
        env['PATH'] = env['PATH'] + f":{env['ELMFIRE_INSTALL_DIR']}:{env['ELMFIRE_BASE_DIR']}/cloudfire"
        env['CLOUDFIRE_BASE_DIR'] = '/home/jack/elmfire'

        subprocess.run(['python3', 'firedata.py'], check=True, env=env)
        app.logger.info("Fire prediction script executed successfully.")
    except subprocess.CalledProcessError as e:
        app.logger.error(f"Failed to execute the fire prediction script: {str(e)}")



def run_tkinter_app():
    subprocess.Popen(['python3', 'run_tkinter_app.py'])

@app.route('/run_script', methods=['POST'])
def run_script():
    if 'submit_button' in request.form:
        script_path = None
        if request.form['submit_button'] == 'Run Drone Clustering':
            script_path = './cluster.py'
        elif request.form['submit_button'] == 'Fire History':
            script_path = './firetable.py'
        elif request.form['submit_button'] == 'Generate Data':
            script_path = './generate.py'
        elif request.form['submit_button'] == 'Practice Tool Arena':
            script_path = './suppression.py'

        if script_path:
            try:
                subprocess.run(['python3', script_path], check=True)
                flash(f"{script_path} executed successfully.", 'success')
            except subprocess.CalledProcessError as e:
                flash(f"Failed to execute the script: {str(e)}", 'error')
        else:
            flash("No valid script selected", 'error')

    return render_template('webpage.html', image='./out/simfire/out.gif')

@app.route('/trigger_prediction')
def trigger_prediction():
    predicted_class, probability, center_lon, center_lat = perform_prediction('out/weather_info.txt')
    if predicted_class is None:
        return jsonify({'error': 'Prediction failed'}), 500
    return jsonify({
        'prediction': predicted_class,
        'probability': probability,
        'lon': center_lon,
        'lat': center_lat
    })

@app.route('/')
def index():
    return render_template('webpage.html', image='./out/simfire/out.gif')

if __name__ == '__main__':
    watcher_thread = FileWatcher()
    watcher_thread.daemon = True
    watcher_thread.start()

    app.run(debug=True, use_reloader=False)