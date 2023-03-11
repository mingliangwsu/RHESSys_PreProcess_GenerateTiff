import arcpy,csv
from arcpy.sa import *
import math
arcpy.ResetEnvironments()
arcpy.env.workspace = "U:/Projects/Colorado_MZ/cobasin/cobasin.gdb"
arcpy.env.overwriteOutput = True

#Inputs
basin_grid = Raster("gbasin")
out_cell_size = str(int(arcpy.Describe(basin_grid).meanCellWidth))

dem = Raster("Z:/Projects/GIS_datasets/DataSet_ForRHESSys/NA_Elevation/na_elevation")
lai = Raster("Z:/Projects/GIS_datasets/DataSet_ForRHESSys/LAI/maxLAI_2018_2020_CONUS.tif") #0-100 i.e. scale 10
basin_shp = "U:/Projects/Colorado_MZ/BigThomson_WS_Shapefile/BigThomson_Shapefile.shp"
#Outputs
outbase = "U:/Projects/Colorado_MZ/raster_tiff/gridmet.base"
out_gridmet_utm = "U:/Projects/Colorado_MZ/raster_tiff/gridmet_utm.tif"

#example_ncfile = "U:/Projects/Colorado_MZ/Rind_CO/RHESSys_NetCDF_pr_daily_UI_historical_1979_2022.nc"
ncpath = "U:/Projects/Colorado_MZ/"
climname = {'tmax' : 'Downloaded_GridMET/agg_met_tmmx_1979_CurrentYear_CONUS.nc',
            'tmin' : 'Downloaded_GridMET/agg_met_tmmn_1979_CurrentYear_CONUS.nc',
            'rain' : 'Downloaded_GridMET/agg_met_pr_1979_CurrentYear_CONUS.nc',
            'huss' : 'Downloaded_GridMET/agg_met_sph_1979_CurrentYear_CONUS.nc',
            'rmax' : 'Downloaded_GridMET/agg_met_rmax_1979_CurrentYear_CONUS.nc',
            'rmin' : 'Downloaded_GridMET/agg_met_rmin_1979_CurrentYear_CONUS.nc',
            'rsds' : 'Downloaded_GridMET/agg_met_srad_1979_CurrentYear_CONUS.nc',
            'was' : 'Downloaded_GridMET/agg_met_vs_1979_CurrentYear_CONUS.nc'
            }
"""
climname = {'tmax' : 'Rind_CO/RHESSys_NetCDF_tasmax_daily_UI_historical_1979_2022.nc',
            'tmin' : 'Rind_CO/RHESSys_NetCDF_tasmin_daily_UI_historical_1979_2022.nc',
            'rain' : 'Rind_CO/RHESSys_NetCDF_pr_daily_UI_historical_1979_2022.nc',
            'huss' : 'Rind_CO/RHESSys_NetCDF_huss_daily_UI_historical_1979_2022.nc',
            'rmax' : 'Rind_CO/RHESSys_NetCDF_rmax_daily_UI_historical_1979_2022.nc',
            'rmin' : 'Rind_CO/RHESSys_NetCDF_rmin_daily_UI_historical_1979_2022.nc',
            'rsds' : 'Rind_CO/RHESSys_NetCDF_rsds_daily_UI_historical_1979_2022.nc',
            'was' : 'Rind_CO/RHESSys_NetCDF_was_daily_UI_historical_1979_2022.nc'
            }     
"""            
example_ncfile = ncpath + climname['tmax']

utm_ref = arcpy.Describe(basin_grid).spatialReference
geo_ref = arcpy.SpatialReference(4269)


#get lat and lon list from netcdf file
import xarray as xr

# Open the netCDF file using xarray
ds = xr.open_dataset(example_ncfile)
# Extract the latitude and longitude values as lists
lat_list = ds['lat'].values.tolist()
lon_list = ds['lon'].values.tolist()
lat_min = min(lat_list)
lat_max = max(lat_list)
lon_min = min(lon_list)
lon_max = max(lon_list)
lat_step = (lat_max - lat_min) / (len(lat_list) - 1.0)
lon_step = (lon_max - lon_min) / (len(lon_list) - 1.0)

#generating fishnet
xmin = lon_min - lon_step / 2.0
ymin = lat_min - lat_step / 2.0
ymin_dir = ymin + 1.0
origin_coord = str(xmin) + ' ' + str(ymin) #"-180 -90"
y_axis_coord = str(xmin) + ' ' + str(ymin_dir) #"-180 -89"
cell_width = str(lon_step)
cell_height = str(lat_step)
num_rows = str(len(lat_list))
num_cols = str(len(lon_list))
opposite_corner = ""

# Create the fishnet
arcpy.management.CreateFishnet("gridmet_shp", origin_coord, y_axis_coord, cell_width, cell_height, num_rows, num_cols,"#","#",'#',"POLYGON")
arcpy.management.DefineProjection("gridmet_shp", geo_ref)

arcpy.management.AddField("gridmet_shp", "gridmet_id", "LONG")
fields = ["OID", "gridmet_id"]
with arcpy.da.UpdateCursor("gridmet_shp", fields) as cursor:
    # loop through each row in the feature class
    for row in cursor:
        # calculate the value for field2 based on the value in field1
        row[1] = row[0]
        # update the row
        cursor.updateRow(row)
arcpy.management.AddGeometryAttributes("gridmet_shp", "CENTROID", "#", "#", geo_ref)
arcpy.management.AlterField("gridmet_shp", "CENTROID_X","lon","lon")
arcpy.management.AlterField("gridmet_shp", "CENTROID_Y","lat","lat")
arcpy.management.AddGeometryAttributes("gridmet_shp", "CENTROID", "#", "#", utm_ref)
arcpy.management.AlterField("gridmet_shp", "CENTROID_X","proj_x","proj_x")
arcpy.management.AlterField("gridmet_shp", "CENTROID_Y","proj_y","proj_y")
arcpy.env.outputCoordinateSystem = utm_ref
#generate raster    
try:
    arcpy.MakeFeatureLayer_management("gridmet_shp","gridmet_lyr")
    sel_gridmet = arcpy.SelectLayerByLocation_management("gridmet_lyr", "INTERSECT", basin_shp)
    if arcpy.Exists("pgridmet_utm"):
        arcpy.Delete_management("pgridmet_utm")
    arcpy.CopyFeatures_management("gridmet_lyr","pgridmet_utm")
except:
   print(arcpy.GetMessages())
#poly to raster
arcpy.env.snapRaster = basin_grid

arcpy.conversion.FeatureToRaster("pgridmet_utm", "gridmet_id", "gridmet_utm", int(out_cell_size))
gridmetbnd = Raster("gridmet_utm")

#generate elevation info
outZonalStatistics = ZonalStatisticsAsTable(gridmetbnd, "Value", dem,"testtable","DATA","MEAN")

#generate LAI info
outZonalStatistics_lai = ZonalStatisticsAsTable(gridmetbnd, "Value", lai,"laitable","DATA","MEAN")


#elevation of each gridmet grid
elevation = dict()
fields = ['Value','MEAN']
with arcpy.da.SearchCursor("testtable", fields) as cursor:
    for row in cursor:
      elevation[str(row[0])] = float(row[1])
      
#lai of each gridmet grid
laidic = dict()
fields = ['Value','MEAN']
with arcpy.da.SearchCursor("laitable", fields) as cursor:
    for row in cursor:
      laidic[str(row[0])] = float(row[1]) / 10.0

gridmet_cor = dict()
fields = ['gridmet_id','lat','lon','proj_x','proj_y']
with arcpy.da.SearchCursor("pgridmet_utm", fields) as cursor:
    for a in cursor:
        gridmet_cor[str(a[0])] = [str(a[0]),f"{a[1]:.5f}",f"{a[2]:.5f}",f"{a[3]:.1f}",f"{a[4]:.1f}"];

#base station tiff
arcpy.env.extent = basin_grid
arcpy.env.mask = basin_grid
arcpy.env.cellSize = int(out_cell_size)
test = Raster("gridmet_utm") + 0
test.save(out_gridmet_utm)

#basinfo

#number to multiply to get the unit "mm/day"
ppt_coef = 1.
#number to multiply to get the unit to "fraction", i.e. in range 0-1
rhum_coef = 1.0
#temperature unit 'K' or 'C'
temperature_unit = 'K'
#huss should be in unit "kg/kg"
#rsds should be in unit "W m-2"
#wind should be in unit "m s-1"


varname = dict()
for var in climname:
    ncfile = xr.open_dataset(ncpath + climname[var])
    variable_names = list(ncfile.variables)
    if len(variable_names) > 0:
        for varn in variable_names:
            if varn not in ['day','time', 'lat', 'lon']:
                varname[var] = varn
    else:
        print("Warning:" + ncfile + "has no variable for " + var + "\n")
    variable_properties = ncfile[varname[var]].attrs
    unit = variable_properties['units']
    if var == "rain" and unit == "kg m-2 s-1":
        ppt_coef = 86.4
    elif var in ['rmax','rmin'] and unit == "%":
        rhum_coef = 0.01
    elif var in ['tmax','tmin']:
        temperature_unit = unit



"""
varname = {'tmax' : 'air_temperature',
            'tmin' : 'air_temperature',
            'rain' : 'precipitation_flux',
            'huss' : 'specific_humidity',
            'rmax' : 'relative_humidity',
            'rmin' : 'relative_humidity',
            'rsds' : 'surface_downwelling_shortwave_flux_in_air',
            'was' : 'wind_speed'
            }
"""
with open(outbase,'w') as f:
    f.write(str(len(gridmet_cor)) + ' grid_cells\n')
    f.write('0.03 location_searching_distance\n')
    f.write('1900 year_start_index\n')
    f.write('0.0 day_offset\n')
    f.write('1.0 leap_year_include\n')
    f.write(str(ppt_coef) + ' precip_multiplier\n')
    f.write(str(rhum_coef) + ' rhum_multiplier\n')
    f.write(temperature_unit + ' temperature_unit\n')
    f.write('lon netcdf_var_x\n')
    f.write('lat netcdf_var_y\n')
    for var in climname:
        f.write(climname[var] + ' netcdf_' + var + '_filename\n')
        f.write(varname[var] + ' netcdf_var_' + var +'\n')
    for grid in gridmet_cor:
        f.write(grid + ' base_station_id\n')
        #gridmet_id 0,lat 1,lon 2,utm_x 3,utm_y 4
        f.write(gridmet_cor[grid][2] + ' lon\n')
        f.write(gridmet_cor[grid][1] + ' lat\n')
        f.write(gridmet_cor[grid][3] + ' xc\n')
        f.write(gridmet_cor[grid][4] + ' yc\n')
        f.write(f"{elevation[grid]:.1f}" + ' z_coordinate\n')
        f.write(f"{laidic[grid]:.2f}" + ' effective_lai\n')
        f.write('10.0 screen_height\n')



