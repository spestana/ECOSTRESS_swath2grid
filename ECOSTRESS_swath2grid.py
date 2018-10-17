# -*- coding: utf-8 -*-
"""
-------------------------------------------------------------------------------
ECOSTRESS Swath to Grid Conversion Script
Author: Cole Krehbiel
Last Updated: 10/17/2018
See README for additional information: 
https://git.earthdata.nasa.gov/projects/LPDUR/repos/ecostress_swath2grid/browse
-------------------------------------------------------------------------------
"""
# Load necessary packages into Python
import h5py, os, pyproj, sys, getopt, argparse, math
import numpy as np
from pyresample import geometry as geom
from pyresample import kd_tree as kdt
from osgeo import gdal, gdal_array, gdalconst, osr

#-----------------COMMAND LINE ARGUMENTS AND ERROR HANDLING-------------------#
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
            print('ECOSTRESS_swath2grid.py <output_projection> <input_directory>')
            sys.exit()
        elif "'" in sys.argv[2] or '"' in sys.argv[1]:
            parser.error('Do not include quotes in input directory argument')
        elif len(sys.argv) < 2:
            parser.error('2 Arguments are needed: <output_projection> <input_directory>')
        elif sys.argv[1] != 'UTM' and sys.argv[1] != 'GEO':
            parser.error("output projection options include UTM and GEO")
    except getopt.GetoptError:
        print('error: Invalid option passed as argument')      
        print('ECOSTRESS_swath2grid.py <output_projection> <input_directory>')
        sys.exit(2)
    try:
        os.chdir(sys.argv[2])
    except FileNotFoundError:
        print('error: input_directory provided does not exist or was not found')
        sys.exit(2)
        
#-----------------------SET ARGUMENTS TO VARIABLES----------------------------#
    if sys.argv[2][-1] != '/' and sys.argv[2][-1] != '\\': 
        inDir = sys.argv[2] + os.sep
    else: 
        inDir = sys.argv[2] # Set input/working directory from user-defined arg
    os.chdir(inDir)
    crsIN = sys.argv[1] # Options include 'UTM' or 'GEO'
    
#----------------------SET UP WORKSPACE---------------------------------------#
    # Create and set output directory
    outDir = os.path.normpath((os.path.split(inDir)[0] + os.sep + 'output'))+ os.sep
    if not os.path.exists(outDir): os.makedirs(outDir)
                
    # Create lists of ECOSTRESS HDF-EOS5 files (geo, data) in the directory
    geoList = [f for f in os.listdir() if f.endswith('.h5') and 'GEO' in f]
    ecoList = [f for f in os.listdir() if f.endswith('.h5') and 'GEO' not in f]   
    
#----------------------DEFINE FUNCTIONS---------------------------------------#
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
    
#------------------------IMPORT ECOSTRESS FILE--------------------------------# 
    # Batch process all files in the input directory
    i = 0
    for e in ecoList:
        i += 1
        print('Processing: {} ({} of {})'.format(e, str(i), str(len(ecoList))))
        f = h5py.File(e)            # Read in ECOSTRESS HDF5-EOS data file
        ecoName = e.split('.h5')[0] # Keep original filename
        eco_objs = []            
        f.visit(eco_objs.append)    # Retrieve list of datasets  

        # Search for relevant SDS inside data file
        ecoSDS = [str(o) for o in eco_objs if isinstance(f[o],h5py.Dataset)] 
        
#--------------------------CONVERT SWATH DATA TO GRID-------------------------#  
        if 'ALEXI_USDA' in e: # ALEXI products already gridded, bypass below
            cols, rows, dims = 3000, 3000, (3000,3000)
        else:
#------------------------IMPORT GEOLOCATION FILE------------------------------#
            geo = [g for g in geoList if e[-37:] in g] # Match GEO filename
            if len(geo) != 0 or 'L1B_MAP' in e:        # Proceed if GEO/MAP file
                if 'L1B_MAP' in e: g = f               # Map file contains lat/lon
                else: g = h5py.File(geo[0])            # Read in GEO file
                geo_objs = []
                g.visit(geo_objs.append)
                
                # Search for relevant SDS inside data file
                latSD = [str(o) for o in geo_objs if isinstance(g[o],h5py.Dataset) and '/latitude' in o]
                lonSD = [str(o) for o in geo_objs if isinstance(g[o],h5py.Dataset) and '/longitude' in o]
                lat = g[latSD[0]].value.astype(np.float) # Open Lat array
                lon = g[lonSD[0]].value.astype(np.float) # Open Lon array
                dims = lat.shape
                
#-----------------------SWATH TO GEOREFERENCED ARRAYS-------------------------#               
                swathDef = geom.SwathDefinition(lons=lon, lats=lat)
                mid = [int(lat.shape[1]/2)-1, int(lat.shape[0]/2)-1]
                midLat, midLon = lat[mid[0]][mid[1]], lon[mid[0]][mid[1]]    
                
                if crsIN == 'UTM':
                    epsg = utmLookup(midLat, midLon) # Determine UTM zone that center of scene is in
                    epsgConvert = pyproj.Proj("+init=EPSG:{}".format(epsg))
                    proj, pName = 'utm', 'Universal Transverse Mercator'
                    projDict = {'proj': proj,'zone':epsg[-2:],'ellps': 'WGS84', 'datum': 'WGS84', 'units': 'm'}
                    if epsg[2] == '7': projDict['south'] = 'True' # Add for s. hemisphere UTM zones
                    llLon, llLat = epsgConvert(np.min(lon), np.min(lat), inverse=False)
                    urLon, urLat = epsgConvert(np.max(lon), np.max(lat), inverse=False)                    
                    areaExtent = (llLon, llLat, urLon, urLat)
                    ps = 70 # 70 is pixel size (meters)
                    
                if crsIN == 'GEO':   
                    # Use info from aeqd bbox to calculate output cols/rows/pixel size
                    epsgConvert = pyproj.Proj("+proj=aeqd +lat_0={} +lon_0={}".format(midLat, midLon)) 
                    llLon, llLat = epsgConvert(np.min(lon), np.min(lat), inverse=False)
                    urLon, urLat = epsgConvert(np.max(lon), np.max(lat), inverse=False)
                    areaExtent = (llLon, llLat, urLon, urLat)
                    cols = int(round((areaExtent[2] - areaExtent[0])/70)) # 70 m pixel size
                    rows = int(round((areaExtent[3] - areaExtent[1])/70)) 
                    '''Use no. rows and columns generated above from the aeqd projection 
                    to set a representative number of rows and columns, which will then be translated
                    to degrees below, then take the smaller of the two pixel dims to determine output size'''
                    epsg, proj, pName = '4326', 'longlat', 'Geographic' 
                    llLon, llLat, urLon, urLat = np.min(lon), np.min(lat), np.max(lon), np.max(lat)
                    areaExtent = (llLon, llLat, urLon, urLat)
                    projDict = {'proj': proj,'datum': 'WGS84', 'units': 'degree'}
                    areaDef = geom.AreaDefinition(epsg, pName, proj, projDict, cols, rows, areaExtent)
                    ps = np.min([areaDef.pixel_size_x, areaDef.pixel_size_y])  # Square pixels 
                    
                cols = int(round((areaExtent[2] - areaExtent[0])/ps)) # Calculate the output cols
                rows = int(round((areaExtent[3] - areaExtent[1])/ps)) # Calculate the output rows                    
                areaDef = geom.AreaDefinition(epsg, pName, proj, projDict, cols, rows, areaExtent)
                index, outdex, indexArr, distArr = kdt.get_neighbour_info(swathDef, areaDef, 210, neighbours=1)
            else:
                print('ECO1BGEO File not found for {}'.format(e))
                
#--------LOOP THROUGH SDS CONVERT SWATH2GRID AND APPLY GEOREFERENCING---------#
        for s in ecoSDS: 
            if f[s].shape == dims: # Omit NA layers/objs
                ecoSD = f[s].value # Create array and read dimensions            
                
                # Read SDS Attributes if available
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
                    
                if 'ALEXI_USDA' in e:  # USDA Contains proj info in metadata
                    if 'ET' in e: metaName = 'L3_ET_ALEXI Metadata'
                    else: metaName = 'L4_ESI_ALEXI Metadata'
                    gt = f['{}/Geotransform'.format(metaName)].value
                    proj = f['{}/OGC_Well_Known_Text'.format(metaName)].value.decode('UTF-8')
                    sdGEO = ecoSD
                else:
                    try:
                        # Perform kdtree resampling (swath 2 grid conversion) 
                        sdGEO = kdt.get_sample_from_neighbour_info('nn', areaDef.shape, ecoSD ,index, outdex, indexArr, fill_value=fv)                        
                        ps = np.min([areaDef.pixel_size_x, areaDef.pixel_size_y]) 
                        gt = [areaDef.area_extent[0],ps,0,areaDef.area_extent[3],0,-ps]
                    except ValueError:
                        continue 
                    
                # Apply Scale Factor
                if sf != 1:
                    sdGEO = sdGEO*sf
                    sdGEO[sdGEO == fv*sf] = fv    
                    
#-----------------------------EXPORT GEOTIFFS---------------------------------#                    
                # For USDA, export to UTM, then convert to GEO
                if 'ALEXI_USDA' in e and crsIN == 'GEO': 
                    tempName = '{}{}_{}_{}.tif'.format(outDir,ecoName,s.rsplit('/')[-1], 'TEMP')
                    outName = tempName
                else:
                    outName = '{}{}_{}_{}.tif'.format(outDir,ecoName,s.rsplit('/')[-1], crsIN)
                
                # Get driver, specify dimensions, define and set output geotransform
                height, width = sdGEO.shape  # Define geotiff dimensions
                driv =  gdal.GetDriverByName('GTiff')
                dataType = gdal_array.NumericTypeCodeToGDALTypeCode(sdGEO.dtype)
                d = driv.Create(outName, width, height, 1, dataType)
                d.SetGeoTransform(gt)
                 
                # Create and set output projection, write output array data
                if 'ALEXI_USDA' in e: d.SetProjection(proj)
                else:
                    # Define target SRS
                    srs = osr.SpatialReference()
                    srs.ImportFromEPSG(int(epsg))
                    d.SetProjection(srs.ExportToWkt())
                band = d.GetRasterBand(1)                                                 
                band.WriteArray(sdGEO)  

                # Define fill value if it exists, if not, set to mask fill value 
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
                    srs = osr.SpatialReference()
                    srs.ImportFromEPSG(int('4326'))
                    srs = srs.ExportToWkt()

                    # Open temp file, get default vals for target dims & geotransform
                    dd = gdal.Open(tempName, gdalconst.GA_ReadOnly)
                    vrt = gdal.AutoCreateWarpedVRT( dd, None, srs, gdal.GRA_NearestNeighbour, 0.125)
                    
                    # Create the final warped raster
                    outName = '{}{}_{}_{}.tif'.format(outDir,ecoName,s.rsplit('/')[-1], crsIN)
                    d = driv.CreateCopy(outName, vrt)
                    dd, d, vrt = None, None, None
                    os.remove(tempName)

if __name__ == "__main__":
   main(sys.argv[1:])    