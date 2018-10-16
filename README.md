# ECOSTRESS Swath to Grid Conversion Script
---
# Objective:
The ECOSTRESS_Georeference.py script converts ECOSTRESS swath data products, stored in Hierarchical Data Format version 5 (HDF5, .h5) into projected GeoTIFFs. When executing this script, a user will submit a desired output projection and input directory containing ECOSTRESS swath data products as command line arguments. The script begins by opening any of the ECOSTRESS products listed below that are contained in the input directory. Next, it uses the latitude and longitude arrays from the ECOSTRESS L1GEO product (except for L3/L4 ALEXI_USDA and ECO1BMAPRAD) to resample the swath dataset to a grid using nearest neighbor resampling (`Pyresample/kdtree`). From there, the script defines the coordinate reference system (CRS) input by the user (options include UTM Zones and Geographic (EPSG:4326)). Ultimately, the script exports the gridded array as a GeoTIFF (`GDAL`). The script will loop through and perform the aforementioned steps for each science dataset (SDS) in the HDF5 file. The resulting GeoTIFF files can be downloaded with spatial reference into GIS and Remote Sensing software programs. The script also will batch process all ECOSTRESS swath files contained in the input directory provided. For ECOSTRESS products that include a scale factor in the metadata, the output will be scaled, and for products that include a fill value in the file metadata, this will be carried over into the GeoTIFF outputs. For layers that do not contain a fill value in the file metadata, the fill value will be defined as the highest possible value for the given datatype of an SDS.
## Available Products:
    0. ECO1BGEO (Latitude and Longitude arrays are needed for swath to grid conversion)
    1. ECO1BMAPRAD (lat/lon arrays contained within; ECO1BGEO not needed)  
    2. ECO1BRAD  
    3. ECO2CLD  
    4. ECO2LSTE  
    5. ECO3_ET_ALEXI_USDA (30 m, in UTM Projection; ECO1BGEO not needed)  
    6. ECO3ETPTJPL  
    7. ECO3ANCQA  
    8. ECO4ESIPTJPL  
    9. ECO4_ESI_ALEXI_USDA  (30 m, in UTM Projection; ECO1BGEO not needed)  
    10. ECO4WUE
---
# Prerequisites:
*Disclaimer: Script has been tested on Windows and MacOS using the specifications identified below.*  
+ #### Python version 3.6  
  + `GDAL`
  + `h5py`
  + `pyproj`
  + `math`
  + `pyresample`
  + `numpy`      

For a complete list of required packages, check out `windowsOS.yml` (Windows users) or `macOS.yml` (MacOS users).
---
# Procedures:
> #### 1.	Copy/clone ECOSTRESS_Georeference.py from LP DAAC Data User Resources Repository  
> #### 2.	Download ECOSTRESS data and corresponding ECO1BGEO files from the LP DAAC to a local directory (see above for applicable products)  
> #### 3. Set up a Python environment on your OS (recommended to use yml file for your OS available from the LP DAAC User Resources Repository)
> #### 4.	Open a Command Prompt/terminal window and navigate to the directory where you downloaded the ECOSTRESS_Georeference.py script  
> #### 5.	Activate ECOSTRESS Python environment (created in step 3) in the Command Prompt/terminal window  
  > 1.  `activate <python environment name>`
> #### 6.	Once activated, run the script with the following in your Command Prompt/terminal window:
  > 1.  `python ECOSTRESS_Georeference.py <insert reprojection desired. Options: 'GEO' and 'UTM'> <insert input directory with ECOSTRESS files here>`
  > 2. Ex:   `python ECOSTRESS_Georeference.py GEO C:/users/johndoe/ASTERL1T/`
---
# Contact Information:
#### Author: Cole Krehbiel¹   
**Contact:** LPDAAC@usgs.gov  
**Voice:** +1-866-573-3222  
**Organization:** Land Processes Distributed Active Archive Center (LP DAAC)  
**Website:** https://lpdaac.usgs.gov/  
**Date last modified:** 10-16-2018  

¹Innovate!, Inc., contractor to the U.S. Geological Survey, Earth Resources Observation and Science (EROS) Center,  
 Sioux Falls, South Dakota, USA. Work performed under USGS contract G15PD00467 for LP DAAC².  
²LP DAAC Work performed under NASA contract NNG14HH33I.
