# V1 shallow-water stereo research robot

## 公开工程资料 v0.1.1

2026年11月4日更新。本版本在v0.1.0基础上整合已确认的成本、接线、制造配合和处理说明，保留原CAD几何、作者程序与温度数据。论文仍在作者审阅阶段，工程资料版本不代表论文已经投稿或录用。

V1采用商购亚克力舱体、六台推进器、两盏灯、Pixhawk兼容控制器和Jetson Orin Nano。自设计支架提供80、100和120 mm名义双目安装位置，两台相机共用前端平面视窗；内部载荷架可从后端抽出维护，面向有人监督的浅水研究使用。

## 下载和文件入口

完整源包为 [V1_HardwareX_Open_Source_v0.1.1.zip](https://github.com/zhu-chengdong/rov-v1-hardwarex/blob/main/V1_HardwareX_Open_Source_v0.1.1.zip)。解压到独立目录后保留相对文件结构。当前版本也可直接浏览下列目录。

- [自设计原生零件](hardware/native_2018)包含11个SolidWorks 2018可编辑零件。
- [制造与交换格式](hardware/exports)提供现有DXF、STEP和STL文件，几何单位为mm。
- [2024制造审阅图](hardware/manufacturing_2024_R1)包含五张原生图、配套模型、孔槽表和PDF。配合说明及中层四孔对应见 [制造说明](docs/manufacturing_fit.md) 和 [四孔表](docs/middle_main_hole_mapping.csv)；未规定公差不改写为实测精度。
- [BOM](docs/BOM.csv)及 [原币成本依据](docs/BOM_cost_basis.csv)列出46项。报告金额统一GBP，基础平台估算1130.65，可选MTi-3增加433.54，已列合计1564.19；地面设备、工具和GT设施分列。6S电池147.26为2026年11月3日同规格现价参考，历史购价151.00另行保留。
- [接线](docs/wiring.md)、[部署](docs/deployment.md)、[制造与操作](docs/build_and_operation.md)记录已确认的通道、启动和维护。
- [作者软件](software)包含机载入口及现有离线程序；[处理说明](docs/offline_processing.md)、[历史参数对应](docs/processing_evidence.md) 和 [数据布局](docs/data_layout.md)区分程序接口与实际保存的历史证据。
- [已有温度资料](validation/thermal)包括CSV、统计和脚本，沿用原结果和适用范围。

[manifest.json](manifest.json)逐项记录本版源包的137个普通文件及分项许可；加上manifest和SHA256SUMS，完整ZIP共139个文件。[SHA256SUMS](SHA256SUMS)覆盖137个普通文件及manifest，校验文件本身和两个版本ZIP不在其校验范围。Git工作树额外保留旧版和新版ZIP；[ARCHIVE_SHA256SUMS](https://github.com/zhu-chengdong/rov-v1-hardwarex/blob/main/ARCHIVE_SHA256SUMS)单独记录两个ZIP哈希。

旧版 [v0.1.0完整包](https://github.com/zhu-chengdong/rov-v1-hardwarex/blob/0897b234fac709542c385ab6d9ef04d38ec13119/V1_HardwareX_Open_Source_v0.1.0.zip)保留原字节，历史固定提交为0897b234fac709542c385ab6d9ef04d38ec13119。两个ZIP均位于仓库根目录，解压后的源包结构相同。

## 许可和复用范围

自设计硬件及功能接线图采用CERN-OHL-P-2.0，作者软件采用MIT，文档、BOM及所附验证数据采用CC BY 4.0。许可正文见 [LICENSES](LICENSES)，第三方范围见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

商购参考CAD、含其几何的私有总装与开发历史、完整ROS bag、论文草稿、实物照片和视频未纳入本源包。第三方驱动、内核和算法由原来源取得。York-Tank数据集为独立存档对象，硬件正式DOI尚未建立。

## 已保存的验证范围

本次为工程资料更新，没有改变CAD设计、程序算法或既有实验数据。制造图保持R1审阅状态；未进行新的异机SolidWorks重建或统一清洁环境端到端运行。源包包含现有GT相机导出辅助资料，完整GT求解器及ORB-SLAM3/SVO实现不在其中。版本变化见 [CHANGELOG.md](https://github.com/zhu-chengdong/rov-v1-hardwarex/blob/main/CHANGELOG.md)。
