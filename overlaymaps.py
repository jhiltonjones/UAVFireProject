import rasterio
import matplotlib.pyplot as plt
from rasterio.plot import show
from pyproj import Transformer
import numpy as np
def convert_lat_lon_to_utm(lon, lat, output_crs='epsg:32610'):
    """ Convert latitude and longitude to UTM coordinates. """
    transformer = Transformer.from_crs('epsg:4326', output_crs, always_xy=True)
    x, y = transformer.transform(lon, lat)
    return x, y

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
def normalize(array):
    array_min, array_max = array.min(), array.max()
    return (array - array_min) / (array_max - array_min)



def overlay_raster_at_point(base_raster_path, overlay_raster_path):
    try:
     
        with rasterio.open(base_raster_path) as base_src:
            band1 = base_src.read(1)  
            nodata = base_src.nodata
            mask = band1 == nodata
            band1_masked = np.ma.masked_array(band1, mask=mask)
            band1_normalized = normalize(band1_masked)

            base_extent = [
                base_src.bounds.left, 
                base_src.bounds.right, 
                base_src.bounds.bottom, 
                base_src.bounds.top
            ]

        with rasterio.open(overlay_raster_path) as overlay_src:
            overlay_band = overlay_src.read(1)
            band2 = overlay_src.read(1)  
            nodata = overlay_src.nodata
            mask = band2 == nodata
            band2_masked = np.ma.masked_array(band1, mask=mask)
            overlay_extent = [
                overlay_src.bounds.left, 
                overlay_src.bounds.right, 
                overlay_src.bounds.bottom, 
                overlay_src.bounds.top
            ]

            plt.figure(figsize=(10, 10))
            plt.imshow(band1_normalized, cmap='Greens', extent=base_extent, interpolation='none')
            plt.imshow(band2_masked, cmap='Oranges', extent=overlay_extent, alpha=1.0, interpolation='none')
            plt.title('Overlay Raster on Base Raster')
            zoom_center_x = (overlay_extent[0] + overlay_extent[1]) / 2
            zoom_center_y = (overlay_extent[2] + overlay_extent[3]) / 2
            zoom_width = 50000 
            zoom_height = 50000  

            plt.xlim(zoom_center_x - zoom_width / 2, zoom_center_x + zoom_width / 2)
            plt.ylim(zoom_center_y - zoom_height / 2, zoom_center_y + zoom_height / 2)

            plt.show()

    except Exception as e:
        print(f"An error occurred: {e}")



base_raster_path = 'models/04-fire-potential/outputs/head_fire_spread_rate_006.tif'
overlay_raster_path = 'models/03-real-fuels/outputs/time_of_arrival_0000001_0003605.tif'
file_path = 'out/weather_info.txt'  
longitude, latitude = readcenterinfo(file_path)   
utm_x, utm_y = convert_lat_lon_to_utm(longitude, latitude)
overlay_raster_at_point(base_raster_path, overlay_raster_path)
