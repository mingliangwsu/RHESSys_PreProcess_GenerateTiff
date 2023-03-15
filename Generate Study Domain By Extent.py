"""
Script documentation
- Tool parameters are accessed using arcpy.GetParameter() or 
                                     arcpy.GetParameterAsText()
- Update derived parameter values using arcpy.SetParameter() or
                                        arcpy.SetParameterAsText()
"""
import arcpy
from arcpy.sa import *
def script_tool(param0, param1, param2, param3, param4, param5, param6, param7):
    """Script code goes below"""
    arcpy.ResetEnvironments()
    arcpy.env.workspace = param0
    define_extent = param1
    inextent = param2
    cellsize = param3
    ref = param4
    arcpy.env.overwriteOutput = param5
    outputbndfc = param6
    outputbndraster = param7
    
    array = arcpy.Array([arcpy.Point(inextent.XMin, inextent.YMin),
                     arcpy.Point(inextent.XMin, inextent.YMax),
                     arcpy.Point(inextent.XMax, inextent.YMax),
                     arcpy.Point(inextent.XMax, inextent.YMin)])
    polygon = arcpy.Polygon(array)
    # Open an insert cursor for the output feature class
    arcpy.CreateFeatureclass_management(arcpy.env.workspace, "ctemp", "POLYGON")
    arcpy.AddField_management("ctemp", "PID", "SHORT")
    # Insert the point into the feature class
    #fields = ['SHAPE@',"PID"]
    #cursor = arcpy.da.InsertCursor("ctemp_pour", fields)
    #cursor.insertRow([new_geom,1])
    row_values = [(1, polygon)]
    with arcpy.da.InsertCursor("ctemp", ['PID', 'SHAPE@']) as cursor:
    # Insert new rows that include the ID and a x,y coordinate
    #  pair that represents the county center
        for row in row_values:
            cursor.insertRow(row)
    #define projection
    geo_ref = arcpy.SpatialReference(4269)
    arcpy.management.DefineProjection("ctemp", geo_ref)
    arcpy.Project_management("ctemp", outputbndfc, ref)
    arcpy.conversion.FeatureToRaster(outputbndfc, "PID", outputbndraster, cellsize)
    # Clean up
    del cursor
    arcpy.AddMessage("Done!")
    return
if __name__ == "__main__":
    param0 = arcpy.GetParameterAsText(0)
    param1 = arcpy.GetParameter(1)
    param2 = arcpy.GetParameter(2)
    param3 = arcpy.GetParameter(3)
    param4 = arcpy.GetParameter(4)
    param5 = arcpy.GetParameter(5)
    param6 = arcpy.GetParameterAsText(6)
    param7 = arcpy.GetParameterAsText(7)
    script_tool(param0, param1, param2, param3, param4, param5, param6, param7)
    #arcpy.SetParameterAsText(2, "Result")
