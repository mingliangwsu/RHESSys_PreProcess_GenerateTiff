"""
Script documentation
- Tool parameters are accessed using arcpy.GetParameter() or 
                                     arcpy.GetParameterAsText()
- Update derived parameter values using arcpy.SetParameter() or
                                        arcpy.SetParameterAsText()
"""
import arcpy
from arcpy.sa import *
def script_tool(param0, param1, param2, param3, param4):
    """Script code goes below"""
    arcpy.ResetEnvironments()
    arcpy.env.workspace = param0
    arcpy.env.mask = Raster(param1)
    arcpy.env.extent = Raster(param1)
    arcpy.env.overwriteOutput = param2
    #output_path = param3
    outx = param3
    outy = param4
    basin_grid = Raster(param1)
    arcpy.AddMessage("workspace:" + arcpy.env.workspace)
    
    #flai = Raster("U:/Projects/Colorado_MZ/raster_tiff/LAI.tif")
    desc = arcpy.Describe(basin_grid)
    xmin = desc.extent.XMin
    ymin = desc.extent.YMin
    xmax = desc.extent.XMax
    ymax = desc.extent.YMax
    cell_size = desc.meanCellWidth
    #num_rows = desc.height
    #num_cols = desc.width
    if not arcpy.Exists("f_gbasin"):
        arcpy.management.CopyRaster(basin_grid, "f_gbasin", pixel_type='32_BIT_FLOAT')
    fbasin = Raster("f_gbasin")
    xcor = Raster(fbasin.getRasterInfo())
    ycor = Raster(fbasin.getRasterInfo())
    with RasterCellIterator({'rasters':[fbasin, xcor, ycor],'skipNoData':[fbasin]}) as rci_skip:
        for i,j in rci_skip:
            xcor[i,j] = xmin + cell_size * 0.5 + j * cell_size
            ycor[i,j] = ymax - cell_size * 0.5 - i * cell_size
    
    xcor.save(outx)
    ycor.save(outy)
    arcpy.AddMessage("Done!")
    return
if __name__ == "__main__":
    param0 = arcpy.GetParameterAsText(0)
    param1 = arcpy.GetParameterAsText(1)
    param2 = arcpy.GetParameter(2)
    param3 = arcpy.GetParameterAsText(3)
    param4 = arcpy.GetParameterAsText(4)
    #param5 = arcpy.GetParameterAsText(5)
    script_tool(param0, param1, param2, param3, param4)
    #arcpy.SetParameterAsText(2, "Result")
