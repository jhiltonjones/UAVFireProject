import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import rasterio
import matplotlib
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import math
import matplotlib.pyplot as plt


# Paths
script_directory = '/home/jack/elmfire/tutorials/Custom/Automated_drone/04-fire-potential'
script_path = os.path.join(script_directory, '01-run.sh')
wx_csv_path = os.path.join(script_directory, 'wx.csv')
def quadrant_sum(cumulative_sum, top, left, bottom, right):
    total = cumulative_sum[bottom, right]
    top_area = cumulative_sum[top-1, right] if top > 0 else 0
    left_area = cumulative_sum[bottom, left-1] if left > 0 else 0
    overlap = cumulative_sum[top-1, left-1] if top > 0 and left > 0 else 0
    return total - top_area - left_area + overlap

def compute_diff(cumulative_sum, horizontal, vertical, shape):
    top_left = quadrant_sum(cumulative_sum, 0, 0, horizontal, vertical)
    top_right = quadrant_sum(cumulative_sum, 0, vertical + 1, horizontal, shape[1] - 1)
    bottom_left = quadrant_sum(cumulative_sum, horizontal + 1, 0, shape[0] - 1, vertical)
    bottom_right = quadrant_sum(cumulative_sum, horizontal + 1, vertical + 1, shape[0] - 1, shape[1] - 1)

    diff = max(top_left, top_right, bottom_left, bottom_right) - min(top_left, top_right, bottom_left, bottom_right)
    return diff, horizontal, vertical
def run_shell_script(script_path):
    """ Run the shell script to generate the raster data. """
    try:
        os.chdir(script_directory)
        subprocess.run(['bash', script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the shell script: {e}")
        return False
    return True
def execute_and_process():
    if run_shell_script(script_path):
        print("Shell script executed successfully.")
        process_raster()
    else:
        messagebox.showerror("Error", "Failed to execute the shell script.")
def process_raster():
    with rasterio.open('/home/jack/elmfire/tutorials/Custom/Automated_drone/04-fire-potential/outputs/head_fire_spread_rate_006.tif') as src:
        band1 = src.read(1)  
        nodata = src.nodata
        mask = band1 == nodata
        band1_masked = np.ma.masked_array(band1, mask=mask)

        rows_with_data = np.any(~mask, axis=1)
        cols_with_data = np.any(~mask, axis=0)
        top, bottom = np.where(rows_with_data)[0][[0, -1]]
        left, right = np.where(cols_with_data)[0][[0, -1]]

        cumulative_sum = np.cumsum(np.cumsum(band1_masked.filled(0), axis=0), axis=1)

        min_diff = np.inf
        optimal_horizontal, optimal_vertical = None, None

        with ThreadPoolExecutor() as executor:
            futures = []
            for vertical in range(1, band1_masked.shape[1] - 1):
                for horizontal in range(1, band1_masked.shape[0] - 1):
                    futures.append(executor.submit(compute_diff, cumulative_sum, horizontal, vertical, band1_masked.shape))

            for future in futures:
                diff, horizontal, vertical = future.result()
                if diff < min_diff:
                    min_diff = diff
                    optimal_horizontal = horizontal
                    optimal_vertical = vertical

        print(f"Optimal horizontal line at: {optimal_horizontal}")
        print(f"Optimal vertical line at: {optimal_vertical}")



        mid_top_left = (top + optimal_horizontal) // 2, (left + optimal_vertical) // 2
        mid_top_right = (top + optimal_horizontal) // 2, (optimal_vertical + right) // 2
        mid_bottom_left = (optimal_horizontal + bottom) // 2, (left + optimal_vertical) // 2
        mid_bottom_right = (optimal_horizontal + bottom) // 2, (optimal_vertical + right) // 2

        top_right_top_left = optimal_horizontal, optimal_vertical
        top_right_top_right = optimal_horizontal, right
        top_right_bottom_left = bottom, optimal_vertical
        top_right_bottom_right = bottom, right
        pixel_width, pixel_height = src.res
        pixel_area = pixel_width * pixel_height  

        num_pixels_top_left = np.count_nonzero(~band1_masked.mask[:optimal_horizontal, :optimal_vertical])
        num_pixels_top_right = np.count_nonzero(~band1_masked.mask[:optimal_horizontal, optimal_vertical:])
        num_pixels_bottom_left = np.count_nonzero(~band1_masked.mask[optimal_horizontal:, :optimal_vertical])
        num_pixels_bottom_right = np.count_nonzero(~band1_masked.mask[optimal_horizontal:, optimal_vertical:])

        area_top_left = num_pixels_top_left * pixel_area / 1e6  

        area_top_right = num_pixels_top_right * pixel_area / 1e6
        area_bottom_left = num_pixels_bottom_left * pixel_area / 1e6
        area_bottom_right = num_pixels_bottom_right * pixel_area / 1e6

        quadrants = [
            ("Top Left", area_top_left),
            ("Top Right", area_top_right),
            ("Bottom Left", area_bottom_left),
            ("Bottom Right", area_bottom_right),
        ]
        print(f"Area of Top Left Quadrant: {area_top_left} km²")
        print(f"Area of Top Right Quadrant: {area_top_right} km²")
        print(f"Area of Bottom Left Quadrant: {area_bottom_left} km²")
        print(f"Area of Bottom Right Quadrant: {area_bottom_right} km²")

        HFOV_width = 4200  
        speed_ms = 22.73  
        total_num_drones = 0
        for quadrant, area in quadrants:
            side_length = math.sqrt(area * 1e6)  
            num_passes = math.ceil(side_length / HFOV_width)  
            time_per_pass = side_length / speed_ms  
            total_time_detection = time_per_pass * num_passes / 60  
            print(f"Time to cover {quadrant} Quadrant with one dection drone: {total_time_detection:.2f} minutes")
            if area < 200:
                time_needed_to_detect = 5
            elif area <400:
                time_needed_to_detect = 6
            elif area < 600:
                time_needed_to_detect = 7
            elif area < 800:
                time_needed_to_detect = 8
            else:
                time_needed_to_detect = 9

            num_drones_needed = total_time_detection / time_needed_to_detect
            print(f"The number of drones needed to complete this quandrant in {time_needed_to_detect} mins is: {num_drones_needed}")
            total_num_drones += num_drones_needed
            print(f"The total number of dornes needed for this area is: {total_num_drones}")



        line_width = 2  

        print(f"Suppressor Drone 1  go to coordinates: {mid_top_left}")
        print(f"Suppressor Drone 2  go to coordinates: {mid_top_right}")
        print(f"Suppressor Drone 3  go to coordinates: {mid_bottom_left}")
        print(f"Suppressor Drone 4  go to coordinates: {mid_bottom_right}")

        print(f"Detection Drone 1 go to coordinates: {top_right_top_left}")
        print(f"Detection Drone 2 go to coordinates: {top_right_top_right}")
        print(f"Detection Drone 3 go to coordinates: {top_right_bottom_left}")
        print(f"Detection Drone 4 go to coordinates: {top_right_bottom_right}")
        # Visualization code
        plt.imshow(band1_masked, cmap='coolwarm')
        plt.axhline(y=optimal_horizontal, color='k', linestyle='-', linewidth=line_width)
        plt.axvline(x=optimal_vertical, color='k', linestyle='-', linewidth=line_width)
        plt.scatter([mid[1] for mid in [mid_top_left, mid_top_right, mid_bottom_left, mid_bottom_right]], 
                    [mid[0] for mid in [mid_top_left, mid_top_right, mid_bottom_left, mid_bottom_right]], 
                    color='gray', s=50)
        plt.scatter([tr[1] for tr in [top_right_top_left, top_right_top_right, top_right_bottom_left, top_right_bottom_right]], 
                    [tr[0] for tr in [top_right_top_left, top_right_top_right, top_right_bottom_left, top_right_bottom_right]], 
                    color='red', s=50)
        plt.colorbar(label='Risk Level', cmap='coolwarm')
        plt.title('Fire Spread Risk with Optimal Split Lines')
        plt.show()
    messagebox.showinfo("Success", "Raster processed successfully.")



# Modify the Bash script
def modify_bash_script():
    new_lon = lon_entry.get()
    new_lat = lat_entry.get()
    new_buffers = buffer_entry.get()
    try:
        with open(script_path, 'r') as file:
            lines = file.readlines()

        new_lines = []
        for line in lines:
            if '--center_lon' in line or '--center_lat' in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.startswith('--center_lon'):
                        parts[i] = f"--center_lon={new_lon}"
                    elif part.startswith('--center_lat'):
                        parts[i] = f"--center_lat={new_lat}"
                    elif part.endswith('buffer'):
                        parts[i] = f"--{part.split('=')[0].split('--')[1]}={new_buffers}"
                new_lines.append(' '.join(parts) + '\n')
            else:
                new_lines.append(line)

        with open(script_path, 'w') as file:
            file.writelines(new_lines)
        messagebox.showinfo("Success", "Bash script updated successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to modify the Bash script: {str(e)}")

# Modify the wx.csv file
def modify_wx_csv():
    new_rows = wx_entry.get()
    try:
        with open(wx_csv_path, 'w') as file:
            file.write('ws,wd,m1,m10,m100,lh,lw\n')
            file.write('0,0,2,3,4,30,60\n')
            file.write('0,0,2,3,4,30,60\n')
            file.write('0,0,2,3,4,30,60\n')
            file.write('0,0,2,3,4,30,60\n')
            file.write('0,0,2,3,4,30,60\n')
            file.write(new_rows + '\n')
        messagebox.showinfo("Success", "CSV file updated successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to modify the wx.csv file: {str(e)}")

# GUI setup
root = tk.Tk()
root.title("Configuration Editor")

# Entry widgets for script parameters
tk.Label(root, text="Enter Longitude:").pack(pady=(10, 0))
lon_entry = ttk.Entry(root, width=20)
lon_entry.pack(pady=5)
tk.Label(root, text="Enter Latitude:").pack(pady=(10, 0))
lat_entry = ttk.Entry(root, width=20)
lat_entry.pack(pady=5)
tk.Label(root, text="Enter buffer area:").pack(pady=(10, 0))
buffer_entry = ttk.Entry(root, width=20)
buffer_entry.pack(pady=5)

# Entry widget for CSV data
tk.Label(root, text="Enter weather information(ws, wd, m1, m10, m100, lh, lw):").pack(pady=(10, 0))
wx_entry = ttk.Entry(root, width=40 )
wx_entry.pack(pady=5)

# Buttons for saving changes
save_script_button = ttk.Button(root, text="Save Bash Script", command=modify_bash_script)
save_script_button.pack(pady=5)
save_csv_button = ttk.Button(root, text="Save CSV", command=modify_wx_csv)
save_csv_button.pack(pady=5)

run_button = ttk.Button(root, text="Run Script and Process Raster", command=execute_and_process)
run_button.pack(pady=20)
root.mainloop()