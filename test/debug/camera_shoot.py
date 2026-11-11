#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import os
import time
from datetime import datetime

class ImageSaver:
    def __init__(self):
        # 初始化节点
        rospy.init_node('image_saver_node', anonymous=True)
        self.bridge = CvBridge()
        
        # 基础保存目录
        self.base_dir = "./captured"
        
        # 检查并创建目录
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            print(f"目录不存在，已创建: {self.base_dir}")

        # 订阅摄像头话题
        self.image_sub = rospy.Subscriber("/usb_cam_chest/image_raw", Image, self.callback)
        
        self.has_saved = False
        print("等待接收摄像头画面...")

    def callback(self, data):
        if self.has_saved:
            return

        try:
            # 将 ROS 图像消息转换为 OpenCV 格式
            cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
            
            # 生成带时间戳的文件名 (格式: 20231027_103005.jpg)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"captured_{timestamp}.jpg"
            save_path = os.path.join(self.base_dir, file_name)
            
            # 保存图片
            cv2.imwrite(save_path, cv_image)
            
            print("-" * 50)
            print(f"成功保存图片到: {save_path}")
            print(f"文件名: {file_name}")
            print("-" * 50)
            
            self.has_saved = True
            # 延时一小会儿确保打印信息显示完毕
            rospy.Timer(rospy.Duration(0.5), lambda e: rospy.signal_shutdown("图片已成功保存"))
            
        except CvBridgeError as e:
            print(f"ROS图像转换错误: {e}")
        except Exception as e:
            print(f"保存失败: {e}")

if __name__ == '__main__':
    try:
        saver = ImageSaver()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass