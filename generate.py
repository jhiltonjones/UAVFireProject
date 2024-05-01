import random
import time

def generate_random_weather_data(filepath):
    
    center_lon = round(random.uniform(-121, -119), 2)  
    center_lat = round(random.uniform(37, 39), 2)   

    
    weather_data = [
        (
            random.randint(10, 25),       # ws
            random.choice([0, 22.5, 45]), # wd
            random.randint(1, 3),         # m1
            random.randint(2, 4),         # m10
            random.randint(3, 5),         # m100
            random.randint(20, 40),       # lh
            random.randint(50, 70)        # lw
        )
        for _ in range(8)
    ]
      
    value1 = round(random.uniform(0, 1), 6)
    value2 = round(random.uniform(13000, 16000), 2)
    value3 = round(random.uniform(3.0, 6.0), 6)

    

    with open(filepath, 'w') as file:
       
        file.write(f"{value1}\t{value2}\t{value3}\n")
        file.write(f"--center_lon={center_lon} --center_lat={center_lat} \\\n")
        
        file.write("ws\twd\tm1\tm10\tm100\tlh\tlw\n")
        
        
    
        for row in weather_data:
            file.write('\t'.join(map(str, row)) + '\n')

    print(f"Weather information with random location has been written to {filepath}")

def run_at_random_intervals(min_interval_seconds, max_interval_seconds, filepath):
    while True:
        generate_random_weather_data(filepath)
        sleep_time = random.randint(min_interval_seconds, max_interval_seconds)
        print(f"Sleeping for {sleep_time} seconds...")
        time.sleep(sleep_time)

if __name__ == "__main__":
    file_path = './out/weather_info.txt'  
    max_interval_seconds = 50
    min_interval_seconds = 45
    run_at_random_intervals(min_interval_seconds, max_interval_seconds, file_path)