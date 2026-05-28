# ROIResizer Container

## Overview

`ROIResizer-Container` is a Dockerized XNAT workflow for resizing regions of interest (ROIs) stored in DICOM RTSTRUCT files. The container can resize a selected ROI by name or resize all ROIs in an RTSTRUCT. It was designed to support clinical imaging and radiomics workflows where users may need to generate scaled segmentations for downstream feature extraction, sensitivity testing, or analysis.

The workflow reads an RTSTRUCT file, creates a modified copy, rescales contour coordinates using a user-defined percentage, saves the resized RTSTRUCT as a DICOM file, and uploads the new ROI collection back to XNAT.

## Motivation

Radiomics and clinical imaging workflows often depend on segmentation-based measurements. Small changes in ROI boundaries can affect extracted features, model behavior, and downstream statistical analysis. This container provides a reproducible way to generate scaled versions of RTSTRUCT segmentations inside XNAT.

The tool is especially useful for testing how sensitive radiomics features or imaging models are to ROI size, contour placement, and segmentation uncertainty.

## Workflow Summary

The pipeline performs the following steps:

1. Mounts an XNAT image assessor containing an RTSTRUCT file.
2. Searches the mounted assessor folder for an `RTSTRUCT` resource.
3. Reads the RTSTRUCT DICOM file using `pydicom`.
4. Filters for a specific ROI name, if provided.
5. Resizes either:
   - all contours within each selected ROI, or
   - only the largest contour within each selected ROI.
6. Renames the resized ROI using the user-provided prefix.
7. Saves the resized RTSTRUCT as a new DICOM file.
8. Uploads the resized RTSTRUCT back to XNAT as a new ROI collection.

## Key Features

- Runs as a Docker container through XNAT Container Service
- Reads and modifies DICOM RTSTRUCT files
- Resizes all ROIs or a selected ROI by name
- Supports resizing all contours or only the largest contour
- Allows user-defined scaling percentage
- Allows user-defined naming of resized ROIs
- Saves the modified RTSTRUCT as a DICOM file
- Uploads the resized RTSTRUCT back to XNAT
- Useful for radiomics sensitivity analysis and segmentation perturbation workflows

## Inputs

The container expects an XNAT image assessor containing an RTSTRUCT resource.

### XNAT-mounted input

```text
/assessor/
```

Expected internal structure:

```text
/assessor/
└── RTSTRUCT/
    └── *.dcm
```

### Command-line arguments

The main script is:

```text
scale.py
```

Arguments:

| Argument | Flag | Description | Default |
|---|---|---|---|
| `filterForROIName` | `-f` | Name of the ROI to resize. If blank, all ROIs are considered. | `""` |
| `percentage` | `-p` | Fraction to scale the ROI down by. Example: `0.2` reduces contour size by 20%. | `0.2` |
| `newName` | `-n` | Prefix/name for the resized ROI. | `resizedROI` |
| `all` | `-a` | If `True`, resize all contours in the selected ROI. If `False`, only the largest contour is resized. | `False` |

## Outputs

The resized RTSTRUCT is saved inside the container output folder:

```text
/out/
```

Example output file name:

```text
<newName>scaled<percentage>P.dcm
```

The script also uploads the resized RTSTRUCT back to XNAT as a new ROI collection using the XNAT ROI API.

Example uploaded ROI collection label:

```text
S20P_AIM_YYYYMMDD_HHMMSS_mmm
```

where `S20P` indicates a 20 percent scaling operation.

## How Scaling Works

The scaling method operates on each contour independently:

1. Extracts XYZ contour coordinates from the RTSTRUCT.
2. Uses the XY coordinates for each contour.
3. Computes the 2D polygon centroid using `shapely`.
4. Translates contour points to the centroid.
5. Scales the contour inward by the selected percentage.
6. Restores the original Z coordinate for each contour.
7. Writes the scaled coordinates back into the RTSTRUCT.

For example:

```text
-p 0.2
```

means the contour is scaled down by 20 percent. Internally, the coordinate scale factor becomes:

```text
1 - 0.2 = 0.8
```

## Running on XNAT

1. Navigate to the relevant subject and imaging session in XNAT.
2. Open the RTSTRUCT image assessor you want to resize.
3. Select **Run Containers**.
4. Choose **Resizes ROI with assessor folder mounted**.
5. Enter the desired parameters:
   - ROI name filter, if any
   - scaling percentage
   - new ROI name
   - whether to resize all contours or only the largest contour
6. Run the container.
7. Review the newly uploaded resized ROI collection in XNAT.

## Running Outside XNAT

The core Python script can be adapted for local execution if an RTSTRUCT DICOM file is available. Users may need to modify the hardcoded XNAT-specific paths and upload logic.

Current XNAT-specific paths include:

```text
/assessor/
/out/
```

To run outside XNAT, modify:

```python
rtsfolderpath = "/assessor/"
saveFolderPath = "/out/"
```

and remove or comment out the XNAT upload section that uses:

```python
XNAT_USER
XNAT_PASS
XNAT_HOST
PROJECT
SESSION
```

## XNAT Command Configuration

The XNAT command mounts the input assessor and output folder:

```json
"mounts": [
  {
    "name": "roi-in",
    "writable": "false",
    "path": "/assessor"
  },
  {
    "name": "out",
    "writable": "true",
    "path": "/out"
  }
]
```

The command runs:

```text
python scale.py -f <ROI_NAME> -p <PERCENTAGE> -n <NEW_NAME> -a <ALL>
```

The XNAT wrapper is configured for:

```text
xnat:imageAssessorData
```

and expects an input assessor containing the RTSTRUCT resource.

## Repository Structure

```text
ROIResizer-Container/
├── workspace/
│   └── scale.py
├── xnat/
│   └── command.json
├── Dockerfile.base
├── build.sh
└── README.md
```

Update this section if the repository structure changes.

## Requirements

Core Python dependencies include:

- `pydicom`
- `numpy`
- `shapely`
- `dicom-contour`
- `scipy`
- `requests`

Additional requirements:

- Docker
- XNAT Container Service, if running through XNAT
- RTSTRUCT DICOM input
- XNAT credentials/environment variables for upload

## Installation and Build

Clone the repository:

```bash
git clone https://github.com/ythackerCS/ROIResizer-Container.git
cd ROIResizer-Container
```

Edit the script or command configuration if needed:

```text
workspace/scale.py
xnat/command.json
```

Build the Docker container:

```bash
./build.sh
```

If deploying through XNAT, update:

```text
xnat/command.json
```

XNAT Container Service documentation is available here:

```text
https://wiki.xnat.org/container-service/making-your-docker-image-xnat-ready-122978887.html
```

## Notes and Limitations

- This method assumes each contour lies on a constant Z plane and scales the XY coordinates of that contour.
- Scaling is performed around the 2D polygon centroid.
- Highly concave polygons may not scale correctly if the centroid lies outside the polygon.
- If `all` is set to `False`, only the largest contour in the selected ROI is retained and resized.
- If no ROI name filter is provided, the script attempts to resize every ROI in the RTSTRUCT.
- The XNAT upload section is specific to XNAT deployments using the ROI API.
- Users should visually inspect resized contours before using them for clinical analysis, radiomics, or model development.

## Example Use Cases

- Generate scaled ROIs for radiomics sensitivity testing
- Assess feature robustness to segmentation boundary changes
- Create smaller derived ROIs from existing RTSTRUCT annotations
- Prepare controlled ROI perturbations for downstream imaging analysis
- Support XNAT-based clinical imaging workflows

## Related Projects

- [pyradiomics-Container](https://github.com/ythackerCS/pyradiomics-Container): XNAT-integrated PyRadiomics feature extraction workflow
- [fNIRSPluginXNAT](https://github.com/ythackerCS/fNIRSPluginXNAT): XNAT plugin for fNIRS data organization
- [OXI](https://oxi.wustl.edu): Optical-imaging XNAT-enabled Informatics platform

## Status

Research software. This container may require project-specific adaptation before use in new XNAT deployments or imaging workflows.

## Future Work

Potential future improvements include:

- Adding more robust scaling methods for highly concave contours
- Supporting additional geometric perturbation strategies
- Adding contour validation and image-space consistency checks
- Improving local execution support outside XNAT
- Adding automated visual QC outputs
- Adding test RTSTRUCT examples with expected outputs
