#!/usr/bin/python
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import rospy
import socket  # 💡 增加导入用于获取IP
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import robot_common as common
from action import color_range 

# =================================================================
# 调试显示配置 (为了让网页显示正常)
# =================================================================
DEBUG_TOPIC = '/usb_cam_chest/image_color'

# 此时直接定义网页看到的 RGB 颜色
PRESET_RGB = {
    'yellow': (255, 255, 0), 'blue': (0, 0, 255),
    'green': (0, 255, 0), 'pink': (255, 105, 180),
    'black': (50, 50, 50), 'red': (255, 0, 0)
}

def get_ip():
    """获取本机IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

class ColorRefinementNode:
    def __init__(self):
        rospy.init_node('color_refinement_debug', anonymous=True)
        self.bridge = CvBridge()
        common.start_background_services()
        self.image_pub = rospy.Publisher(DEBUG_TOPIC, Image, queue_size=1)
        
        # 💡 只增加以下打印网址的逻辑
        my_ip = get_ip()
        print("\033[1;32m颜色调试节点已启动！\033[0m")
        print("\033[1;36m请在浏览器访问以下网址查看实时监控：\033[0m")
        print("http://{}:8080/stream_viewer?topic={}".format(my_ip, DEBUG_TOPIC))

    def run(self):
        rate = rospy.Rate(10)
        while not rospy.is_shutdown():
            raw_frame = common.ChestOrg
            if raw_frame is not None:
                # ---------------------------------------------------------
                # 💡 核心修正点：
                # 如果蓝变黄，说明 raw_frame 里的通道顺序是 RGB 而非 BGR
                # 我们强制把它当做 RGB 转成 BGR，这样识别就正了！
                # ---------------------------------------------------------
                # 1. 纠正逻辑层：让 OpenCV 拿到真正的 BGR 去转 HSV
                correct_bgr = cv2.cvtColor(raw_frame, cv2.COLOR_RGB2BGR) 
                hsv_frame = cv2.cvtColor(correct_bgr, cv2.COLOR_BGR2HSV)
                
                # 2. 准备显示层：直接用 raw_frame (因为它已经是 RGB 顺序，网页直接看就是对的)
                display_canvas = raw_frame.copy()

                for color_name, bounds in color_range.items():
                    lower = np.array(bounds[0])
                    upper = np.array(bounds[1])
                    
                    # 识别 (此时基于纠正后的 hsv_frame)
                    mask = cv2.inRange(hsv_frame, lower, upper)
                    mask = cv2.erode(mask, None, iterations=2)
                    mask = cv2.dilate(mask, None, iterations=2)
                    
                    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if contours:
                        best_cnt = max(contours, key=cv2.contourArea)
                        if cv2.contourArea(best_cnt) > 500:
                            x, y, w, h = cv2.boundingRect(best_cnt)
                            draw_color = PRESET_RGB.get(color_name, (255, 255, 255))
                            
                            # 在显示层画框
                            cv2.rectangle(display_canvas, (x, y), (x+w, y+h), draw_color, 2)
                            cv2.putText(display_canvas, f"{color_name.upper()}", (x, y-10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, draw_color, 2)

                # 3. 发布
                try:
                    # 既然 display_canvas 已经是 RGB 顺序，发布声明为 "rgb8"
                    msg = self.bridge.cv2_to_imgmsg(display_canvas, "rgb8")
                    self.image_pub.publish(msg)
                except Exception as e:
                    rospy.logerr(e)
            rate.sleep()

if __name__ == '__main__':
    ColorRefinementNode().run()