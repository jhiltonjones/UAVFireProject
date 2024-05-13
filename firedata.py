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
import math
from pyproj import Geod
from pyproj import Transformer
import os
<<<<<<< HEAD
from overlaymaps import overlay_raster_at_point, reproject_raster, check_crs
from calculate_multiagent_supressant import get_raster_data_bounds, calculate_x_y_distances, calc_circumference, find_optimal_elliptical_path, plot_fire_ellipse_and_drone_path,calculate_phoschek_needs, convert_utm_to_lat_lon_from_file2, find_optimal_elliptical_path_after_suppressant
=======
from overlaymaps import overlay_raster_at_point, display_location_on_raster_utm, convert_lat_lon_to_utm
from multisuppressant import get_raster_data_bounds, calculate_x_y_distances, calc_circumference, find_optimal_elliptical_path, plot_fire_ellipse_and_drone_path,calculate_phoschek_needs, convert_utm_to_lat_lon_from_file2, find_optimal_elliptical_path_after_suppressant
>>>>>>> ff6c280ab6c5ab7720a2320bddc00ce0344b2761

csv_file_path = './models/03-real-fuels/outputs/fire_size_stats.csv' 
dronepositionpath = './configs/drone_coordinates.txt'

def read_center_info(file_path):
    """Read center longitude and latitude from a file."""
    with open(file_path, 'r') as file:
        lines = file.readlines()
    try:
        lon_lat = lines[5].strip()  
        lon = lon_lat.split('--center_lon=')[1].split()[0]
        lat = lon_lat.split('--center_lat=')[1].split()[0]
        print(lon, lat)
    except IndexError as e:
        print(f"Error parsing longitude/latitude: {e}")
        return None
    return float(lon), float(lat)

def readcenterinfo(file_path):
    """
    Read NDVI, LST, burned area, and center coordinates from a file.
    """
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        
        lon, lat = None, None

        for line in lines:
            if '--center_lon=' in line:
                lon = float(line.split('--center_lon=')[1].split()[0])  
            if '--center_lat=' in line:
                lat = float(line.split('--center_lat=')[1].split()[0])  

            if lon is not None and lat is not None:
                break

        if lon is None or lat is None:
            raise ValueError("Longitude or latitude not found in the file.")

        return lon, lat
    except Exception as e:
        print(f"Error parsing weather info: {e}")
        return None, None
def convert_utm_to_lat_lon_from_file(center_lon, center_lat, filepath, input_crs='epsg:32610', output_crs='epsg:4326'):

    with open(filepath, 'r') as file:
        line = file.readline().strip()
        utm_coords_strings = line.split('\t')  
    utm_coords = []
    for coord in utm_coords_strings:
        parts = coord.strip('()').split(',')
        utm_coords.append((float(parts[0]), float(parts[1])))

    transformer = Transformer.from_crs(input_crs, output_crs, always_xy=True)
    results = {}
    positions = ["Top Left", "Top Right", "Bottom Left", "Bottom Right"]
    
    for pos, (x, y) in zip(positions, utm_coords):
        lon, lat = transformer.transform(x, y)
        results[pos] = (lon, lat)
    print(results)
    results['Center'] = (center_lon, center_lat)

    return results


def calculate_drone_travel_time_fastest(center_lon, center_lat, drone_positions, drone_speed=60):

    geod = Geod(ellps="WGS84")
    min_time = float('inf')
    fastest_drone = None
    
    # print(f"Target coordinates: Longitude = {center_lon}, Latitude = {center_lat}")
    # print("\nDistances to the target location:")
    for drone, (lon, lat) in drone_positions.items():
        _, _, distance = geod.inv(center_lon, center_lat, lon, lat)
        distance_km = distance / 1000  

        # print(f"{drone} is {distance_km:.2f} km away from the target.")

        travel_time_minutes = (distance_km / drone_speed) * 60

        if travel_time_minutes < min_time:
            min_time = travel_time_minutes
            fastest_drone = drone

    # print(f"\nThe fastest drone is {fastest_drone} with a travel time of {min_time:.2f} minutes.")
    return fastest_drone, min_time
def calculate_drone_travel_times(center_lon, center_lat, drone_positions, drone_speed=60):
    geod = Geod(ellps="WGS84")
    drone_travel_times = {}
    max_time = 0
    slowest_drone = None

    for drone, (lon, lat) in drone_positions.items():
        _, _, distance = geod.inv(center_lon, center_lat, lon, lat)
        distance_km = distance / 1000
        travel_time_minutes = (distance_km / drone_speed) * 60

        # Store each drone's travel time in the dictionary
        drone_travel_times[drone] = travel_time_minutes

        # Identify the slowest drone
        if travel_time_minutes > max_time:
            max_time = travel_time_minutes
            slowest_drone = drone

        print(f"{drone} is {distance_km:.2f} km away from the target, travel time: {travel_time_minutes:.2f} minutes.")

    return slowest_drone, max_time, drone_travel_times

def log_fire_data(csv_path, fire_data):
    """
    Log fire data to a CSV file. If the file doesn't exist, create it and add headers.
    """
    fieldnames = ['Date', 'Longitude', 'Latitude', 'Fire Volume (ac-ft)', 'Total Fire Area (ac)', 'Average Spread Rate (unit)', 'Priority', 'Nearest Drone', 'Travel Time', 'Circumference', 'Drone Suppressant Time']
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()  
        writer.writerow(fire_data)


def update_fire_stats(lon, lat, volume, area, spread_rate, priority, fastest_drone, travel_time, optimal_circumference, drone_suppressant_time):
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
        'Priority': priority,
        'Nearest Drone': fastest_drone,
        'Travel Time': travel_time,
        'Circumference': optimal_circumference,
        'Drone Suppressant Time': drone_suppressant_time

    }
    csv_file_path = 'out/fire_log3'
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
                    'Priority of Fire': row.get('Priority', 'N/A'),
                    'Nearest Drone': row.get('Nearest Drone', 'N/A'),
                    'Travel Time': row.get('Travel Time', 'N/A'),
                    'Circumference': row.get('Circumference', 'N/A'),
                    'Drone Suppressant Time': row.get('Drone Suppressant Time', 'N/A')

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


def read_weather_info(file_path='out/weather_info.txt'):
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
def update_csv_with_average(csv_path, average_spread, priority, fastest_drone, travel_time, optimal_circumference, drone_suppressant_time):
    try:

        with open(csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)

            rows = [row for row in reader]
            fieldnames = reader.fieldnames


        if 'Average Spread Rate (unit)' not in fieldnames:
            fieldnames.append('Average Spread Rate (unit)')
        if 'Priority' not in fieldnames:
            fieldnames.append('Priority')
        if 'Nearest Drone' not in fieldnames:
            fieldnames.append('Nearest Drone')
        if 'Travel Time' not in fieldnames:
            fieldnames.append('Travel Time')
        if 'Circumference' not in fieldnames:
            fieldnames.append('Circumference')
        if 'Drone Suppressant Time' not in fieldnames:
            fieldnames.append('Drone Suppressant Time')
        for row in rows:
            row['Average Spread Rate (unit)'] = average_spread
            row['Priority'] = priority
            row['Nearest Drone'] = fastest_drone
            row['Travel Time'] = travel_time
            row ['Circumference'] = optimal_circumference
            row ['Drone Suppressant Time'] = drone_suppressant_time


        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print("CSV file updated successfully with average fire spread and priority.")
    except Exception as e:
        print(f"Failed to update CSV: {e}")

def modify_bash_script(script_path, lon, lat, travel_time):
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
            elif 'SIMULATION_TSTOP' in line:
                travel_time_round = round(travel_time*60)
                line = f"SIMULATION_TSTOP={travel_time_round}\n"
           
            new_lines.append(line)  

        with open(script_path, 'w') as file:
            file.writelines(new_lines)
    except Exception as e:
        print(f"Error modifying bash script: {e}")
def modify_txt_in(script_path2, lon, lat, travel_time):
    try:
        with open(script_path2, 'r') as file:
            lines = file.readlines()

        new_lines = []
        for line in lines:
            if 'SIMULATION_TSTOP' in line:
                travel_time_round = round(travel_time*60)
                line = f"SIMULATION_TSTOP={travel_time_round}\n"
           
            new_lines.append(line)  

        with open(script_path2, 'w') as file:
            file.writelines(new_lines)
    except Exception as e:
        print(f"Error modifying bash script: {e}")

import os
import subprocess

def run_script(script_name):
    script_directory = os.path.join(os.getcwd(), 'models', '03-real-fuels')
    script_path = os.path.join(script_directory, script_name)
    print("Running script at:", script_path)  
    try:
        subprocess.run(['bash', script_path], check=True, cwd=script_directory)
        print("Script executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Script failed with return code {e.returncode}")
    except Exception as e:
        print(f"Failed to run script: {str(e)}")


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

def launch_gui(result, x_dist_n, y_dist_n, results):
    root2= tk.Tk()
    root2.title("Results Display")
    info = f"Optimal Circumference: {result[0]:.2f} km\nDrone Time: {result[1]:.2f} seconds\nx-distance: {x_dist_n:.2f} meters\ny-distance: {y_dist_n:.2f} meters\nPhos-Chek Needs: {results}"
    label = tk.Label(root2, text=info, padx=10, pady=10)
    label.pack()
    button = tk.Button(root2, text="Close", command=root2.destroy)
    button.pack(pady=20)
    root2.mainloop()
def launch_gui_not_a_fire(info):
    root2= tk.Tk()
    root2.title("Fire Warning")
    root2.geometry('600x300')
    label = tk.Label(root2, text=info, padx=10, pady=10)
    label.pack()
    button = tk.Button(root2, text="Close", command=root2.destroy)
    button.pack(pady=20)
    root2.mainloop()
# def find_minimal_effective_circle(fire_area, spread_rate, drone_speed=50):
#     """Find the minimal effective circle the drone can circle, adjusting for fire spread.

#     Args:
#     fire_area (float): Initial fire area in square kilometers.
#     spread_rate (float): Rate of spread of the fire in feet per minute.
#     drone_speed (float): Speed of the drone in km/h.

#     Returns:
#     float: Optimal circumference in km that allows the drone to complete its round.
#     """
#     fire_area_km = fire_area * 0.00404686
#     spread_rate_km_s = spread_rate * 0.0003048 / 60 / 60

#     initial_radius = math.sqrt(fire_area_km / math.pi)
#     increment = 0.01  

#     radius = initial_radius + 0.001  
#     while True:
#         circumference = 2 * math.pi * radius
#         drone_time_to_cover = circumference / (drone_speed / 3600)  

#         additional_area = spread_rate_km_s * drone_time_to_cover
#         new_fire_area = math.pi * radius ** 2 + additional_area
#         new_radius = math.sqrt(new_fire_area / math.pi)

#         if new_radius > radius:
#             break

#         radius -= increment

#     final_circumference = 2 * math.pi * radius
#     final_drone_time_to_cover = final_circumference / (drone_speed / 3600)
#     return final_circumference, final_drone_time_to_cover
    
def main():
    script_directory = 'models/03-real-fuels'
    weather_info_path = ('out/weather_info.txt')
    script_path = os.path.join(script_directory, '01-run.sh')
    script_path2 = os.path.join(script_directory, 'elmfire.data.in')
    csv_path = './models/03-real-fuels/outputs/fire_size_stats.csv'
    base_raster_path= 'models/04-fire-potential/outputs/head_fire_spread_rate_006.tif'

    result = read_weather_info(weather_info_path)
    if result:
        ndvi, lst, burned_area, lon, lat, weather_data = result
        print(f"NDVI: {ndvi}, LST: {lst}, Burned Area: {burned_area}")
        center_lon, center_lat = read_center_info(file_path = './models/04-fire-potential/01-run.sh')
        converted_coords = convert_utm_to_lat_lon_from_file(center_lon, center_lat, dronepositionpath)
        # cen_lon, cen_lat = readcenterinfo(file_path = '/home/jack/elmfire/tutorials/04-fire-potential/01-run.sh')
        fastest_drone, travel_time = calculate_drone_travel_time_fastest(lon, lat, converted_coords)
        
        print(travel_time)
        modify_bash_script(script_path, lon, lat, travel_time)
        modify_txt_in(script_path2, lon, lat, travel_time)
        # modify_wx_csv(weather_write_path, weather_data)
        
        run_script('01-run.sh')
        
        average_fire_spread_tif = get_first_matching_file(average_fire_spread_tif_pattern)
        print(average_fire_spread_tif)
        tif_file_pattern = os.path.join(script_directory, 'outputs', 'time_of_arrival*.tif')
        tif_file_path = get_first_matching_file(tif_file_pattern)
        overlay_raster_path = tif_file_path
        average_spread = read_average_fire_spread(average_fire_spread_tif)
        round_average_spread = round(average_spread,2)
        csv_data = read_csv(csv_path)
        for data in csv_data:
                fire_area = float(data['Total Fire Area (ac)'])
        if fire_area < 0.3:
            info = 'NOT A FIRE'
            launch_gui_not_a_fire(info)
            return
        
        print(fire_area, round_average_spread)
                # display_raster(tif_file_path)
        desired_crs = 'EPSG:32610'
        base_raster_crs = check_crs(base_raster_path)
        overlay_raster_crs = check_crs(overlay_raster_path)

        if base_raster_crs != desired_crs:
            new_base_raster_path = os.path.splitext(base_raster_path)[0] + '_reprojected.tif'
            reproject_raster(base_raster_path, new_base_raster_path, desired_crs)
            base_raster_path = new_base_raster_path

        if overlay_raster_crs != desired_crs:
            new_overlay_raster_path = os.path.splitext(overlay_raster_path)[0] + '_reprojected.tif'
            reproject_raster(overlay_raster_path, new_overlay_raster_path, desired_crs)
            overlay_raster_path = new_overlay_raster_path
        
        base_raster_crs = check_crs(base_raster_path)
        overlay_raster_crs = check_crs(overlay_raster_path)

        print("Base Raster CRS:", base_raster_crs)
        print("Overlay Raster CRS:", overlay_raster_crs)
        overlay_raster_at_point(base_raster_path, overlay_raster_path)
        lat2_utm, lon1_utm, lat1_utm, lon2_utm = get_raster_data_bounds(tif_file_path)
        # print(lon1_utm, lat1_utm, lon2_utm, lat2_utm)
        lat1,lon1 = convert_utm_to_lat_lon_from_file2(lat1_utm,lon1_utm)
        lat2,lon2= convert_utm_to_lat_lon_from_file2(lat2_utm,lon2_utm)
        print( lon1, lon2, lat1, lat2)
        start_coords = lon1,lat1
        end_coords = lon2, lat2
        x_dist, y_dist = calculate_x_y_distances(lon1, lat1, lon2, lat2)
        # distance = haversine_distance(start_coords, end_coords)
        print(f"x distance: {x_dist} y distance: {y_dist}")
        
        spread_rate = average_spread  # feet per minute

        result = find_optimal_elliptical_path(x_dist, y_dist, spread_rate)
        print(f"Optimal Circumference: {result[0]} km, Drone Time: {result[1]} seconds")
        major_axis = x_dist/2
        minor_axis = y_dist/2
        plot_fire_ellipse_and_drone_path(major_axis, minor_axis, start_coords, end_coords)
        # plot_fire_ellipse_and_drone_path_on_raster(major_axis, minor_axis, start_coords, end_coords, filepath)
        length = result[0] * 1000  # in meters
        width = 10  # in meters
        results = calculate_phoschek_needs(length, width)
        print(results)
        drone_suppressant_time = result[1]
        optimal_circumference = result[0]

        # optimal_circumference, drone_suppressant_time = find_minimal_effective_circle(fire_area, round_average_spread)
        # print(optimal_circumference, drone_suppressant_time)
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
        update_csv_with_average(csv_path, average_spread, priority, fastest_drone, travel_time, optimal_circumference, drone_suppressant_time)
        
        if csv_data:
            
            csv_data = read_csv(csv_file_path)
        if csv_data:
            for data in csv_data:
                fire_volume = data['Fire Volume (ac-ft)']
                fire_area = data['Total Fire Area (ac)']
                average_spread = data['Average Spread Rate']
                priority = data['Priority of Fire']
                fastest_drone = data['Nearest Drone']
                travel_time = data['Travel Time']
                optimal_circumference = data['Circumference']
                drone_suppressant_time = data['Drone Suppressant Time']
                
                update_fire_stats(lon, lat, fire_volume, fire_area, average_spread, priority, fastest_drone, travel_time, optimal_circumference, drone_suppressant_time)
        create_gui(csv_data)
        try:
            fire_area_float = float(fire_area)
        except ValueError:
            print("Error converting fire area to float")

        if fire_area_float < 1:
            info = 'This fire does NOT need multiagent, fire will be removed by closest drone'
            launch_gui_not_a_fire(info)
            launch_gui(result, x_dist, y_dist, results)
            return

        launch_gui(result, x_dist, y_dist, results)
        
        slowest_drone, max_travel_time, all_travel_times = calculate_drone_travel_times(center_lon, center_lat, converted_coords)            
        modify_bash_script(script_path, lon, lat, max_travel_time)
        modify_txt_in(script_path2, lon, lat, max_travel_time)
        
        run_script('01-run.sh')
        tif_file_path = get_first_matching_file(tif_file_pattern)
        lat2_utm, lon1_utm, lat1_utm, lon2_utm = get_raster_data_bounds(tif_file_path)
        # print(lon1_utm, lat1_utm, lon2_utm, lat2_utm)
        lat12,lon12 = convert_utm_to_lat_lon_from_file2(lat1_utm,lon1_utm)
        lat22,lon22= convert_utm_to_lat_lon_from_file2(lat2_utm,lon2_utm)
        print( lon12, lon22, lat12, lat22)
        start_coords = lon12,lat12
        end_coords = lon12, lat2
        x_dist_n, y_dist_n = calculate_x_y_distances(lon1, lat12, lon2, lat22)
        # distance = haversine_distance(start_coords, end_coords)
        print(f"x distance: {x_dist_n} y distance: {y_dist_n}")
        result = find_optimal_elliptical_path(x_dist_n, y_dist_n, spread_rate)
        print(f"Optimal Circumference: {result[0]} km, Drone Time: {result[1]} seconds")
        # major_axis = x_dist_n/2
        # minor_axis = y_dist_n/2
        # plot_fire_ellipse_and_drone_path(major_axis, minor_axis, start_coords, end_coords)
        length = result[0] * 1000  # in meters
        width = 10  # in meters
        results = calculate_phoschek_needs(length, width)
        print(results)
        launch_gui(result, x_dist_n, y_dist_n, results)


    else:
        print("Failed to read configuration or parse longitude/latitude.")
    


if __name__ == "__main__":
    main()