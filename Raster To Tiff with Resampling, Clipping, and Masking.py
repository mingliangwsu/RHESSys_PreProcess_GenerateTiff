"""
Script documentation
- Tool parameters are accessed using arcpy.GetParameter() or 
                                     arcpy.GetParameterAsText()
- Update derived parameter values using arcpy.SetParameter() or
                                        arcpy.SetParameterAsText()
"""
import arcpy
from arcpy.sa import *
import math
def script_tool(param0, param1, param2, param3, param4, param5
                , param6, param7, param8, param9, param10
                , param11, param12, param13, param14, param15
                , param16, param17, param18, param19, param20
                , param21, param22, param23):
    """Script code goes below"""
    arcpy.ResetEnvironments()
    arcpy.env.workspace = param0
    arcpy.env.overwriteOutput = param1
    outpath = param2 + "\\"
    outcell = param3
    nbasin = param4
    nsubbasin = param5
    nbasestation = param6
    npatch = param7
    novercanopy = param8
    nunderstory = param9
    nstream = param10
    ndem = param11
    nslope = param12
    naspect = param13
    nwetness = param14
    nwh = param15
    neh = param16
    nxloc = param17
    nyloc = param18
    nlanduse = param19
    nroad = param20
    nimp = param21
    nsoiltexture = param22
    ncanopycover = param23
    
    arcpy.AddMessage("workspace:" + arcpy.env.workspace)
    arcpy.AddMessage("outpath:" + outpath)
    
    incell = arcpy.Describe(Raster(nbasin)).meanCellWidth
    rasterlist = [nbasin,nsubbasin,nbasestation,npatch,novercanopy,nunderstory
                  ,nstream,ndem,nslope,naspect,nwetness,nwh,neh
                  ,nxloc,nyloc,nlanduse,nroad,nimp,nsoiltexture,ncanopycover]
    #get the majority 
    majorlist = [nbasin,nsubbasin,nbasestation,npatch,novercanopy,nunderstory
                ,nlanduse,nsoiltexture]
    #get nearest
    nearlist = [nstream,naspect,nroad]
    
    #get mean
    meanlist = [ndem,nslope,nwetness,nwh,neh
                ,nxloc,nyloc,nimp,ncanopycover]
    
    for ras in rasterlist:
        arcpy.AddMessage("Processing " + ras)
        rasname = ras.split("\\")[-1]
        arcpy.ResetEnvironments()
        t = Raster(ras)
        incell = arcpy.Describe(t).meanCellWidth
        if incell != outcell:
            if ras in majorlist:
                aggtype = "MAJORITY"
            elif ras in meanlist:
                aggtype = "BILINEAR"
            elif ras in nearlist:
                aggtype = "NEAREST"
            else:
                arcpy.AddMessage("ERROR: no aggregation method defined for raster:" + ras)
            if ras == naspect:
                asp = Raster(ras)
                aspNull = SetNull(asp, asp, "VALUE = -1")
                aspCos = Cos(aspNull * math.pi / 180.0)
                aspSin = Sin(aspNull * math.pi / 180.0)
                arcpy.management.Resample(aspCos, "uuuu", str(outcell), "BILINEAR")
                arcpy.management.Resample(aspSin, "vvvv", str(outcell), "BILINEAR")
                xxSumCos = Raster("uuuu")
                xxSumSin = Raster("vvvv")
                asp_azm = (360+(ATan2(xxSumSin,xxSumCos)) * (180 / math.pi)) % 360.0
                asp_azm.save("YYYY") 
            else:
                arcpy.management.Resample(t, "YYYY", str(outcell), aggtype)
            t = Raster("YYYY")
        #fill null and output
        if ras == nbasin:
            #t.save(outpath + ras + ".tif")
            #arcpy.conversion.RasterToOtherFormat(t, outpath, "TIFF")
            arcpy.AddMessage("nbasin:" + rasname)
            basintiff = rasname + ".tif"
            arcpy.management.CopyRaster(t, outpath + rasname + ".tif")
        else:
            #arcpy.AddMessage("Rasters:" + rasname)
            arcpy.env.extent = Raster(outpath + basintiff)
            arcpy.env.mask = Raster(outpath + basintiff)
            arcpy.env.cellSize = outcell
            if ras in [nwh,neh]:
                tt = Con(IsNull(t) | t < 0, 0, t)
                nibmask = Con(~IsNull(t) & t >= 0, 1)
            else:
                tt = Con(IsNull(t), 0, t)
                nibmask = Con(~IsNull(t), 1)
            ttnib = Nibble(tt, nibmask, "ALL_VALUES", "PRESERVE_NODATA")
            #ttnib.save(outpath + ras + ".tif")
            #arcpy.conversion.RasterToOtherFormat(t, outpath, "TIFF")
            arcpy.management.CopyRaster(ttnib, outpath + rasname + ".tif")
        #clean up
        if arcpy.Exists("YYYY"):
            arcpy.Delete_management("YYYY")
    arcpy.AddMessage("Done!")
    return
if __name__ == "__main__":
    param0 = arcpy.GetParameterAsText(0)
    param1 = arcpy.GetParameter(1)
    param2 = arcpy.GetParameterAsText(2)
    param3 = arcpy.GetParameter(3)
    param4 = arcpy.GetParameterAsText(4)
    param5 = arcpy.GetParameterAsText(5)
    param6 = arcpy.GetParameterAsText(6)
    param7 = arcpy.GetParameterAsText(7)
    param8 = arcpy.GetParameterAsText(8)
    param9 = arcpy.GetParameterAsText(9)
    param10 = arcpy.GetParameterAsText(10)
    param11 = arcpy.GetParameterAsText(11)
    param12 = arcpy.GetParameterAsText(12)
    param13 = arcpy.GetParameterAsText(13)
    param14 = arcpy.GetParameterAsText(14)
    param15 = arcpy.GetParameterAsText(15)
    param16 = arcpy.GetParameterAsText(16)
    param17 = arcpy.GetParameterAsText(17)
    param18 = arcpy.GetParameterAsText(18)
    param19 = arcpy.GetParameterAsText(19)
    param20 = arcpy.GetParameterAsText(20)
    param21 = arcpy.GetParameterAsText(21)
    param22 = arcpy.GetParameterAsText(22)
    param23 = arcpy.GetParameterAsText(23)    
    script_tool(param0, param1, param2, param3, param4, param5
                , param6, param7, param8, param9, param10
                , param11, param12, param13, param14, param15
                , param16, param17, param18, param19, param20
                , param21, param22, param23)
    #arcpy.SetParameterAsText(2, "Result")
