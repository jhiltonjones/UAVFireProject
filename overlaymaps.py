import rasterio
import matplotlib.pyplot as plt
from rasterio.plot import show
from pyproj import Transformer
import numpy as np
import os
import glob
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
def normalise(array):
    array_min, array_max = array.min(), array.max()
    return (array - array_min) / (array_max - array_min)



def overlay_raster_at_point(base_raster_path, overlay_raster_path, zoom_scale=0.1, zoom_scale2 = 1):
    try:
        with rasterio.open(base_raster_path) as base_src:
            band1 = base_src.read(1)  
            nodata = base_src.nodata
            mask = band1 == nodata
            band1_masked = np.ma.masked_array(band1, mask=mask)
            band1_normalised = normalise(band1_masked)
            base_extent = [
                base_src.bounds.left, 
                base_src.bounds.right, 
                base_src.bounds.bottom, 
                base_src.bounds.top
            ]

        with rasterio.open(overlay_raster_path) as overlay_src:
            band2 = overlay_src.read(1)  
            nodata = overlay_src.nodata
            mask = band2 == nodata
            band2_masked = np.ma.masked_array(band2, mask=mask)
            overlay_extent = [
                overlay_src.bounds.left, 
                overlay_src.bounds.right, 
                overlay_src.bounds.bottom, 
                overlay_src.bounds.top
            ]

            center_x = (overlay_extent[0] + overlay_extent[1]) / 2
            center_y = (overlay_extent[2] + overlay_extent[3]) / 2
            half_width = (overlay_extent[1] - overlay_extent[0]) * zoom_scale / 2
            half_height = (overlay_extent[3] - overlay_extent[2]) * zoom_scale / 2
            zoomed_extent = [
                center_x - half_width,
                center_x + half_width,
                center_y - half_height,
                center_y + half_height
            ]
            center_x2 = (base_extent[0] + base_extent[1]) / 2
            center_y2 = (base_extent[2] + base_extent[3]) / 2
            half_width2 = (base_extent[1] - base_extent[0]) * zoom_scale2 / 2
            half_height2 = (base_extent[3] - base_extent[2]) * zoom_scale2 / 2
            zoomed_extent2 = [
                center_x2 - half_width2,
                center_x2 + half_width2,
                center_y2 - half_height2,
                center_y2 + half_height2
            ]

            plt.figure(figsize=(10, 10))
            plt.imshow(band1_normalised, cmap='Greens', extent=base_extent, interpolation='none')
            plt.imshow(band2_masked, cmap='Oranges_r', extent=overlay_extent, alpha=1.0, interpolation='none')
            plt.title('Overlay Raster on Base Raster')
            plt.xlim(zoomed_extent[0], zoomed_extent[1])
            plt.ylim(zoomed_extent[2], zoomed_extent[3])
            plt.show()
            # plt.figure(figsize=(10, 10))
            # plt.imshow(band1_normalised, cmap='Grays', extent=base_extent, interpolation='none')
            # plt.imshow(band2_masked, cmap='Reds_r', extent=overlay_extent, alpha=1.0, interpolation='none')
            # plt.title('Overlay Raster on Base Raster')
            # plt.xlim(zoomed_extent2[0], zoomed_extent2[1])
            # plt.ylim(zoomed_extent2[2], zoomed_extent2[3])
            # plt.show()
            with rasterio.open(base_raster_path) as base_src:
                col, row = base_src.index(center_x2, center_y2)  
                
                plt.figure(figsize=(10, 10))
                plt.imshow(band1_normalised, cmap='Greens', extent=base_extent, interpolation='none')
                plt.scatter([center_x], [center_y], color='red', s=50, label='Overlay Center')  
                plt.title('Overlay Raster on Base Raster with Center Marked')
                plt.legend()
                plt.show()

    except Exception as e:
        print(f"An error occurred: {e}")


    except Exception as e:
        print(f"An error occurred: {e}")
def get_first_matching_file(pattern):
    print("Looking for files matching pattern:", pattern)
    files = glob.glob(pattern)
    print("Files found:", files)
    if files:
        return files[0]
    return None

def display_location_on_raster_utm(raster_path, x, y):
    """ Display UTM coordinates on the raster image. """
    with rasterio.open(raster_path) as src:
        col, row = src.index(x, y)

        band1 = src.read(1)
        band1_normalised = normalise(band1)
        plt.figure(figsize=(10, 10))

        plt.imshow(band1_normalised, cmap='Greens')
        plt.scatter([col], [row], color='red', s=50)
        plt.title('Raster Display with Specified UTM Location')
        plt.show()




def main():
    script_directory = ('models/03-real-fuels')
    tif_file_pattern = os.path.join(script_directory, 'outputs', 'time_of_arrival*.tif')
    tif_file_path = get_first_matching_file(tif_file_pattern)
    base_raster_path = 'models/04-fire-potential/outputs/head_fire_spread_rate_006.tif'
    overlay_raster_path = tif_file_path
    file_path = 'out/weather_info.txt'  
    longitude, latitude = readcenterinfo(file_path) 
    print(longitude, latitude)
    utm_x, utm_y = convert_lat_lon_to_utm(longitude, latitude)
    overlay_raster_at_point(base_raster_path, overlay_raster_path)
    # display_location_on_raster_utm(base_raster_path, utm_x, utm_y)
if __name__ == "__main__":
    main()