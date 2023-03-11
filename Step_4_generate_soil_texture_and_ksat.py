import arcpy,csv
from arcpy.sa import *
import math

arcpy.ResetEnvironments()
arcpy.env.overwriteOutput = True
#Inputs
arcpy.env.workspace = "U:/Projects/Colorado_MZ/cobasin/cobasin.gdb"
tiffpath = "U:/Projects/Colorado_MZ/raster_tiff/"
gbndry = Raster("gbasin")

gnatsgo_gdb = "Z:/Projects/GIS_datasets/DataSet_ForRHESSys/SoilTexture/gNATSGO_CONUS/gNATSGO_CONUS.gdb"
mapunit_name = "MapunitRaster_30m"

#information table
surface_texture_tab = gnatsgo_gdb + "/" + "liu_surface_texture"
clay_tab = gnatsgo_gdb + "/" + "clay_percent_dcp_0_30cm"
sand_tab = gnatsgo_gdb + "/" + "sand_percent_dcp_0_30cm"
silt_tab = gnatsgo_gdb + "/" + "silt_percent_dcp_0_30cm"
Ksat_tab = gnatsgo_gdb + "/" + "Ksat_dcp_0_30cm"
Bulk_tab = gnatsgo_gdb + "/" + "Bulkdensity_dcp_0_30cm"

#Outputs:
outmapunit_name = "mapunit"
soiltexture_name = "soiltexture"
clay_name = "pclay"
sand_name = "psand"
silt_name = "psilt"
Ksat_name = "Ksat"
Bulk_name = "Bulkdensity"

#E. Benham and R.J. Ahrens, W.D. 2009. Clarification of Soil Texture Class Boundaries. Nettleton National Soil Survey Center, USDA-NRCS, Lincoln, Nebraska.
#A simple code to automate the determination of the soil textural class based on the percent of sand and clay according to the US Department of Agriculture Natural Resources Conservation Service (NRCS). There are a total of 12 soil textural classes and this classification is typically done by hand using the textural triangle
#https://soilwater.github.io/pynotes-agriscience/notebooks/soil_textural_class.html
def soiltexturalclass(sand,clay):
    """Function that returns the USDA 
    soil textural class given 
    the percent sand and clay.
    Inputs = Percetnage of sand and clay
    """
    silt = 100 - sand - clay
    if sand + clay > 100 or sand < 0 or clay < 0:
        raise Exception('Inputs adds over 100% or are negative')
    elif silt + 1.5*clay < 15:
        textural_class = 'sand'
    elif silt + 1.5*clay >= 15 and silt + 2*clay < 30:
        textural_class = 'loamy sand'
    elif (clay >= 7 and clay < 20 and sand > 52 and silt + 2*clay >= 30) or (clay < 7 and silt < 50 and silt + 2*clay >= 30):
        textural_class = 'sandy loam'
    elif clay >= 7 and clay < 27 and silt >= 28 and silt < 50 and sand <= 52:
        textural_class = 'loam'
    elif (silt >= 50 and clay >= 12 and clay < 27) or (silt >= 50 and silt < 80 and clay < 12):
        textural_class = 'silt loam'
    elif silt >= 80 and clay < 12:
        textural_class = 'silt'
    elif clay >= 20 and clay < 35 and silt < 28 and sand > 45:
        textural_class = 'sandy clay loam'
    elif clay >= 27 and clay < 40 and sand > 20 and sand <= 45:
        textural_class = 'clay loam'
    elif clay >= 27 and clay < 40 and sand <= 20:
        textural_class = 'silty clay loam'
    elif clay >= 35 and sand > 45:
        textural_class = 'sandy clay'
    elif clay >= 40 and silt >= 40:
        textural_class = 'silty clay'
    elif clay >= 40 and sand <= 45 and silt < 40:
        textural_class = 'clay'
    else:
        textural_class = 'na'
    return textural_class

#surface texture to USDS classes (add rock and water)
def soiltexture_name_to_USDA_classes(texture):
    """Function that returns the USDA 
    soil textural class given the name
    Inputs = texture name from gNATSGO
    """
    if 'water' in texture.lower():
        textural_class = 'water'
    elif 'bedrock' in texture.lower():
        textural_class = 'rock'
    elif 'sandy clay loam' in texture.lower():
        textural_class = 'sandy clay loam'
    elif 'silty clay loam' in texture.lower():    
        textural_class = 'silty clay loam'
    elif 'loamy sand' in texture.lower():     
        textural_class = 'loamy sand'
    elif 'sandy loam' in texture.lower():      
        textural_class = 'sandy loam'
    elif 'silt loam' in texture.lower():    
        textural_class = 'silt loam'
    elif 'clay loam' in texture.lower():    
        textural_class = 'clay loam'
    elif 'sandy clay' in texture.lower():      
        textural_class = 'sandy clay'
    elif 'silty clay' in texture.lower():    
        textural_class = 'silty clay'
    elif 'clay' in texture.lower():  
        textural_class = 'clay'
    elif 'loam' in texture.lower(): 
        textural_class = 'loam'  
    elif 'silt' in texture.lower(): 
        textural_class = 'silt'
    elif 'sand' in texture.lower():     
        textural_class = 'sand'
    else:
        textural_class = 'na'
    return textural_class
    
#coding according to RHESSys    
usda_to_rhessys_code = {'sand':10,
                        'loamy sand':11,
                        'sandy loam':12,
                        'loam':9,
                        'silt loam':8,
                        'silt':7,
                        'sandy clay loam':5,
                        'clay loam':6,
                        'silty clay loam':3,
                        'sandy clay':4,
                        'silty clay':2,
                        'clay':1,
                        'rock':13,
                        'water':14}


#env
mapunit = Raster(gnatsgo_gdb + '/' + mapunit_name)
#clip mapunit (first, need get the boundary of target area)
input_ref = arcpy.Describe(mapunit).spatialReference
output_ref = arcpy.Describe(gbndry).spatialReference
out_cell_size = str(int(arcpy.Describe(gbndry).meanCellWidth))

#get corner in EVC
#vegetation to EVC projection

if input_ref.factoryCode == output_ref.factoryCode and input_ref.name == output_ref.name:
    arcpy.CopyRaster_management(gbndry, "XXXXXX")
else:
    arcpy.management.ProjectRaster(gbndry, "XXXXXX", input_ref, "NEAREST", out_cell_size)

desc = arcpy.Describe("XXXXXX")
xmin = desc.extent.XMin
ymin = desc.extent.YMin
xmax = desc.extent.XMax
ymax = desc.extent.YMax
cell_size = desc.meanCellWidth
buffer_dist = 50 * cell_size

bnd = str(xmin - buffer_dist) + ' ' + str(ymin - buffer_dist) + ' ' + str(xmax + buffer_dist) + ' ' + str(ymax + buffer_dist) #x-min, y-min, x-max, y-max
arcpy.management.Clip(mapunit, bnd, "XXXXXX")
#reproject to same as Vegetation inputs
arcpy.env.snapRaster = gbndry
if input_ref.factoryCode == output_ref.factoryCode and input_ref.name == output_ref.name:
    arcpy.CopyRaster_management("XXXXXX", outmapunit_name)
else:
    arcpy.management.ProjectRaster("XXXXXX", outmapunit_name, output_ref, "NEAREST", out_cell_size)
if arcpy.Exists("XXXXXX"):
    arcpy.Delete_management("XXXXXX")
    
#generate output
arcpy.env.extent = gbndry
arcpy.env.mask = gbndry

gmapunit = Raster(outmapunit_name)
#link all table to this map unit raster

arcpy.conversion.ExportTable(gmapunit, "temptable")
arcpy.JoinField_management("temptable","MUKEY",surface_texture_tab,"MUKEY")
arcpy.JoinField_management("temptable","MUKEY",clay_tab,"MUKEY")
arcpy.JoinField_management("temptable","MUKEY",sand_tab,"MUKEY")
arcpy.JoinField_management("temptable","MUKEY",silt_tab,"MUKEY")
arcpy.JoinField_management("temptable","MUKEY",Ksat_tab,"MUKEY")
arcpy.JoinField_management("temptable","MUKEY",Bulk_tab,"MUKEY")

fd = arcpy.ListFields("temptable")
for field in fd:
    print(field.name)

usda_to_rhessys_code = {'sand':10,
                        'loamy sand':11,
                        'sandy loam':12,
                        'loam':9,
                        'silt loam':8,
                        'silt':7,
                        'sandy clay loam':5,
                        'clay loam':6,
                        'silty clay loam':3,
                        'sandy clay':4,
                        'silty clay':2,
                        'clay':1,
                        'rock':13,
                        'water':14}
NODATA = -9999
arcpy.management.AddField("temptable", "RHESSys_texture", "SHORT")
fields = ["SURFTEXT_DCD","CLAY_DCP","SAND_DCP","RHESSys_texture"]
with arcpy.da.UpdateCursor("temptable", fields) as cursor:
    for row in cursor:
        #usda texture class from surface texture name 
        usda_class = 'na'
        if row[0] is not None:
            usda_class = soiltexture_name_to_USDA_classes(row[0])
        else:
            usda_class = 'na'
            
        if usda_class == "water":
            row[3] = usda_to_rhessys_code["water"]
        elif usda_class == "rock":
            row[3] = usda_to_rhessys_code["rock"]
        elif row[1] is not None and row[2] is not None: 
            name_from_texture = soiltexturalclass(row[2],row[1])
            if name_from_texture in usda_to_rhessys_code:
                row[3] = usda_to_rhessys_code[name_from_texture]
            elif usda_class in usda_to_rhessys_code:
                row[3] = usda_to_rhessys_code[usda_class]
            else:
                row[3] = NODATA
        elif usda_class in usda_to_rhessys_code:
            row[3] = usda_to_rhessys_code[usda_class]
        else:
            row[3] = NODATA
        cursor.updateRow(row)

#Create all rasters 
# Get access to the VAT table
arcpy.JoinField_management(gmapunit,"MUKEY","temptable","MUKEY")
if arcpy.Exists("temptable"):
    arcpy.Delete_management("temptable")
    
outvar_name_lib = {"RHESSys_texture" : soiltexture_name,
                   "CLAY_DCP" : clay_name,
                   "SAND_DCP" : sand_name,
                   "SILT_DCP" : silt_name,
                   "DB3RDBAR_DCP" : Bulk_name,
                   "KSAT_DCP" : Ksat_name}
# Extract the column of interest from the VAT table
for var in outvar_name_lib:
    if var == 'RHESSys_texture':
        column_values = Int(arcpy.sa.Lookup(gmapunit, var))
    else:
        column_values = arcpy.sa.Lookup(gmapunit, var)
    column_values.save(outvar_name_lib[var])
     