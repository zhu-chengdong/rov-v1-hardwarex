# V1 shallow water stereo research robot

Initial public engineering release v0.1.0, 2 November 2026.

V1 combines a commercial acrylic enclosure, six thrusters, two lights, a Pixhawk-compatible controller and a Jetson Orin Nano. Custom acrylic stereo mounts provide 80, 100 and 120 mm nominal mounting positions behind a shared flat front window. The internal payload rack can be withdrawn through the rear for maintenance. The platform is intended for supervised shallow-water research.

## Files and use

- `hardware/native_2018` contains the eleven custom editable SolidWorks part sources. `hardware/exports` contains their available DXF, STEP and STL manufacturing/interchange forms. Geometry is in millimetres.
- `hardware/manufacturing_2024_R1` contains five 2024 review drawings, their unchanged model copies and PDF exports. Preserve relative folders when opening drawings. Tolerances and acceptance requirements remain unresolved; these are review drawings.
- `hardware/wiring` contains editable functional diagrams. Read `docs/wiring.md` for the actual TELEM1, PM02 and single-signal PWM implementation and remaining physical channel mapping.
- `docs/build_and_operation.md` and `docs/BOM.csv` describe assembly, maintenance and the 46-item cost/support scope.
- `software/onboard` contains the actual camera-node source and serial/UDP bridge. `docs/deployment.md` distinguishes measured installation, historical logs and author-reported operation.
- `software/offline` contains 27 calibration, processing, GT-camera and RTAB-Map helper files; `docs/offline_processing.md` describes their static interfaces. These do not include a complete GT solver or the ORB-SLAM3/SVO implementations.
- `validation/thermal` contains existing auxiliary air/water observations and analysis. They are not a controlled thermal comparison or proof of full-duration camera operation.

The GitHub repository includes a complete source bundle named `V1_HardwareX_Open_Source_v0.1.0.zip`. If browsing the repository without extracted hardware directories, extract that bundle into a separate directory to obtain all native CAD, drawings and source files. `manifest.json` records each published file and its licence; `SHA256SUMS` verifies the bundle contents.

## Reuse and licences

Copyright 2026 Chengdong Zhu and contributors. Hardware designs and functional wiring diagrams are licensed under **CERN-OHL-P-2.0**. Author software and associated software configuration are licensed under **MIT**. Documentation, BOM and supplied validation data are licensed under **CC BY 4.0**. See `LICENSE`, `LICENSES` and `THIRD_PARTY_NOTICES.md`; this is a mixed-licence project, not a claim to third-party component designs.

Commercial component reference CAD, supplier drawings, driver/kernel binaries, the Xsens upstream driver and full commercial-module assemblies are excluded. Obtain those components and dependencies from their original suppliers. The private development repository and its history remain separate.

## Evidence and outstanding details

The stereo system supported York-Tank, C. Zhu and M. Post, Sensors 26 (2026) 6567, https://doi.org/10.3390/s26206567. This repository is not the full York-Tank dataset. It makes no maximum-depth, endurance, positioning-accuracy or long-term reliability claim.

Motor-to-physical-position mapping, left/right lamp mapping for outputs 7/8, some wire/fastener details, tolerances and historical calibration associations remain documented gaps. Camera effective controls and some current device state will be checked during normal later use. No new experiments were run for this release. Publication of these sources does not establish submission readiness. A DOI archive has not yet been created.
