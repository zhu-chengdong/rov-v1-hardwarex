#include <ros/ros.h>
#include <sensor_msgs/Image.h>

#include <opencv2/opencv.hpp>
#include <string>

static bool toMono8(const cv::Mat& in, cv::Mat& out) {
  if (in.empty()) return false;

  // Case 1: already 8-bit single channel
  if (in.type() == CV_8UC1) {
    out = in;
    return true;
  }

  // Case 2: 16-bit single channel -> keep high 8 bits
  if (in.type() == CV_16UC1) {
    out.create(in.rows, in.cols, CV_8UC1);
    for (int r = 0; r < in.rows; ++r) {
      const uint16_t* src = in.ptr<uint16_t>(r);
      uint8_t* dst = out.ptr<uint8_t>(r);
      for (int c = 0; c < in.cols; ++c) dst[c] = static_cast<uint8_t>(src[c] >> 8);
    }
    return true;
  }

  // Case 3: 3-channel -> convert to gray
  if (in.channels() >= 3) {
    cv::cvtColor(in, out, cv::COLOR_BGR2GRAY);
    if (out.type() != CV_8UC1) out.convertTo(out, CV_8U);
    return true;
  }

  // Fallback: convert to 8U
  in.convertTo(out, CV_8U);
  if (out.channels() != 1) return false;
  return true;
}

int main(int argc, char** argv) {
  ros::init(argc, argv, "mono_cam_cpp_node");
  ros::NodeHandle nh("~");

  std::string device = "/dev/video0";
  int width = 2560;
  int height = 800;

  nh.param<std::string>("device", device, device);
  nh.param<int>("width", width, width);
  nh.param<int>("height", height, height);

  ros::Publisher pub = nh.advertise<sensor_msgs::Image>("/camera/image_raw", 1);

  cv::VideoCapture cap(device, cv::CAP_V4L2);
  if (!cap.isOpened()) {
    ROS_ERROR("Failed to open %s", device.c_str());
    return 1;
  }

  cap.set(cv::CAP_PROP_FRAME_WIDTH, width);
  cap.set(cv::CAP_PROP_FRAME_HEIGHT, height);
  cap.set(cv::CAP_PROP_BUFFERSIZE, 1);
  cap.set(cv::CAP_PROP_CONVERT_RGB, 0);  // try avoid implicit conversion

  // Warm up a few frames
  for (int i = 0; i < 5; ++i) {
    cv::Mat tmp;
    cap.read(tmp);
    ros::Duration(0.02).sleep();
  }

  ROS_INFO("mono_cam_cpp_node started: %s %dx%d (publish full-rate)", device.c_str(), width, height);

  ros::Rate safety_rate(500); // not to throttle, just avoid busy spin on failures
  while (ros::ok()) {
    cv::Mat frame;
    if (!cap.read(frame) || frame.empty()) {
      ROS_WARN_THROTTLE(5.0, "Failed to read frame");
      safety_rate.sleep();
      ros::spinOnce();
      continue;
    }
    
    static int debug_count = 0;
    if (debug_count < 5) {
      ROS_INFO("frame: type=%d channels=%d depth=%d size=%dx%d",
               frame.type(), frame.channels(), frame.depth(),
               frame.cols, frame.rows);
      debug_count++;
    }

    ros::Time stamp = ros::Time::now();
    
    cv::Mat mono8;
    if (!toMono8(frame, mono8)) {
      ROS_WARN_THROTTLE(5.0, "Failed to convert frame to mono8");
      safety_rate.sleep();
      ros::spinOnce();
      continue;
    }

    if (mono8.cols != width || mono8.rows != height) {
      ROS_ERROR_THROTTLE(5.0, "Unexpected size %dx%d (expected %dx%d). Skipping.",
                         mono8.cols, mono8.rows, width, height);
      safety_rate.sleep();
      ros::spinOnce();
      continue;
    }

    sensor_msgs::Image msg;
    msg.header.stamp = stamp;
    msg.header.frame_id = "camera";

    msg.height = mono8.rows;
    msg.width = mono8.cols;
    msg.encoding = "mono8";
    msg.is_bigendian = 0;
    msg.step = static_cast<sensor_msgs::Image::_step_type>(mono8.cols);
    msg.data.assign(mono8.datastart, mono8.dataend);  // copy into ROS message

    pub.publish(msg);

    ros::spinOnce();
    safety_rate.sleep();
  }

  cap.release();
  return 0;
}
