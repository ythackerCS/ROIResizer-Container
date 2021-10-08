# ROIResizer-Container 

## Introduction

> This container loads an rtstruct file and then resizes segmentations based on user defined parameters. The user can choose whether to filter for a specific segementation name or resize every segementation within the container. Additionally the user is able to choose the scale for resizing, and whether to resize just the largest roi within a segmentation. The user also can define the new name of the resized segmentation. 

##  Design: 
  * Used python 
  * full list of packages needed: (listed within the Dockerfile.base)
    * pydicom
    * numpy 
    * shapely 
    * dicom-contour 
    * scipy 
    * requests 
    
   
##  How to use:
  > All the scripts are located within the "workspace" dir - any edits you will need to make for your specific use case will be with "scale.py". Once edits are done run ./build.sh to build your docker container. Specifics to edit within docker are the Dockerfile.base file for naming the container, pushing to git and libraries used. If you want integration with XNAT navigate to the "xnat" folder and edit the command.json documentation available at @ https://wiki.xnat.org/container-service/making-your-docker-image-xnat-ready-122978887.html#MakingyourDockerImage%22XNATReady%22-installing-a-command-from-an-xnat-ready-image

  * NOTE this was designed to be generalized to most RT structs so it should work just fine on its own with the exception of the rtstruct upload part that is unique to XNAT 

## Running (ON XNAT): 
  * Navigate to a Subject and then a particular session
  * Scroll down to assessments and click on the RTSTUCT you would like to scale click on Run Containers and then click "Resizes ROI with assessor folder mounted" 
  * Enter parameters you would like to tweak and hit run 

## Running in general: 
  * scale.py will read the RTStruct create a copy and then search through it for given filters, then scale the given ROI(s)
  * There are arguments needed to run this pipline which can be found within the scale.py script 
  * There is an upload componenet unique to XNAT if you just want to run it without uploading you can comment out that component. 

## NOTES: 
  * The scaling is done by extracting the XY cords from a set of XYZ cords, it assumes the z cord is the same for all of the xy points within an individual contour of a segmentation and a centroid of that 2D polygon is then used to scale the contour by a user defined percentage 
  * Hyperconcave polygons may break this method if the contours centroid is outside the polygon (USE WITH CAUTION) 
  * Parts of the scripts within workspace were written with project specificity in mind so please keep that in mind as you use this code 
  * It is recommended that you have some experience working with docker and specficially building containers for xnat for this to work for your use cases 
  * If you just want to use the code for your own work without docker stuff just navigate to workspace copy the python files from it and edit them 
  
## Future: 
   * Update method for more robust algorithm for scaling  
