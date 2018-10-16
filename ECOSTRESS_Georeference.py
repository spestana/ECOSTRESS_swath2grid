# -*- coding: utf-8 -*-
"""
Script to Georeference ECOSTRESS Products
Author: Cole Krehbiel
Last Updated: 9/21/2018
Products Tested:
    1. L1B_MAP
    2. L1B_RAD 
    3. L2_CLOUD
    4. L2_LSTE
    5. L3_ET_ALEXI_USDA
    6. L3_ET_PT-JPL
    7. L3_L4_QA
    8. L4_ESI_PT-JPL
    9. L4_ESI_ALEXI_USDA
    10. L4_WUE

Completed Tasks:
1. Add functionality for L1B_MAP
2. Add functionality for ALEXI Products
3. Add support for Geographic (Calculate Pixel Size)
4. Add support for UTM (Determine Zone)
5. Wrap into command line executable
6. Added ability to scale data 

Outstanding Issues/Questions/Tasks:
    1. How to handle datasets with no fill value?
    3. Add more error handling
    4. Identical outputs with ecostress_reprojection_tool


-------------------------------------------------------------------------------
 PROCEDURES:
 1.	Copy/clone ECOSTRESS_Georeference.py from LP DAAC Data User Resources Repository
 2.	Download ECOSTRESS data and corresponding L1BGEO files from the LP DAAC to
   a local directory (see above for applicable products)
 3.	Open a Command Prompt/terminal window and navigate to the directory where 
     you downloaded the ECOSTRESS_Georeference.py script
 4.	Activate python in the Command Prompt/terminal window
     1.  > activate [python environment name]
 5.	Once activated, run the script with the following in your Command Prompt:
     1.  > python ECOSTRESS_Georeference.py [insert input dir with ECOSTRESS files here]
             1.	Example of input directory: C:/users/johndoe/ASTERL1T/
-------------------------------------------------------------------------------
"""
# Load necessary packages into Python
import h5py, os, pyproj, sys, getopt, argparse, math
import numpy as np
from pyresample import geometry as geom
from pyresample import kd_tree as kdt
from osgeo import gdal, gdal_array, gdalconst, osr
#------------------------------------------------------------------------------
# Define Script and handle errors
def main(argv):
    parser = argparse.ArgumentParser()
    try:
        opts, args = getopt.getopt(argv,"hi:", ["output_projection","input_directory"])   
        if len(sys.argv[1:]) == 0:
            class MyParser(argparse.ArgumentParser):
                def error(self, message):
                    sys.stderr.write('error: %s\n' % message)
                    self.print_help()
                    sys.exit(2)
            parser = MyParser()
            parser.add_argument('output_projection', nargs='+')
            parser.add_argument('input_directory', nargs='+')
        elif sys.argv[1] == '-h':
            print('ECOSTRESS_Georeference.py <output_projection> <input_directory>')
            sys.exit()
        elif "'" in sys.argv[2] or '"' in sys.argv[1]:
            parser.error('Do not include quotes in input directory argument')
        elif len(sys.argv) < 2:
            parser.error('2 Arguments are needed (output_projection, input_directory)')
        elif sys.argv[2][-1] != '/' and sys.argv[2][-1] != '\\':
            parser.error('Please end your directory location with / or \\')
        elif sys.argv[1] != 'UTM' and sys.argv[1] != 'GEO':
            parser.error("output projection options include 'UTM' and 'GEO'")
    except getopt.GetoptError:
        print('error: Invalid option passed as argument')      
        print('ECOSTRESS_Georeference.py <output_projection> <input_directory>')
        sys.exit(2)
    try:
        os.chdir(sys.argv[2])
    except FileNotFoundError:
        print('error: input_directory provided does not exist or was not found')
        sys.exit(2)
#-----------------------SET ARGUMENTS TO VARIABLES-----------------------------
    # Set input/current working directory from user defined argument
    inDir = sys.argv[2] # inDir = 'D:/Sci_Int/Tutorials/ECOSTRESS/' 
    os.chdir(inDir)
    crsIN = sys.argv[1] # crsIN = ['UTM','GEO']

#----------------------SET UP WORKSPACE----------------------------------------
    # Create and set output directory
    outDir = os.path.normpath((os.path.split(inDir)[0] + os.sep + 'output'))+ os.sep
    if not os.path.exists(outDir):os.makedirs(outDir)
                
    # Create a list of ECOSTRESS HDF-EOS5 files in the directory
    geoList = [f for f in os.listdir() if f.endswith('.h5') and 'GEO' in f] # Geo Files
    ecoList = [f for f in os.listdir() if f.endswith('.h5') and 'GEO' not in f] # ECOSTRESS Files    
#----------------------DEFINE FUNCTIONS----------------------------------------
    # Write function to determine which UTM zone to use:
    def utmLookup(lat, lon):
        utm = str((math.floor((lon + 180) / 6 ) % 60) + 1)
        if len(utm) == 1:
            utm = '0' + utm
        if lat >= 0:
            epsg_code = '326' + utm
        else:
            epsg_code = '327' + utm
        return epsg_code
#-------------------------GEOREFERENCING---------------------------------------    
    # Batch process all files in the input directory
    i = 0
    for e in ecoList:
#------------------------IMPORT ECOSTRESS FILE---------------------------------
        i += 1
        print('Processing: {} ({} of {})'.format(e, str(i), str(len(ecoList))))
        f = h5py.File(e)         # Read in the ECOSTRESS Data HDF-EOS5 file
        ecoName = e.rsplit('\\')[-1].split('.h5')[0]  # Keep original filename
        eco_objs = []            
        f.visit(eco_objs.append) # Retrieve list of datasets  

        # Search for relevant SDS inside data file
        ecoSDS = [str(o) for o in eco_objs if isinstance(f[o],h5py.Dataset)] 
#--------------------------CONVERT SWATH DATA TO GRID--------------------------    
        # ALEXI products are already georeferenced, bypass section below
        if 'ALEXI_USDA' in e: 
            cols = 3000
            rows = 3000
        else:
#------------------------IMPORT GEOLOCATION FILE-------------------------------
            geo = [g for g in geoList if e[-37:] in g] # Use subset name to match GEO file
            if 'L1B_MAP' in e: geo = 'T'               # L1B Map contains lat/lon arrays
            if len(geo) != 0:                          # Only proceed if GEO file found
                if 'L1B_MAP' not in e:
                    g = h5py.File(geo[0])    # Read in the ECOSTRESS GEO HDF-EOS5 file
                    geo_objs = []
                    g.visit(geo_objs.append)
                    latSD = [str(o) for o in geo_objs if isinstance(g[o],h5py.Dataset) and 'Geolocation/latitude' in o]
                    lonSD = [str(o) for o in geo_objs if isinstance(g[o],h5py.Dataset) and 'Geolocation/longitude' in o]
                else: # L1BMAP has different naming
                    g = f 
                    latSD = [str(o) for o in eco_objs if isinstance(g[o],h5py.Dataset) and 'Mapped/latitude' in o]
                    lonSD = [str(o) for o in eco_objs if isinstance(g[o],h5py.Dataset) and 'Mapped/longitude' in o] 
                
                lat = g[latSD[0]].value.astype(np.float) # Open Lat array
                lon = g[lonSD[0]].value.astype(np.float) # Open Lon array
#-----------------------SWATH TO GEOREFERENCED ARRAYS--------------------------               
                swathDef = geom.SwathDefinition(lons=lon, lats=lat)
                datum = 'WGS84'
                mid = [int(lat.shape[1]/2)-1, int(lat.shape[0]/2)-1]
                midLat, midLon = lat[mid[0]][mid[1]], lon[mid[0]][mid[1]]
                
                if crsIN == 'UTM':
                    # Determine UTM zone that majority of scene lies in
                    epsg = utmLookup(midLat, midLon)
                    epsgConvert = pyproj.Proj("+init=EPSG:{}".format(epsg))
                    proj, projName = 'utm', 'Universal Transverse Mercator'
                    llLon, llLat = epsgConvert(np.min(lon), np.min(lat), inverse=False)
                    urLon, urLat = epsgConvert(np.max(lon), np.max(lat), inverse=False)                    
                    ps = 70
                    projDict = {'proj': proj,'zone':epsg[-2:],'ellps': datum, 'datum': datum, 'units': 'm'}
                    # Add 'south' for southern hemisphere UTM zones
                    if epsg[2] == '7':
                        projDict['south'] = 'True'
                    areaExtent = (llLon, llLat, urLon, urLat)
                    cols = int((areaExtent[2] - areaExtent[0])/ps) 
                    rows = int((areaExtent[3] - areaExtent[1])/ps) 
                    
                if crsIN == 'GEO':   
                    # Use info from aeqd bbox to calculate output cols/rows/pixel size
                    epsgConvert = pyproj.Proj("+proj=aeqd +lat_0={} +lon_0={}".format(midLat, midLon)) 
                    llLon, llLat = epsgConvert(np.min(lon), np.min(lat), inverse=False)
                    urLon, urLat = epsgConvert(np.max(lon), np.max(lat), inverse=False)
                    ps = 70 # Meters
                    areaExtent = (llLon, llLat, urLon, urLat)
                    cols = int(round((areaExtent[2] - areaExtent[0])/ps)) 
                    rows = int(round((areaExtent[3] - areaExtent[1])/ps)) 
                    '''Use no. rows and columns generated above from the aeqd projection 
                    to set a representative number of rows and columns, which will then be translated
                    to degrees below, then take the smaller of the two pixel dims to determine output size'''
                    epsg, proj, projName = '4326', 'longlat', 'Geographic' 
                    llLon, llLat, urLon, urLat = np.min(lon), np.min(lat), np.max(lon), np.max(lat)
                    areaExtent = (llLon, llLat, urLon, urLat)
                    projDict = {'proj': proj,'datum': datum, 'units': 'degree'}
                    areaDef = geom.AreaDefinition(epsg, projName, proj, projDict, cols, rows, areaExtent)
                    ps = np.min([areaDef.pixel_size_x, areaDef.pixel_size_y]) 
                    # Calculate the output cols and rows after squaring pixels
                    cols = int(round((areaExtent[2] - areaExtent[0])/ps)) 
                    rows = int(round((areaExtent[3] - areaExtent[1])/ps))                     
                    
                areaDef = geom.AreaDefinition(epsg, projName, proj, projDict, cols, rows, areaExtent)
                index, outdex, indexArr, distArr = kdt.get_neighbour_info(swathDef, areaDef, 210, neighbours=1)
#-----------------------LOOP THROUGH SDS AND APPLY GEOREFERENCING--------------
        for s in ecoSDS: 
            if len(f[s].shape) > 1:  # Omit NA layers/objs
                if f[s].shape[0] > 1 and f[s].shape[1] > 1:  # Omit NA layers/objs
                    ecoSD = f[s].value # Create array and read dimensions            
                    # Try and read SDS Attributes, some products missing...
                    try:
                        fv = int(f[s].attrs['_FillValue'])
                    except KeyError:
                        fv = None
                    except ValueError:
                        fv = f[s].attrs['_FillValue'][0]
                    try:
                        sf = f[s].attrs['_Scale'][0]
                    except:
                        sf = 1                    
                    if 'ALEXI_USDA' in e:  # gather georeferencing info from file metadata
                        sdGEO = ecoSD * sf
                        if 'ET' in e:
                            metaName = 'L3_ET_ALEXI Metadata'
                        else:
                            metaName = 'L4_ESI_ALEXI Metadata'
                        gt = f['{}/Geotransform'.format(metaName)].value
                        proj = f['{}/OGC_Well_Known_Text'.format(metaName)].value.decode('UTF-8')
                    else:
                        try:
                            # Perform kdtree resampling 
                            sdGEO = kdt.get_sample_from_neighbour_info('nn', areaDef.shape, ecoSD ,index, outdex, indexArr, fill_value=fv)
                            if sf != 1:
                                sdGEO = sdGEO*sf
                                sdGEO[sdGEO == fv*sf] = fv                            
                            ps = np.min([areaDef.pixel_size_x, areaDef.pixel_size_y]) 
                            gt = [areaDef.area_extent[0],ps,0,areaDef.area_extent[3],0,-ps]
                        except ValueError:
                            continue             
#-----------------------------EXPORT GEOTIFFS----------------------------------                    
                    if 'ALEXI_USDA' in e and crsIN == 'GEO': # For this case, export to UTM, then convert to GEO
                        tempName = '{}{}_{}_{}.tif'.format(outDir,ecoName,s.rsplit('/')[-1], 'TEMP')
                        outName = tempName
                    else:
                    # Export the result as GeoTIFF
                        outName = '{}{}_{}_{}.tif'.format(outDir,ecoName,s.rsplit('/')[-1], crsIN)
                    
                    driv =  gdal.GetDriverByName('GTiff')
                    height, width = sdGEO.shape  # define geotiff dimensions, array 
        
                    # create dataset writer, specify dimensions, define and set output geotransform
                    dataType = gdal_array.NumericTypeCodeToGDALTypeCode(sdGEO.dtype)
                    d = driv.Create(outName, width, height, 1, dataType)
                    d.SetGeoTransform(gt)
                     
                    # create and set output projection, write output array data
                    if 'ALEXI_USDA' in e: d.SetProjection(proj)
                    else:
                        # Define target SRS
                        srs = osr.SpatialReference()
                        srs.ImportFromEPSG(int(epsg))
                        d.SetProjection(srs.ExportToWkt())
                    band = d.GetRasterBand(1)                                                 
                    band.WriteArray(sdGEO)  
                    # Define fill value if it exists, if not--set to mask fill value 
                    if fv != None and fv != 'NaN': 
                        band.SetNoDataValue(fv)
                    else:
                        try:
                            band.SetNoDataValue(sdGEO.fill_value)     
                        except AttributeError:
                            pass
                    band.FlushCache()       
                    d, band = None, None
    
                    if 'ALEXI_USDA' in e and crsIN == 'GEO':
                        # Define target SRS
                        epsg = '4326'                 
                        srs = osr.SpatialReference()
                        srs.ImportFromEPSG(int(epsg))
                        srs = srs.ExportToWkt()
    
                        # Open temp file, get default vals for target dims and geotransform
                        dd = gdal.Open(tempName, gdalconst.GA_ReadOnly)
                        vrt = gdal.AutoCreateWarpedVRT( dd, None, srs, gdal.GRA_NearestNeighbour, 0.125)
                        
                        # Create the final warped raster
                        outName = '{}{}_{}_{}.tif'.format(outDir,ecoName,s.rsplit('/')[-1], crsIN)
                        d = driv.CreateCopy(outName, vrt)
                        dd, d, vrt = None, None, None
                        os.remove(tempName)

if __name__ == "__main__":
   main(sys.argv[1:])    