import rasterio
import math
import numpy as np
from pyproj import Transformer
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse
from rasterio.plot import show

def get_raster_data_bounds(filepath):
    with rasterio.open(filepath) as dataset:
        data = dataset.read(1)  
        mask = dataset.read_masks(1)  

        rows, cols = np.nonzero(mask)

        if rows.size > 0 and cols.size > 0:
            x_coords, y_coords = dataset.transform * (cols, rows)

            min_x, max_x = x_coords.min(), x_coords.max()
            min_y, max_y = y_coords.min(), y_coords.max()
        else:
            return None

    return min_x, min_y, max_x, max_y


def calculate_x_y_distances(lat1, lon1, lat2, lon2):
    R = 6371 * 1000

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    delta_lat_rad = math.radians(delta_lat)
    delta_lon_rad = math.radians(delta_lon)

    y_distance = (delta_lat_rad * R)/1000
    x_distance = (delta_lon_rad * R * math.cos((lat1_rad + lat2_rad) / 2))/1000

    return abs(x_distance), abs(y_distance)






def calc_circumference(major_axis, minor_axis):
    # Using Ramanujan's approximation for the circumference of an ellipse
    a = major_axis
    b = minor_axis
    h = (a - b)**2 / (a + b)**2
    return math.pi * (a + b) * (1 + (3 * h) / (10 + math.sqrt(4 - 3 * h)))

def find_optimal_elliptical_path(x_dist, y_dist, spread_rate, drone_speed=50):
    spread_rate_km_s = spread_rate * 0.0003048 / 60 / 60
    # print(x_dist, y_dist)
    initial_major_axis = y_dist/2
    # print('initial major' , initial_major_axis)
    initial_minor_axis = x_dist/2
    # print('initial minor' , initial_minor_axis)
    smallest_circumference = float('inf')
    optimal_drone_time = 0
    major_axis = initial_major_axis + 0.01
    minor_axis = initial_minor_axis + 0.01
    increment = 0.001  

    while minor_axis > 0:
        initial_circumference = calc_circumference(major_axis, minor_axis)
        # print( f"initial c: {initial_circumference}")
        drone_time_to_cover = initial_circumference / (drone_speed / 3600)
        additional_fire_spread = spread_rate_km_s * drone_time_to_cover
        # print(additional_fire_spread)
        # print(drone_time_to_cover)
        increased_major_axis = initial_major_axis + additional_fire_spread 
        new_circumference = calc_circumference(increased_major_axis, initial_minor_axis)
        # print(increased_major_axis, initial_minor_axis)

        # print(new_circumference)
        if new_circumference > initial_circumference:
            break
        elif initial_circumference < smallest_circumference:
            smallest_circumference = initial_circumference
            optimal_drone_time = drone_time_to_cover

        minor_axis -= increment  
        major_axis -= increment
    return smallest_circumference, optimal_drone_time

def find_optimal_elliptical_path_after_suppressant(x_dist_n, y_dist_n, spread_rate, drone_speed=50):
    # Convert spread rate to km/s for consistency in units
    spread_rate_km_s = spread_rate * 0.0003048 / 60 / 60
    # print(x_dist, y_dist)
    initial_major_axis = y_dist_n/2
    # print('initial major' , initial_major_axis)
    initial_minor_axis = x_dist_n/2
    # print('initial minor' , initial_minor_axis)
    smallest_circumference = float('inf')
    optimal_drone_time = 0
    major_axis = initial_major_axis + 0.01
    minor_axis = initial_minor_axis + 0.01
    increment = 0.001  #

    while minor_axis > 0:
        initial_circumference = calc_circumference(major_axis, minor_axis)
        # print( f"initial c: {initial_circumference}")
        drone_time_to_cover = initial_circumference / (drone_speed / 3600)
        additional_fire_spread = spread_rate_km_s * drone_time_to_cover
        # print(drone_time_to_cover)
        increased_minor_axis = initial_minor_axis + (additional_fire_spread)
        new_circumference = calc_circumference(initial_major_axis, increased_minor_axis)
        # print(initial_major_axis, increased_minor_axis)
        # print(new_circumference)

        if new_circumference > initial_circumference:
            break
        elif initial_circumference < smallest_circumference:
            smallest_circumference = initial_circumference
            optimal_drone_time = drone_time_to_cover

        minor_axis -= 0.0001
        major_axis -=increment
    return smallest_circumference, optimal_drone_time
def convert_utm_to_lat_lon_from_file2(x, y, input_crs='epsg:32610', output_crs='epsg:4326'):


    transformer = Transformer.from_crs(input_crs, output_crs, always_xy=True)
    lat, lon = transformer.transform(x, y)


    return lat, lon

def plot_fire_ellipse_and_drone_path(major_axis, minor_axis, start_coords, end_coords):
    fig, ax = plt.subplots()

    center_x = (start_coords[0] + end_coords[0]) / 2
    center_y = (start_coords[1] + end_coords[1]) / 2

    ellipse = Ellipse((center_x, center_y), width=2*major_axis, height=2*minor_axis, 
                      edgecolor='red', facecolor='none', label='Fire Area')
    ax.add_patch(ellipse)

    drone_path_ellipse = Ellipse((center_x, center_y), width=2*major_axis*1.05, height=2*minor_axis*1.05,
                                 edgecolor='blue', linestyle='--', facecolor='none', label='Drone Path')
    ax.add_patch(drone_path_ellipse)

    ax.set_xlim(center_x - major_axis*20, center_x + major_axis*20)
    ax.set_ylim(center_y - minor_axis*1.2, center_y + minor_axis*1.2)
    ax.set_aspect('equal', 'box')

    plt.grid(True)
    plt.legend()
    plt.title('Visualization of Fire Area and Drone Path')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.show()


def calculate_phoschek_needs(length_m, width_m, application_rate_l_per_m2=1):

    """

    Calculate the required amount of Phos-Chhek LC-95-W concentrate and its weight to cover a specific area.

    

    Parameters:

    - length_m (float): The length of the area to cover in meters.

    - width_m (float): The width of the area to cover in meters.

    - application_rate_l_per_m2 (float): Application rate in liters per square meter.

    

    Returns:

    - dict: A dictionary containing the gallons of concentrate, total gallons of mixed retardant, and weight of concentrate needed.

    """
    LITERS_PER_GALLON = 3.785
    MIX_RATIO = 5.5  # Gallons of water per gallon of concentrate
    TOTAL_MIX_FROM_ONE_GAL_CONCENTRATE = 1 + MIX_RATIO  # Total mixed retardant from one gallon of concentrate
    WEIGHT_PER_GAL_CONCENTRATE = 12.31  # in pounds
    area_m2 = length_m * width_m
    total_liters_needed = area_m2 * application_rate_l_per_m2
    total_gallons_needed = total_liters_needed / LITERS_PER_GALLON
    gallons_of_concentrate = total_gallons_needed / TOTAL_MIX_FROM_ONE_GAL_CONCENTRATE
    weight_of_concentrate = gallons_of_concentrate * WEIGHT_PER_GAL_CONCENTRATE
    return {
        'gallons_of_concentrate': round(gallons_of_concentrate, 2),
        'total_gallons_of_retardant': round(total_gallons_needed, 2),
        'weight_of_concentrate_lbs': round(weight_of_concentrate, 2)
    }




def main():
    filepath = 'models/03-real-fuels/outputs/time_of_arrival_0000001_0000814.tif'
    lat2_utm, lon1_utm, lat1_utm, lon2_utm = get_raster_data_bounds(filepath)
    # print(lon1_utm, lat1_utm, lon2_utm, lat2_utm)
    lat1,lon1 = convert_utm_to_lat_lon_from_file2(lat1_utm,lon1_utm)
    lat2,lon2= convert_utm_to_lat_lon_from_file2(lat2_utm,lon2_utm)
    # print(lat1, lat2, lon1, lon2)
    start_coords = lon1,lat2
    end_coords = lon2, lat1
    x_dist, y_dist = calculate_x_y_distances(lon1, lat1, lon2, lat2)
    # distance = haversine_distance(start_coords, end_coords)
    print(x_dist, y_dist)
    result = find_optimal_elliptical_path(x_dist, y_dist, spread_rate)
    print(f"Optimal Circumference: {result[0]} km, Drone Time: {result[1]} seconds")
    major_axis = x_dist/2
    minor_axis = y_dist/2
    plot_fire_ellipse_and_drone_path(major_axis, minor_axis, start_coords, end_coords)
    length = result[0] * 1000  # in meters
    width = 10  # in meters
    results = calculate_phoschek_needs(length, width)
    print(results)

if __name__ == "__main__":
    main()
