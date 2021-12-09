import os 
import pydicom 
# from read_roi import read_roi_zip
from dicom_contour.contour import *
from requests.api import head
from shapely.geometry import Polygon
import numpy as np
import argparse
import requests 



from requests.structures import CaseInsensitiveDict
from datetime import date 
from datetime import datetime



#this python script can take a RTStruct of dcm type and scale every segmentation within it or scale only the segmentation with a matching filter name; flag: -f 
    #the scaling of the segmentation can also be done in two ways:; flags: -a (for all) and -p (percentage of scaling) and -n (new name of scaled segmentation)
        #1 - the largest contour (by area) of segmentation is rescaled 
        #2 - every contour in a segmentation is rescaled 

#NOTE: plt plots have been strategically placed to be able to view the scaling for correctness just uncomment them to see the results 
#WARNING: This technique employs the use of the centeroid of a polygon which may be ouside a highly concave polygon e.g U shaped contours which can make this method ineffective 
#Second NOTE: number of ROICollection folders in = number of ROI collection folders out, data accross ROICollection folders cannot be concatinated, if more than one ROI collection is found then a source tag will be added to clarify source of data 

#XNAT ARGUMENTS FOR SCRIPT 


def str_to_bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in {'false', 'f', '0', 'no', 'n'}:
        return False
    elif value.lower() in {'true', 't', '1', 'yes', 'y'}:
        return True
    raise ValueError("{0} is not a valid boolean value".format(value))

parser = argparse.ArgumentParser(description='Resizes ROIs in the rts struct files')


##-Arguments to python script -##
parser.add_argument('-f',"--filterForROIName", help="Name of the ROI to rescaled, if none provided all will be resized", nargs='?', default="", type=str)
parser.add_argument('-p',"--percentage", help="Percentage to scale the roi DOWN by provide float e.g. 0.2 -> scale down by 20 percent (Default 0.2)", nargs='?', default="0.2", type=float)
parser.add_argument('-n',"--newName", help="Name of the resized ROI", nargs='?', default="resizedROI", type=str)

parser.add_argument('-a',"--all", help="Rescale every ROI in the RTstruct? If false only the largest roi will be rescaled", type=str_to_bool, nargs='?', default=False)



##contour is scaled using calcualted centeroid cordinates after flattening xyz cordinates to just xy cordinates 
def scale_contour(cnt, scale):
    scale = 1-scale
    polygon = Polygon(cnt)
    cx, cy = polygon.centroid.coords[0]
    cnt_norm = cnt - [cx, cy]
    cnt_scaled = cnt_norm * scale
    cnt_scaled = cnt_scaled + [cx, cy]
    cnt_scaled = cnt_scaled.astype(np.float64)
    scaledxcord, scaledycord = cnt_scaled.T 
    return cnt_scaled, cx, cy, scaledxcord, scaledycord 


#this function scales segmentation aka all contours for segmentation provided will be resized 
def scaleSegmentation(copyRTStruct, segData, whichROI, scale, segmentationName):
    for contour in segData.ContourSequence: 
        #scaling stuff using polygon 
        # print("scaling contour", contour.ContourNumber)
        contNum = contour.ContourNumber

        #getting contour xy data for plot z is assumed to be contstant accross all xy points of a given contour 
        length = int(len(contour.ContourData)/3)
        data = contour.ContourData
        reshapedData = np.reshape(data, (length,3))
        reshapedDataXY = reshapedData[:, :2]

        #calculating area of current contour to compare to rescaled contour 
        polygon = Polygon(reshapedDataXY)
        currentArea = polygon.area
        # print("area of contour before rescale is: ", currentArea)

        x,y = reshapedDataXY.T
        contourNumber = contour.ContourNumber
        z = reshapedData[0][2]
        plt.plot(x,y, color="Orange")

        #scaling the contour 
        cnt_scaled, cx, cy, sx, sy  = scale_contour(reshapedDataXY, scale)

        #calculating area of rescaled contour
        polygon = Polygon(cnt_scaled)
        scaledArea = polygon.area
        # print("area of contour after rescale is: ", scaledArea)
        plt.plot(sx,sy, color="Blue")
        #stacking z coordinate back in for OHIF viewing 
        zstack = np.full(x.shape, z)
        zAdded = np.dstack([sx, sy, zstack]).flatten()
        # print()
        #adding replacing contour data within correct segmentation with scaled data 
        copyRTStruct.ROIContourSequence[whichROI].ContourSequence[contourNumber-1].ContourData = zAdded.tolist()
    #changing roi name for xnat 
    copyRTStruct.StructureSetROISequence[whichROI].ROIName = segmentationName

    #uncommenting this code will show all orginal segmentations ploted along with scaled segmentations orange is original, blue is scaled 
    # plt.show() 
    return copyRTStruct


#this function will calculate the largest roi and return its contour number 
def getLargestROI(roiDataSet):
    largestArea = None 
    largestROI = None
    largestROIReshapedData = None 
    zdim = None 
    contourNumber = None 

    for contour in roiDataSet.ContourSequence:
        length = int(len(contour.ContourData)/3)
        data = contour.ContourData
        
        #getting contour xy data for plot z is assumed to be contstant accross all xy points of a given contour 
        reshapedData = np.reshape(data, (length,3))
        reshapedDataXY = reshapedData[:, :2]
        polygon = Polygon(reshapedDataXY)
        currentArea = polygon.area
        if largestArea is None or largestArea < currentArea:
            largestArea = currentArea
            largestROI = reshapedDataXY
            largestROIReshapedData = reshapedData
            zdim = largestROIReshapedData[0][2]
            contourNumber = contour.ContourNumber
        x,y = largestROI.T
    return reshapedData,largestROI, x, y, zdim, contourNumber


#this function will calculate the largest contour and then scale it based on user defied scale 
def scaleLargestContourInSegmentation(copyRTStruct, segmentationDataSet, whichROI, scaleFactor, segmentationName): 
    print("scaling largest roi in segmentation ")

    reshape, largest, xcoords, ycoords, z, contNum = getLargestROI(segmentationDataSet)
    plt.plot(xcoords,ycoords, color='Orange')

    cnt_scaled, cx, cy, scaledxcord, scaledycord  = scale_contour(largest, scaleFactor)
    plt.plot(scaledxcord, scaledycord, color="BlUE")

    #uncommenting below line will display orginal segmentation along with scaled segmentation in a plot, orange is original, blue is scaled
    # plt.show() 


    zstack = np.full(xcoords.shape, z)
    zAdded = np.dstack([scaledxcord, scaledycord, zstack]).flatten()

    copyRTStruct.ROIContourSequence[whichROI].ContourSequence[contNum-1].ContourData = zAdded.tolist()

    #delete every roi other than the resized one
    data = copyRTStruct.ROIContourSequence[whichROI].ContourSequence[contNum-1]
    copyRTStruct.ROIContourSequence[whichROI].ContourSequence = [data]
    copyRTStruct.ROIContourSequence[whichROI].ContourSequence[0].ContourNumber=1


    copyRTStruct.StructureSetROISequence[whichROI].ROIName = segmentationName

    return copyRTStruct


def scaleRTS(roiName, scaleFactor, newName, resizeALL, copyRTStruct):
    # print("CHOOSING TO RESIZE ALL CONTOURS OR JUST LARGEST")
    #determine whether you need to resize the largest ROI or all of the ROI's 
    count = 1
    if resizeALL: 
        #if you resizeall, every countour in the segmentation will be resized 
        print("RESIZING ALL CONTOURS")
        for roi in rois.StructureSetROISequence: 
            #searchEach segmentations name, if it matches filter name then it will be scaled, OR if filter provied is '' (none) then segmentation will be scaled 
            print("checking filters on", roi.ROIName)
            if roi.ROIName == roiName or roiName == "":
                whichROI = roi.ROINumber - 1
                segmentationDataSet = rois.ROIContourSequence[whichROI]
                print("resizing contour named, ",  roi.ROIName)

                #if no segmentation name filter provided newName will be used to rename the scaled segmentation, if no filter provided, a count will be appended to the newName to make sure no segmentations have the same name 
                #note: name for new Segmentation is a concatination of the newName + old ROI name 
                if roiName == "":
                    segmentationName = newName + roi.ROIName + str(count)
                else:
                    segmentationName = newName + roi.ROIName

                #function scales entire segmentation 
                modifiedRTStruct = scaleSegmentation(copyRTStruct, segmentationDataSet, whichROI, scaleFactor, segmentationName)
                count += 1
    else: 
        print("RESIZING LARGEST CONTOURS")
        for roi in rois.StructureSetROISequence: 
            #searchEach segmentations name, if it matches filter name then it will be scaled, OR if filter provied is '' (none) then segmentation will be scaled 
            print("checking filters on", roi.ROIName)
            if roi.ROIName == roiName or roiName == "":
                whichROI = roi.ROINumber - 1
                segmentationDataSet = rois.ROIContourSequence[whichROI]
                print("resizing contour named, ",  roi.ROIName)

                #if no segmentation name filter provided newName will be used to rename the scaled segmentation, if no filter provided, a count will be appended to the newName to make sure no segmentations have the same name 
                #note: name for new Segmentation is a concatination of the newName + old ROI name 
                if roiName == "":
                    segmentationName = newName + roi.ROIName + str(count)
                else:
                    segmentationName = newName + roi.ROIName
                modifiedRTStruct = scaleLargestContourInSegmentation(copyRTStruct, segmentationDataSet, whichROI, scaleFactor, segmentationName)
                count += 1
        
    return modifiedRTStruct 


arguments = parser.parse_args()
ROIFilterName = arguments.filterForROIName
ScaleDownFactor = arguments.percentage 
NewName = arguments.newName
resizeAllContours = arguments.all 


#info printed for user conveneince 
if ROIFilterName == "":
    print("Resizing every segmentation in RTStruct")
    print("Scaling down by: ", ScaleDownFactor)
    print("New Name For Scaled ROI: ", NewName, "+countnumber (for distinct segmentation names)")
    print("Resizing all contours: ", resizeAllContours)
else:
    print("Looking for roiName: ", ROIFilterName)
    print("Scaling down by: ", ScaleDownFactor)
    print("New Name For Scaled ROI: ", NewName)
    print("Resizing all contours: ", resizeAllContours)

#assessorfolder must contain rtstruct within a RTSTRUCT folder 
rtsfolderpath = "/assessor/"
rtfolders = os.listdir(rtsfolderpath)
saveFolderPath = "/out/"


for rt in rtfolders:
    if rt == "RTSTRUCT":
        rtStructFolder = rtsfolderpath+rt
        file = get_contour_file(rtStructFolder)
        path = rtStructFolder+"/"+file
        rois = pydicom.read_file(path)
        copyStruct = rois.copy()

        struct = scaleRTS(ROIFilterName, ScaleDownFactor, NewName, resizeAllContours, copyStruct)
        segmentationCollectionName = struct.StructureSetLabel+"scaled"+str(int(ScaleDownFactor*100))+"P"
        struct.StructureSetLabel=segmentationCollectionName

        #saving dcmfile

        roi_label = NewName+"scaled"+str(int(ScaleDownFactor*100))+"P"

        saveName = roi_label+".dcm"

        print("FILE NAME" , saveName)
        dcmPath = os.path.join(saveFolderPath,saveName)
        print(dcmPath)
        struct.save_as(dcmPath)

        #the code below is very specific to xnat which will gather user info and then "PUT" rtstruct info into project-->session as a new resized rtstruct 
        xnat_user = os.environ['XNAT_USER']
        xnat_pass = os.environ['XNAT_PASS']
        xnat_host = os.environ['XNAT_HOST']
        project = os.environ['PROJECT']
        session = os.environ['SESSION']

        with requests.session() as sesh:
            sesh.keep_alive = False
            now = datetime.now()

            now = now.strftime("AIM_%Y%m%d_%H%M%S_%f")[:-3]
            roi_label = "S"+str(int(ScaleDownFactor*100))+"P_"+now

            url = "{0}/xapi/roi/projects/{1}/sessions/{2}/collections/{3}?type=RTSTRUCT".format(xnat_host, project, session, roi_label)

            headers = CaseInsensitiveDict()
            headers["Content-Type"] = "application/octet-stream"
            headers["Connection"] = "Close"

            data=open(dcmPath, 'rb')


            resp = sesh.put(url, headers=headers, auth=(xnat_user, xnat_pass), data=data)

            if resp.status_code != 200: 
                print("ERROR CODE", resp.status_code)
                print("Error Message", resp.content)

            resp.close() 
            sesh.close() 

            print(resp.content)

            resp = sesh.delete("{0}/data/JSESSION".format(xnat_host))

            print(resp.content)