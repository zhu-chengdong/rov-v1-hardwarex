# Third party sources and exclusions

The public hardware licence covers only the listed custom parts, their exports, review drawings and project functional wiring diagrams. Commercial enclosure, thruster, light, controller, computer, camera and sensor reference models are not relicensed or redistributed. The complete private assembly, including those reference models, is excluded. Use the BOM, custom parts and build documentation to assemble purchased components.

The frame-slot lighting installation follows the BlueROV2 mounting idea acknowledged in the manuscript. No Blue Robotics CAD file or guide image is copied into this release. Source https://bluerobotics.com/learn/bluerov2-assembly-r3-version/ .

The 27 offline experiment files were previously confirmed by the author as original/team scripts, configuration and experiment records. Current release authorization extends these selected files to the stated licences; the private repository's old licence-status documents are not copied as current public policy. Numeric calibration parameters are retained and their historical-use limits are documented.

External dependencies are separately licensed and must be obtained upstream. ROS https://www.ros.org/ ; OpenCV https://opencv.org/ ; Arducam B0266 and matching driver https://www.arducam.com/ ; Xsens driver https://github.com/xsens/xsens_mti_ros_node ; ArduSub https://ardupilot.org/sub/ ; QGroundControl https://qgroundcontrol.com/ ; FTDI/pyserial https://pyserial.readthedocs.io/ . No upstream driver, kernel image, SDK, third-party algorithm or its binaries are bundled.

Software metadata changes in the public camera package are limited to replacing the placeholder licence with MIT and identifying the maintainer. Source acquisition logic is unchanged. No upstream author notice is removed. Licence texts retain their original legal wording.
