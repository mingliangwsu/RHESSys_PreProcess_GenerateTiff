import arcpy,csv
from arcpy.sa import *
import math
arcpy.ResetEnvironments()
arcpy.env.workspace = "U:/Projects/Colorado_MZ/cobasin/cobasin.gdb"
arcpy.env.overwriteOutput = True

#INPUTS
#basin boundary
basin_utm = "U:/Projects/Colorado_MZ/BigThomson_WS_Shapefile/BigThomson_Shapefile.shp"
#land cover
nlcd2019_albs = Raster("Z:/Projects/GIS_datasets/NLCD_USGS/LandCover/nlcd_2019_land_cover_l48_20210604/nlcd_2019_land_cover_l48_20210604.img")
#maximum NDVI
ndvi_input = Raster("U:/Projects/Colorado_MZ/co_maxNDVI_2020_fromNDVI32d.tif") # co_maxNDVI_2020.tif")
#imperviousness (NLCD) 0-100 unsigned interger
imp_albs = Raster("Z:/Projects/GIS_datasets/NLCD_USGS/Imperviousness/nlcd_2019_impervious_l48_20210604.img")



#generate basin raster
out_cell_size = "30"

arcpy.conversion.FeatureToRaster(basin_utm, "value", "gbasin", out_cell_size)

ndvi_ref = arcpy.Describe(ndvi_input).spatialReference
nlcd_ref = arcpy.Describe(nlcd2019_albs).spatialReference
basin_utm_ref = arcpy.Describe(basin_utm).spatialReference

#reproject bndry to albers
arcpy.management.Project(basin_utm, "basin_albers", nlcd_ref)

#clip nlcd & imp
arcpy.management.Clip(nlcd2019_albs, "basin_albers", "nlcd_alb")
arcpy.management.Clip(imp_albs, "basin_albers", "imp_alb")

#reproject nlcd & imp to UTM
#arcpy.env.snapRaster = raster
#may need to change
arcpy.env.snapRaster = Raster("gbasin")

arcpy.management.ProjectRaster("nlcd_alb", "nlcd_utm", basin_utm_ref, "MAJORITY", out_cell_size)
arcpy.management.ProjectRaster("imp_alb", "imp_utm", basin_utm_ref, "BILINEAR", out_cell_size)
if ndvi_ref.factoryCode == basin_utm_ref.factoryCode and ndvi_ref.name == basin_utm_ref.name:
    ndvi_input.save("ndvi_utm")
else:
    arcpy.management.ProjectRaster("ndvi_input", "ndvi_utm", basin_utm_ref, "BILINEAR", out_cell_size)
ndvi_utm = Raster("ndvi_utm")
    

#generate LAI & overcanopy & understory 
arcpy.env.extent = Raster("gbasin")
arcpy.env.mask = Raster("gbasin")
arcpy.env.cellSize = int(out_cell_size)

nlcd = Raster("nlcd_utm")
imperviousness = 1.0 - Raster("imp_utm") * 0.01  #for RHESSys: 0: road   1: forest etc.
imperviousness.save("imperviousness")    


#step one: aggregate/reclassify NLCD into major types: 
#11: water 31:rock 41: deciduous 42: pine 52: shrub 71: grass
#this vegetation code for for estimating LAI
remap = RemapValue([[11, 11], [12, 41],[21, 71],[22, 71],[23, 71],[24, 71],[31, 31],[41, 41],[42, 42],[43, 42],[52, 52],[71, 71],[81, 71],[90, 52],[95, 52]])
nlcd_newc = Reclassify(nlcd, "Value", remap, "NODATA")
nlcd_newc.save("nlcd_newc")

#road
remap_road = RemapValue([[11,12,0],[21,24,1],[31,95,0]])
road = Reclassify(nlcd, "Value", remap_road, "NODATA") 
road.save("road")

#landuse 1: agriculture 2: undeveloped 3: urban
remap_landuse = RemapValue([[11,12,2], [21,24,3],[31,74,2],[81,82,1],[90,95,2]])
landuse = Reclassify(nlcd, "Value", remap_landuse, "NODATA") 
landuse.save("landuse")

#output final strata type and understory strata
#1:evergreen 2:deciduous 3:grass 4:non veg 5:shrub 6:water 49:under deciduous 50:under pine 51:nonveg under
remap_RHESSys_overcanopy = RemapValue([[11, 6], [31, 4],[41, 2],[42, 1],[52, 5],[71, 3]])
govercanopy = Reclassify(nlcd_newc, "Value", remap_RHESSys_overcanopy, "NODATA") 
govercanopy.save("govercanopy")
#understory strata
remap_RHESSys_understory = RemapValue([[11, 51], [31, 51],[41, 49],[42, 50],[52, 51],[71, 51]]) 
gunderstory = Reclassify(nlcd_newc, "Value", remap_RHESSys_understory, "NODATA") 
gunderstory.save("gunderstory")


#const predefined
#11: water 31:rock 41: deciduous 42: pine 52: shrub 71: grass
veg_types = {11:'water',31:'rock',41:'deciduous',42:'pine',52:'shrub',71:'grass'}
#beer's law
lib_blaw = {11:0.1, 31:0.1, 41:0.54, 42:0.46, 52:0.55, 71:0.48}
NDVIinf_const = {11:0.804, 31:0.524, 41:0.878, 42:0.981, 52:0.89705, 71:0.899}
lib_maxlai = {11:3.01, 31:3.01, 41:8.26, 42:12.21, 52:5.24, 71:4.09}


#beerslaw
beerslaw = Con(nlcd_newc == 11, lib_blaw[11], Con(nlcd_newc == 31, lib_blaw[31], Con(nlcd_newc == 41, lib_blaw[41], Con(nlcd_newc == 42, lib_blaw[42], Con(nlcd_newc == 52, lib_blaw[52], lib_blaw[71])))))
beerslaw.save("beerslaw")   

#NDVIinf constant (user predefined)
#NDVIinf = Con(nlcd_newc == 11, 0.804, Con(nlcd_newc == 31, 0.524, Con(nlcd_newc == 41, 0.878, Con(nlcd_newc == 42, 0.981, Con(nlcd_newc == 52, 0.89705, 0.899)))))



maxndvi_input = Con(ndvi_utm < 0, 0, ndvi_utm)

#automatic calculate NDVIinf

NDVIinf_cal = dict()
for veg in veg_types:
    temp = Con(nlcd_newc == veg, maxndvi_input)
    ZonalStatisticsAsTable('gbasin', 'Value', temp,'temptable', 'DATA', 'PERCENTILE', 'CURRENT_SLICE',[99], 'AUTO_DETECT', 'ARITHMETIC')
    fields = ['Value','PCT99']
    with arcpy.da.SearchCursor("temptable", fields) as cursor:
        for row in cursor:
          #print(u'{0}, {1}, {2}'.format(row[0], row[1], row[2]))
          if row[0] == 1:
            NDVIinf_cal[veg] = row[1]
    if veg not in NDVIinf_cal:
        NDVIinf_cal[veg] = NDVIinf_const[veg]
    else:
        if NDVIinf_cal[veg] > NDVIinf_const[veg]:
            NDVIinf_cal[veg] = NDVIinf_const[veg]
        
#calculated        
NDVIinf = Con(nlcd_newc == 11, NDVIinf_cal[11], Con(nlcd_newc == 31, NDVIinf_cal[31], Con(nlcd_newc == 41, NDVIinf_cal[41], Con(nlcd_newc == 42, NDVIinf_cal[42], Con(nlcd_newc == 52, NDVIinf_cal[52], NDVIinf_cal[71])))))
#NDVIback
ZonalStatisticsAsTable('gbasin', 'Value', maxndvi_input,'ndvitable', 'DATA', 'PERCENTILE', 'CURRENT_SLICE',[1], 'AUTO_DETECT', 'ARITHMETIC')
fields = ['Value','PCT1']
with arcpy.da.SearchCursor("ndvitable", fields) as cursor:
    for row in cursor:
      #print(u'{0}, {1}, {2}'.format(row[0], row[1], row[2]))
      if row[0] == 1:
        NDVIback = row[1]

#cal LAI
#range for log portion
ln_min_lib = {}
ln_max = 1.0
for veg in veg_types:
    ln_min_lib[veg] = math.exp(-lib_maxlai[veg]*lib_blaw[veg])

ln_min = Con(nlcd_newc == 11, ln_min_lib[11], Con(nlcd_newc == 31, ln_min_lib[31], Con(nlcd_newc == 41, ln_min_lib[41], Con(nlcd_newc ==42, ln_min_lib[42], Con(nlcd_newc == 52, ln_min_lib[52], ln_min_lib[71])))))

ln_coef = (NDVIinf - maxndvi_input)/(NDVIinf - NDVIback)
lai = (-1.0 / beerslaw) * Ln(Con(ln_coef > ln_max, ln_max, Con(ln_coef < ln_min, ln_min, ln_coef)))

#maximum LAI 11: water 31:rock 41: deciduous 42: pine 52: shrub 71: grass
#https://daac.ornl.gov/VEGETATION/LAI_support_images.html#table   mean+1std
maxlai = Con(nlcd_newc == 11, lib_maxlai[11], Con(nlcd_newc == 31, lib_maxlai[31], Con(nlcd_newc == 41, lib_maxlai[41], Con(nlcd_newc ==42, lib_maxlai[42], Con(nlcd_newc == 52, lib_maxlai[52], lib_maxlai[71])))))
maxlai.save("maxlai")
#laiadj = Con(lai < 0.001, 0.001, Con(((govercanopy == 4) | (govercanopy == 6)) & (lai > 0.01), 0.01, Con((govercanopy == 3) & (lai > 12), , lai)))#
laiadj = Con(lai > maxlai, maxlai, Con(lai < 0.001, 0.001, lai))

laiadj.save("LAI")

#export to TIF
outpath = "U:/Projects/Colorado_MZ/raster_tiff/"
arcpy.CopyRaster_management(laiadj, outpath + "LAI.tif")    
arcpy.CopyRaster_management(govercanopy, outpath + "govercanopy.tif") 
arcpy.CopyRaster_management(gunderstory, outpath + "gunderstory.tif") 
arcpy.CopyRaster_management(imperviousness, outpath + "imperviousness.tif")
arcpy.CopyRaster_management(road, outpath + "road.tif")
arcpy.CopyRaster_management(landuse, outpath + "landuse.tif")