#!/usr/bin/python
# -*- coding: utf-8 -*-

import rospy
import cv2
import numpy as np
import os
import time
from sensor_msgs.msg import Image

# ================= 配置区 =================
IMAGE_TOPIC = '/usb_cam_chest/image_raw'
OUTPUT_PATH = "/home/sunrise/debug/debug_colorgrid.png"
# =========================================

def get_hsv_snapshot():
    rospy.init_node('hsv_snapshot_tool', anonymous=True)
    
    print("等待接收摄像头图像 (Topic: %s)..." % IMAGE_TOPIC)
    
    try:
        # 1. 阻塞式等待一帧图像消息
        msg = rospy.wait_for_message(IMAGE_TOPIC, Image, timeout=10)
    except rospy.ROSException:
        print("❌ 超时：未能接收到信号。")
        return

    # 2. 直接还原形状 (保持原始字节顺序)
    # 修正：如果颜色反了，说明原始数据已经是 BGR，直接 reshape 即可
    img_np = np.frombuffer(msg.data, dtype=np.uint8)
    img_cv2 = img_np.reshape((msg.height, msg.width, 3))
    
    # 3. 基于当前通道生成 HSV 数据
    # 此时 img_cv2 会被作为 BGR 处理
    hsv_img = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2HSV)
    draw_img = img_cv2.copy()
    h, w = draw_img.shape[:2]

    print("📸 图像捕获成功，正在生成 HSV (H,S,V) 全参数地图...")

    # 4. 绘图标注
    step = 60  
    for y in range(20, h, step):
        for x in range(20, w, step):
            h_val, s_val, v_val = hsv_img[y, x]
            
            # 画采样中心点 (红色小点)
            cv2.circle(draw_img, (x, y), 2, (0, 0, 255), -1)
            
            # 标注 H,S,V 三个值
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.32
            thickness = 1
            
            # 这里的标注颜色：H用黄色，S用绿色，V用白色
            cv2.putText(draw_img, "H:%d" % h_val, (x + 5, y - 10), font, font_scale, (0, 255, 255), thickness)
            cv2.putText(draw_img, "S:%d" % s_val, (x + 5, y + 2),  font, font_scale, (0, 255, 0), thickness)
            cv2.putText(draw_img, "V:%d" % v_val, (x + 5, y + 14), font, font_scale, (255, 255, 255), thickness)

    # 5. 绘制坐标网格
    for x in range(0, w, 100):
        cv2.line(draw_img, (x, 0), (x, h), (80, 80, 80), 1)
        cv2.putText(draw_img, str(x), (x + 2, 15), font, 0.4, (200, 200, 200), 1)
    for y in range(0, h, 100):
        cv2.line(draw_img, (0, y), (w, y), (80, 80, 80), 1)
        cv2.putText(draw_img, str(y), (5, y - 5), font, 0.4, (200, 200, 200), 1)

    # 6. 保存
    cv2.imwrite(OUTPUT_PATH, draw_img)
    
    print("="*40)
    print("✅ 分析完成！")
    print("📍 检查路径: %s" % OUTPUT_PATH)
    print("💡 验证提示：")
    print("   - 黄色物体的 H 应在 20-40 之间")
    print("   - 蓝色物体的 H 应在 100-130 之间")
    print("="*40)

if __name__ == '__main__':
    get_hsv_snapshot()