import random
import time

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
import random
import math

def generate_random_coordinate(lon, lat):
    R = 6371.0

    random_radius = random.uniform(0, 18)

    random_angle = random.uniform(0, 2 * math.pi)

    radius_in_degrees = random_radius / R

    delta_lat = radius_in_degrees * math.cos(random_angle)
    delta_lon = radius_in_degrees * math.sin(random_angle) / math.cos(math.radians(lat))

    random_lat = lat + delta_lat * (180 / math.pi)
    random_lon = lon + delta_lon * (180 / math.pi)

    random_lon = round(random_lon, 2)
    random_lat = round(random_lat, 2)

    return random_lon, random_lat

def generate_random_weather_data(filepath, file_path, weather_path):
    
    weather_data = read_weather_info(weather_path)
    lon, lat = read_center_info(file_path='models/04-fire-potential/01-run.sh')
    random_lon, random_lat = generate_random_coordinate(lon, lat)
    if lon is None or lat is None:
        return

    value1 = round(random.uniform(0, 1), 6)
    value2 = round(random.uniform(13000, 16000), 2)
    value3 = round(random.uniform(3.0, 6.0), 6)

    with open(filepath, 'w') as file:
        file.write(f"{value1}\t{value2}\t{value3}\n")
        file.write(f"--center_lon={random_lon} --center_lat={random_lat} \\\n")
        file.write("ws\twd\tm1\tm10\tm100\tlh\tlw\n")
        print(weather_data)
        for row in weather_data:
            file.write(row)

def run_at_random_intervals(min_interval_seconds, max_interval_seconds, filepath, file_path, weather_path):
    """Run data generation at random intervals."""
    while True:
        generate_random_weather_data(filepath, file_path, weather_path)
        # sleep_time = random.randint(min_interval_seconds, max_interval_seconds)
        # print(f"Sleeping for {sleep_time} seconds...")
        # time.sleep(sleep_time)
        exit()
def read_weather_info(weather_path):
    with open(weather_path, 'r') as file:
        lines = file.readlines()
        weather_data = lines[1:]

    return weather_data
if __name__ == "__main__":
    filepath = 'out/weather_info.txt'
    file_path = 'models/04-fire-potential/01-run.sh'
    weather_path = 'models/04-fire-potential/wx.csv'
    max_interval_seconds = 50
    min_interval_seconds = 45
    run_at_random_intervals(min_interval_seconds, max_interval_seconds, filepath, file_path, weather_path)
