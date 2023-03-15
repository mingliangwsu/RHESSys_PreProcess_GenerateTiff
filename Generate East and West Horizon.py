"""
Script documentation
- Tool parameters are accessed using arcpy.GetParameter() or 
                                     arcpy.GetParameterAsText()
- Update derived parameter values using arcpy.SetParameter() or
                                        arcpy.SetParameterAsText()
"""
import arcpy
from arcpy.sa import *
def script_tool(param0, param1, param2, param3, param4, param5):
    """Script code goes below"""
    arcpy.ResetEnvironments()
    arcpy.env.workspace = param0
    arcpy.env.scratchWorkspace = param1
    arcpy.env.overwriteOutput = param2
    arcpy.AddMessage("workspace:" + arcpy.env.workspace)
    dem = Raster(param3)
    #Output
    #output_path = param4
    outEhorizon = param4
    outWhorizon = param5
    #TESTING!
    desc = arcpy.Describe(dem)
    xmin = desc.extent.XMin
    ymin = desc.extent.YMin
    xmax = desc.extent.XMax
    ymax = desc.extent.YMax
    cell_size = desc.meanCellWidth
    # Set the extent environment variable
    arcpy.env.extent = dem
    sr = desc.spatialReference
    origin = arcpy.Point(xmin, ymin)
    
    start = 0
    end = 90
    step = 0.5
    
    import numpy as np
    arr_e = dict()
    arr_w = dict()
    #generate hillshade for each step angle
    arcpy.AddMessage("Genering horizon by creating hillshade from 0 to 90 degree...")
    for i in np.arange(start, end, step):
        arcpy.AddMessage(str(i))
        stri = str(int(i*10))
        te = arcpy.sa.Hillshade(in_raster=dem,azimuth=90,altitude=i,model_shadows="NO_SHADOWS",z_factor=1)
        tw = arcpy.sa.Hillshade(in_raster=dem,azimuth=270,altitude=i,model_shadows="NO_SHADOWS",z_factor=1)
        arr_e[stri] = arcpy.RasterToNumPyArray(te)
        arr_w[stri] = arcpy.RasterToNumPyArray(tw)
    
    arcpy.AddMessage("Processing all...")
    #initialize by the value of -1
    
    e_base = arr_e[str(int(start*10))].copy().astype(float)
    w_base = arr_w[str(int(start*10))].copy().astype(float)
    e_base[:] = -1
    w_base[:] = -1
    
    
    for i in np.arange(start, end, step):
        arcpy.AddMessage(str(i))
        stri = str(int(i*10))
        rad = i * 3.14159 * 1000.0 / 180.0
        e_base = np.where((arr_e[stri] >= 1) & (e_base < 0), rad, e_base)
        w_base = np.where((arr_w[stri] >= 1) & (w_base < 0), rad, w_base)
    arcpy.AddMessage("Saving all...")
    eraster = arcpy.NumPyArrayToRaster(e_base, origin, cell_size, cell_size)
    arcpy.DefineProjection_management(eraster, sr)
    t = Int(eraster * 100) / 100.0
    t.save(outEhorizon)
    wraster = arcpy.NumPyArrayToRaster(w_base, origin, cell_size, cell_size)
    arcpy.DefineProjection_management(wraster, sr)
    tt = Int(wraster * 100) / 100.0
    tt.save(outWhorizon)
    #wraster.save(outWhorizon)
     
    #output tiff
    #eraster.save(outEhorizon) 
    #wraster.save(outWhorizon) 
     
    arcpy.AddMessage("Cleaning up ...")
    arcpy.env.workspace = param1
    for i in range(0, 300):
        arcpy.AddMessage(str(i))
        if arcpy.Exists("HillSha_de" + str(i)):
            arcpy.Delete_management("HillSha_de" + str(i))
        if arcpy.Exists("HillSha_dem" + str(i)):
            arcpy.Delete_management("HillSha_dem" + str(i))
        if arcpy.Exists("HillSha_dem_" + str(i)):
            arcpy.Delete_management("HillSha_dem_" + str(i))
    
    arcpy.AddMessage("Done!")
    return
if __name__ == "__main__":
    param0 = arcpy.GetParameterAsText(0)
    param1 = arcpy.GetParameterAsText(1)
    param2 = arcpy.GetParameter(2)
    param3 = arcpy.GetParameterAsText(3)
    param4 = arcpy.GetParameterAsText(4)
    param5 = arcpy.GetParameterAsText(5)
    #param6 = arcpy.GetParameterAsText(6)
    script_tool(param0, param1, param2, param3, param4, param5)
    #arcpy.SetParameterAsText(2, "Result")
