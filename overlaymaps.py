import rasterio
import matplotlib.pyplot as plt
from rasterio.plot import show
from pyproj import Transformer
import numpy as np
import os
import glob
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling

def reproject_raster(input_raster_path, output_raster_path, target_crs):
    with rasterio.open(input_raster_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, target_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': target_crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        with rasterio.open(output_raster_path, 'w', **kwargs) as dst:
            for band in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, band),
                    destination=rasterio.band(dst, band),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=target_crs,
                    resampling=Resampling.nearest)

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



def overlay_raster_at_point(base_raster_path, overlay_raster_path, zoom_scale=0.1):
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

def check_crs(raster_path):
        with rasterio.open(raster_path) as src:
            return src.crs



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
    # display_location_on_raster_utm(base_raster_path, utm_x, utm_y)
if __name__ == "__main__":
    main()