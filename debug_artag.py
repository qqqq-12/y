#!/usr/bin/python
# -*- coding: utf-8 -*-
import rospy
import time
import sys
from robot_common import TagConverter  # 确保你的文件名正确

def run_all_tag_monitor():
    # 1. 初始化 ROS 节点
    rospy.init_node('full_tag_monitor_node', anonymous=True)
    
    # 2. 实例化你源码里的类
    tag_manager = TagConverter()
    
    # 缓存机制：解决断断续续的问题
    tag_cache = {}        # 存储每个 ID 最后一次出现的数据 {id: [x, y, yaw]}
    tag_loss_count = {}   # 记录每个 ID 消失的帧数 {id: count}
    MAX_LOSS_FRAMES = 5   # 容忍 5 帧丢失（约 0.5 秒）

    print("\n" + "="*65)
    print(f"{'TagID':^8} | {'X (米)':^12} | {'Y (米)':^12} | {'Yaw (度)':^10} | {'状态'}")
    print("-" * 65)

    try:
        while not rospy.is_shutdown():
            # 获取当前帧看到的 markers
            current_markers = tag_manager.get_all_markers()
            seen_this_frame = set()

            # --- 处理当前看到的码 ---
            for m in current_markers:
                tag_id = int(m[0])
                x_pos = float(m[1])
                y_pos = float(m[2])
                yaw = float(m[3]) + 90
                
                # 更新缓存
                tag_cache[tag_id] = [x_pos, y_pos, yaw]
                tag_loss_count[tag_id] = 0
                seen_this_frame.add(tag_id)

            # --- 处理没看到但可能在缓存里的码 ---
            for tid in list(tag_cache.keys()):
                if tid not in seen_this_frame:
                    tag_loss_count[tid] += 1
                    # 如果丢失帧数超过阈值，从缓存删除
                    if tag_loss_count[tid] > MAX_LOSS_FRAMES:
                        del tag_cache[tid]
                        del tag_loss_count[tid]

            # --- 打印展示 ---
            if tag_cache:
                # 按照 ID 排序显示
                sorted_ids = sorted(tag_cache.keys())
                # 打印前先清屏一行（通过 \r）
                output_str = ""
                for tid in sorted_ids:
                    val = tag_cache[tid]
                    status = "LIVE" if tid in seen_this_frame else "HOLD"
                    print(f"[{tid:02d}]  | {val[0]:10.4f} | {val[1]:10.4f} | {val[2]:10.2f} | {status}")
            else:
                sys.stdout.write("\r📡 搜索中... 视野内暂无 ARTag 码 (请对准标签)          ")
                sys.stdout.flush()

            time.sleep(0.1)  # 10Hz 刷新

    except KeyboardInterrupt:
        print("\n\n已停止监测。")

if __name__ == '__main__':
    try:
        run_all_tag_monitor()
    except rospy.ROSInterruptException:
        pass