# ECOSTRESS Swath to Grid Conversion Script
---
# Objective:
The ECOSTRESS_swath2grid.py script converts ECOSTRESS swath data products, stored in Hierarchical Data Format version 5 (HDF5, .h5) into projected GeoTIFFs. When executing this script, a user will submit a desired output projection and input directory containing ECOSTRESS swath data products as command line arguments. The script begins by opening any of the ECOSTRESS products listed below that are contained in the input directory. Next, it uses the latitude and longitude arrays from the ECO1BGEO product (except for L3/L4 ALEXI_USDA and ECO1BMAPRAD products) to resample the swath dataset to a grid using nearest neighbor resampling (`Pyresample/kdtree`). Note that you will need to download the ECO1BGEO files that correspond to your higher level product files. From there, the script defines the coordinate reference system (CRS) input by the user (options include UTM Zones and Geographic (EPSG:4326)). There is an optional argument to override the default UTM zone selected by the script (see below) if needed. Ultimately, the script exports the gridded array as a GeoTIFF (`GDAL`). By default, the script will loop through and perform the aforementioned steps for each science dataset (SDS) in the HDF5 file. There is an optional argument that allows you to select a subset of SDS layers within a given product (see details below). The resulting GeoTIFF files can be imported with spatial reference into GIS and Remote Sensing software programs. The script also will batch process all ECOSTRESS swath files contained in the input directory provided. For ECOSTRESS products that include a scale factor in the metadata, the output will be scaled, and for products that include a fill value in the file metadata, this will be carried over into the GeoTIFF outputs. For layers that do not contain a fill value in the file metadata, the fill value will be defined as the highest possible value for the given datatype of an SDS.
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

#### Note that you will need to separately download the ECO1BGEO files that correspond to the files you have downloaded for products 2-4, 6-8, and 10 above.
---
# Prerequisites:
*Disclaimer: Script has been tested on Windows and MacOS using the specifications identified below.*  
+ #### Python version 3.6  
  + `GDAL`
  + `h5py`
  + `pyproj`
  + `pyresample`
  + `numpy`      
  + For a complete list of required packages, check out `windowsOS.yml` (Windows users) or `macOS.yml` (MacOS users).  
---
# Procedures:
## Getting Started:
> #### 1.	Download ECOSTRESS higher level products and corresponding ECO1BGEO files (ordered separately) from the [LP DAAC Data Pool](https://e4ftl01.cr.usgs.gov/) or [Earthdata Search Client](http://search.earthdata.nasa.gov) to a local directory (see above for applicable products)
> #### 2.	Copy/clone/download  [ECOSTRESS_swath2grid.py](https://git.earthdata.nasa.gov/projects/LPDUR/repos/ecostress_swath2grid/browse/ECOSTRESS_swath2grid.py) from LP DAAC Data User Resources Repository   
## Python Environment Setup
> #### 1. It is recommended to use [Conda](https://conda.io/docs/), an environment manager to set up a compatible Python environment. Download Conda for your OS here: https://www.anaconda.com/download/. Once you have Conda installed, Follow the instructions below to successfully setup a Python environment on MacOS or Windows.
> #### 2. Windows Setup
> 1.  Download the [WindowsEnvironment.zip](https://git.earthdata.nasa.gov/projects/LPDUR/repos/ecostress_swath2grid/raw/WindowsEnvironment.zip?at=refs%2Fheads%2Fmaster) file from the repository, and unzip the contents of file into a local directory.
> 2. Open the `windowsOS.yml` file with your favorite text editor, change the prefix to match the location of Anaconda on your OS, and save the file.  
  > 2a. Ex: `C:\Username\Anaconda3\envs\ecostress` --replace 'Username' with the location of your Conda installation (leave `Anaconda3\envs\ecostress`)  
  > 2b. Tip: search for the location of Conda on your OS by opening the Command Prompt and typing `dir Anaconda3 /AD /s`
> 3. Navigate to the unzipped directory in your Command Prompt, and type `conda env create -f windowsOS.yml`
> 4. Navigate to the directory where you downloaded the `ECOSTRESS_swath2grid.py` script
> 5. Activate ECOSTRESS Python environment (created in step 3) in the Command Prompt  
  > 1. Type  `activate ecostress`  
> #### 3. MacOS Setup
> 1.  Download the [macOS.yml](https://git.earthdata.nasa.gov/projects/LPDUR/repos/ecostress_swath2grid/browse/macOS.yml) file from the repository.
> 2. Open the `macOS.yml` file with your favorite text editor, change the prefix to match the location of Anaconda on your OS, and save the file.  
  > 2a. Ex: `/anaconda3/envs/ecostress` if you downloaded conda under a local user directory, add `/Users/<insert username>` before `anaconda3` (leave `Anaconda3/envs/ecostress`)  
  > 2b. Tip: search for the location of Conda on your OS by opening the terminal and typing `which anaconda`
> 3. Navigate to the directory containing the `macOS.yml` file in your Command Prompt, and type `conda env create -f macOS.yml`
> 4. Navigate to the directory where you downloaded the `ECOSTRESS_swath2grid.py` script
> 5. Activate ECOSTRESS Python environment (created in step 3) in the Command Prompt   
    > 5a. Type `source activate ecostress`  

[Additional information](https://conda.io/docs/user-guide/tasks/manage-environments.html) on setting up and managing Conda environments.
## Script Execution
> #### 1.	Once you have set up your MacOS/Windows environment and it has been activated, run the script with the following in your Command Prompt/terminal window:
  > 1.  `python ECOSTRESS_swath2grid.py --proj <insert reprojection desired, Options: GEO and UTM> --dir <insert input directory with ECOSTRESS files here> --geodir <insert input directory with ECOSTRESS L1B_GEO files here>`  
    > 1a. GEO = Geographic lat/lon, EPSG code 4326  
    >1b. UTM = Universal Transverse Mercator Zones (north/south) with WGS84 datum
  > 2. Ex:   `python ECOSTRESS_swath2grid.py --proj GEO --dir C:\Users\ECOSTRESS\ --geodir C:\Users\ECOSTRESS\L1B_GEO\`
  > 3. If UTM is selected, the script will calculate the UTM zone by using the location of the center of each ECOSTRESS granule. If you prefer to set the UTM zone manually, you can do so by adding the optional argument `--utmzone <insert EPSG code for desired zone>`. This optional argument will override the default functionality for users who desire all ECOSTRESS granules to be in a common UTM projection, regardless of the center location of the granule.   
    > 3a. Ex: `python ECOSTRESS_swath2grid.py --proj UTM --dir <insert input directory with ECOSTRESS files here> --geodir <insert input directory with ECOSTRESS L1B_GEO files here> --utmzone <insert EPSG code for desired UTM zone, i.e. 32610>`   
    > 3b. You can look up EPSG codes for UTM zones at: http://spatialreference.org/, note that only WGS84 datum is supported, and thus EPSG codes for UTM north zones will begin with `326` and utm south zones with `327`
  > 4. The default functionality is to export each science dataset (SDS) layer contained in an ECOSTRESS product as a GeoTIFF. If you prefer to only export one or more layers, you can do so by adding the optional argument `--sds <insert SDS layer names desired>` (comma separated with no spaces,see below for specific SDS layer names by product)
    > 4a. Ex: `python ECOSTRESS_swath2grid.py --proj GEO --dir C:\Users\ECOSTRESS --geodir C:\Users\ECOSTRESS\L1B_GEO --sds LST,QC,Emis1`
    > 4b. See below for specific SDS layer names by product.
## Subsetting Layers:
To use the `--sds` optional command line argument in order to select a subset of science datasets from an ECOSTRESS granule, you will need to submit 1 or more SDS layers names into the `--sds ` argument exactly as they appear in the list below.
> Example for a single layer: `--sds LST`
> Example for multiple layers: `--sds ETcanopy,ETdaily,ETinst` **(make sure the SDS layers are comma separated, with no spaces between SDS!)**
**1.	ECO1BMAPRAD**  
  -	data_quality_1  
  -	data_quality_2  
  -	data_quality_3  
  -	data_quality_4  
  -	data_quality_5  
  -	height  
  -	latitude  
  -	longitude  
  -	radiance_1  
  -	radiance_2  
  -	radiance_3  
  -	radiance_4  
  -	radiance_5  
  -	solar_azimuth  
  -	solar_zenith  
  -	swir_dn  
  -	view_azimuth  
  -	view_zenith    

**2.	ECO1BRAD**  
  -	data_quality_1  
  -	data_quality_2  
  -	data_quality_3  
  -	data_quality_4  
  -	data_quality_5  
  -	radiance_1  
  -	radiance_2  
  -	radiance_3  
  -	radiance_4  
  -	radiance_5  
  -	swir_dn  

**3.	ECO2CLD**  
  -	CloudMask  

**4.	ECO2LSTE**  
  -	Emis1  
  -	Emis1_err  
  -	Emis2  
  -	Emis2_err  
  -	Emis3  
  -	Emis3_err  
  -	Emis4  
  -	Emis4_err  
  -	Emis5  
  -	Emis5_err  
  -	EmisWB  
  -	LST  
  -	LST_err  
  -	PWV  
  -	QC  

**5.	ECO3_ET_ALEXI_USDA**  
  -	ETdaily  
  -	ETdailyUncertainty  
  -	QualityFlag  

**6.	ECO3ETPTJPL**  
  -	ETcanopy  
  -	ETdaily  
  -	ETinst  
  -	ETinstUncertainty  
  -	ETinterception  
  -	ETsoil  

**7.	ECO3ANCQA**  
  -	COT_QC  
  -	GPP_QC  
  -	LST_QC  
  -	aerosol_optical_depth_QC  
  -	air_temperature_rs_QC  
  -	albedo_landsat_QC  
  -	black_sky_albedo_QC  
  -	cloud_fraction_QC  
  -	cloud_height_QC  
  -	cloud_mask_QC  
  -	dewpoint_rs_QC  
  -	emissivity_QC  
  -	ice_mask_QC  
  -	landcover_QC  
  -	ndvi_landsat8_QC  
  -	ndvi_mod13_QC  
  -	snow_mask_QC  
  -	surface_pressure_QC  
  -	surface_pressure_fill_QC  
  -	water_mask_QC  
  -	white_sky_albedo_QC  

**8.	ECO4_ESI_ALEXI_USDA**  
  -	ESIdaily  
  -	ESIdailyUncertainty  
  -	QualityFlag  

**9.	ECO4ESIPTJPL**  
  -	ESIavg  
  -	PET  

**10.	ECO4WUE**  
  -	WUEavg  

## Changing Resampling/Interpolation Methods:
(Experimental)
Use the --r option to select one of the following resampling methods. If no method is selected, it will default to the nearest nehighbor (kdtree) method:
  - `kdtnn`
  - `gauss`
  - `bilinear`
  - `none`

---
# Contact Information:
#### Author: Cole Krehbiel¹   
**Contact:** LPDAAC@usgs.gov  
**Voice:** +1-866-573-3222  
**Organization:** Land Processes Distributed Active Archive Center (LP DAAC)  
**Website:** https://lpdaac.usgs.gov/  
**Date last modified:** 10-29-2018  

¹Innovate!, Inc., contractor to the U.S. Geological Survey, Earth Resources Observation and Science (EROS) Center,  
 Sioux Falls, South Dakota, USA. Work performed under USGS contract G15PD00467 for LP DAAC².  
²LP DAAC Work performed under NASA contract NNG14HH33I.
