from arcpy.sa import *
tiff_file = "X:/Projects/Rangeland/Landfire/LF2022_EVC_220_CONUS/Tif/LC22_EVC_220.tif"

fields = ['Value','CLASSNAMES']
with arcpy.da.SearchCursor(tiff_file, fields) as cursor:
    for row in cursor:
        print(u'{0}, {1}'.format(row[0], row[1]))
