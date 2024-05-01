import os
import subprocess
import csv
import rasterio
from matplotlib import pyplot as plt
import glob
import numpy as np
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import csv

csv_file_path = './models/03-real-fuels/outputs/fire_size_stats.csv'
def log_fire_data(csv_path, fire_data):
    """
    Log fire data to a CSV file. If the file doesn't exist, create it and add headers.
    """
    fieldnames = ['Date', 'Longitude', 'Latitude', 'Fire Volume (ac-ft)', 'Total Fire Area (ac)', 'Average Spread Rate (unit)', 'Priority']
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()  
        writer.writerow(fire_data)


def update_fire_stats(lon, lat, volume, area, spread_rate, priority):
    """
    Prepare fire data and log it.
    """
    fire_data = {
        'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Longitude': lon,
        'Latitude': lat,
        'Fire Volume (ac-ft)': volume,
        'Total Fire Area (ac)': area,
        'Average Spread Rate (unit)': spread_rate,
        'Priority': priority
    }
    csv_file_path = './out/fire_log'
    log_fire_data(csv_file_path, fire_data)

def read_csv(file_path):
    data = []
    try:
        with open(file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                extracted_data = {
                    'Fire Volume (ac-ft)': row.get('Fire volume (ac-ft)', 'N/A'),
                    'Total Fire Area (ac)': row.get('Total fire area (ac)', 'N/A'),
                    'Average Spread Rate': row.get('Average Spread Rate (unit)', 'N/A'),
                    'Priority of Fire': row.get('Priority', 'N/A')
                }
                data.append(extracted_data)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read CSV file: {str(e)}")
    return data

def populate_tree(tree, data):
    for item in data:
        values = list(item.values())
        tree.insert('', 'end', values=values)

def create_gui(data):
    root = tk.Tk()
    root.title("Fire Data Viewer")

  
    tree = ttk.Treeview(root, columns=list(data[0].keys()), show="headings")
    for col in data[0].keys():
        tree.heading(col, text=col)
        tree.column(col, width=150)

    populate_tree(tree, data)

 
    vsb = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(root, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    vsb.pack(side='right', fill='y')
    hsb.pack(side='bottom', fill='x')

    tree.pack(side="top", fill="both", expand=True)
    root.mainloop()


def get_first_matching_file(pattern):
    print("Looking for files matching pattern:", pattern)
    files = glob.glob(pattern)
    print("Files found:", files)
    if files:
        return files[0]
    return None


def read_weather_info(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        ndvi, lst, burned_area = lines[0].strip().split()
        lon_lat = lines[1].strip()
        weather_data = lines[3:]

    print(f"Debug: lon_lat = {lon_lat}")  
    try:
        lon = lon_lat.split('--center_lon=')[1].split()[0]
        lat = lon_lat.split('--center_lat=')[1].split()[0]
    except IndexError as e:
        print(f"Error parsing longitude/latitude: {e}")
        return None

    return float(ndvi), float(lst), float(burned_area), lon, lat, weather_data
script_directory = './models/03-real-fuels'
average_fire_spread_tif_pattern = './models/03-real-fuels/outputs/vs_0000001*.tif'

def read_average_fire_spread(average_fire_spread_tif):
    try:
        with rasterio.open(average_fire_spread_tif) as src:
            band = src.read(1)
            nodata = src.nodata
            mask = band == nodata
            band_masked = np.ma.masked_array(band, mask=mask)
            average_spread = np.mean(band_masked)
            return average_spread
    except Exception as e:
        print("Error", f"Failed to read raster file: {str(e)}")
        return None
def update_csv_with_average(csv_path, average_spread, priority):
    try:

        with open(csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)

            rows = [row for row in reader]
            fieldnames = reader.fieldnames


        if 'Average Spread Rate (unit)' not in fieldnames:
            fieldnames.append('Average Spread Rate (unit)')
        if 'Priority' not in fieldnames:
            fieldnames.append('Priority')

        for row in rows:
            row['Average Spread Rate (unit)'] = average_spread
            row['Priority'] = priority


        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print("CSV file updated successfully with average fire spread and priority.")
    except Exception as e:
        print(f"Failed to update CSV: {e}")

def modify_bash_script(script_path, lon, lat):
    try:
        with open(script_path, 'r') as file:
            lines = file.readlines()

        new_lines = []
        for line in lines:
            if '--center_lon' in line and '--center_lat' in line:
                
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.startswith('--center_lon'):
                        parts[i] = f"--center_lon={lon}"
                    elif part.startswith('--center_lat'):
                        parts[i] = f"--center_lat={lat}"
                
                line = ' '.join(parts) + '\n'
            new_lines.append(line)  

        with open(script_path, 'w') as file:
            file.writelines(new_lines)
    except Exception as e:
        print(f"Error modifying bash script: {e}")



def display_raster(tif_file_path):
    try:
        with rasterio.open(tif_file_path) as src:
            band = src.read(1)
            plt.imshow(band, cmap='gray_r')
            plt.colorbar()
            plt.title('Raster Image')
            plt.show()
    except Exception as e:
        print(f"Error displaying raster: {e}")


def modify_wx_csv(csv_path, weather_data):
    with open(csv_path, 'w') as file:
        file.write('ws\twd\tm1\tm10\tm100\tlh\tlw\n')
        file.writelines(weather_data)

def run_script(script_path):
    subprocess.run(['bash', script_path], check=True, cwd=script_directory)

def display_raster(tif_file_path):
    with rasterio.open(tif_file_path) as src:
        band = src.read(1)
        zoom_window_size = 10 
        mid_y, mid_x = band.shape[0] // 2, band.shape[1] // 2
        min_row = max(0, mid_y - zoom_window_size)
        max_row = min(band.shape[0], mid_y + zoom_window_size)
        min_col = max(0, mid_x - zoom_window_size)
        max_col = min(band.shape[1], mid_x + zoom_window_size)
        zoomed_band = band[min_row:max_row, min_col:max_col]
        plt.imshow(zoomed_band, cmap='gray_r')
        plt.colorbar()
        plt.title('Raster Image')
        plt.show()


def main():
    script_directory = './models/03-real-fuels'
    script_directory2 = './out/'
    weather_info_path = os.path.join(script_directory2, 'weather_info.txt')
    script_path = os.path.join(script_directory, '01-run.sh')
    csv_path = './models/03-real-fuels/outputs/fire_size_stats.csv'



    result = read_weather_info(weather_info_path)
    if result:
        ndvi, lst, burned_area, lon, lat, weather_data = result
        print(f"NDVI: {ndvi}, LST: {lst}, Burned Area: {burned_area}")
        modify_bash_script(script_path, lon, lat)
        run_script(script_path)
        
        average_fire_spread_tif = get_first_matching_file(average_fire_spread_tif_pattern)
        print(average_fire_spread_tif)

        tif_file_pattern = os.path.join(script_directory, 'outputs', 'time_of_arrival*.tif')
        tif_file_path = get_first_matching_file(tif_file_pattern)
        average_spread = read_average_fire_spread(average_fire_spread_tif)
        if average_spread > 150:
            priority = 5
        elif average_spread > 100:
            priority = 4
        elif average_spread > 50:
            priority = 3
        elif average_spread > 10:
            priority = 2
        else:
            priority = 1
        update_csv_with_average(csv_path, average_spread, priority)
        csv_data = read_csv(csv_path)
        if csv_data:
            create_gui(csv_data)
            csv_data = read_csv(csv_file_path)
        if csv_data:
            for data in csv_data:
                fire_volume = data['Fire Volume (ac-ft)']
                fire_area = data['Total Fire Area (ac)']
                average_spread = data['Average Spread Rate']
                priority = data['Priority of Fire']
                
                update_fire_stats(lon, lat, fire_volume, fire_area, average_spread, priority)

        
        display_raster(tif_file_path)
       
    else:
        print("Failed to read configuration or parse longitude/latitude.")

if __name__ == "__main__":
    main()