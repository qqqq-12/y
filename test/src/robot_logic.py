#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import rospy
import time
import robot_common as common
from robot_common import do    # 特别导出 do，使其不需要前缀
from std_msgs.msg import String
from action import VOICE_CONTROL_MAP
# ==========================================
# 1. 核心任务函数 (已修正参数传递格式)
# ==========================================

current_stage = "base_to_task1"
# 预设的全局配置
cfg_test = [1, (0.08, 0, 0), (0.02, 0.02, 1)]

task_step = "align-0"
def base_to_task1(is_jump=False):
    global task_step
    cfg = [0, (0.08, 0, 0), (0.05, 0.05, 8)]
    if task_step == "align-0":
        if common.align_to_tag(cfg):
            print("\n\033[1;33m🔄 Tag-0已对齐\033[0m")
            do("forward_q",1)
            task_step = "align-1"
    if task_step == "align-1":
        cfg = [1, (0.1843, 0, 0), (0.04, 0.04, 8)]   
        if common.align_to_tag(cfg):
            do("turnleft", 10)
            do("forward_q", 2)
            return "task1"
    return False

base_to_task2_step = "align-1"
def base_to_task2(is_jump=False):
    global base_to_task2_step
    if base_to_task2_step == "align-1":
        # cfg = [1, (0.1843, 0, 0), (0.04, 0.04, 8)]
        # if common.align_to_tag(cfg):
        do("forward_q", 5)
        base_to_task2_step = "align-5"
    if base_to_task2_step == "align-5":
        cfg = [5, (0.12, 0, 0), (0.04, 0.04, 3)]
        if common.align_to_tag(cfg):
            do("turnleft", 8)
            do("forward_q", 5)
            base_to_task2_step = "align-3"
            return "task2"
    return False

def base_to_task3(is_jump=False):
    do("forward_q", 5)
    return "task3"

base_to_task4_step = "forward5"
def base_to_task4(is_jump=False):
    global base_to_task4_step
    if base_to_task4_step == "forward5":
        # cfg = [1, (0.1843, 0, 0), (0.04, 0.04, 8)]
        # if common.align_to_tag(cfg):
        do("forward_q", 5)
        base_to_task4_step = "align-5"
    if base_to_task4_step == "align-5":
        cfg = [5, (0.10, 0, 0), (0.05, 0.05, 8)]
        if common.align_to_tag(cfg):
            do("right", 10)
            return "task4"
    return False

def task1(is_jump=False):
    """第一关：推抹布任务"""
    cfg = [2, (0.16, 0, 0), (0.01, 0.02, 3)]
    if common.align_to_tag(cfg):
        common.log("\n\033[1;33m🔄 等待语音启动指令...\033[0m")
        waiting_for_voice = True
        while waiting_for_voice and not rospy.is_shutdown():
            if common.voice_signal:
                voice_word = common.voice_action_name
                if voice_word in VOICE_CONTROL_MAP:
                    target, cmd_type = VOICE_CONTROL_MAP[voice_word]

                    if target == "release_task1":
                        common.log(f"🎙️ 指令匹配成功: '{voice_word}' -> {target}。开始任务！")
                        common.voice_signal = False  # 消费信号
                        waiting_for_voice = False    # 跳出循环
                    else:
                        common.log(f"⏳ 收到指令({target})非目标指令，继续等待...")
                        common.voice_signal = False
                else:
                    common.voice_signal = False
            time.sleep(0.1)
        common.log("\033[1;32m🚀 正在前进并执行推抹布动作...\033[0m")
        do("forward_q", 2)
        common.playmusic(10)
        do("left", 2)
        do("forward_s", 1)
        do("push_rag_p14", 1)
        return "task1_to_task2"
    return False

def task1_to_task2(is_jump=False):
    common.log("\n\033[1;33m🔄 等待语音启动指令...\033[0m")
    waiting_for_voice = True
    while waiting_for_voice and not rospy.is_shutdown():
        if common.voice_signal:
            voice_word = common.voice_action_name
            if voice_word in VOICE_CONTROL_MAP:
                target, cmd_type = VOICE_CONTROL_MAP[voice_word]

                if target == "release_task2":
                    common.log(f"🎙️ 指令匹配成功: '{voice_word}' -> {target}。开始任务！")
                    common.voice_signal = False  # 消费信号
                    waiting_for_voice = False    # 跳出循环
                else:
                    common.log(f"⏳ 收到指令({target})非目标指令，继续等待...")
                    common.voice_signal = False
            else:
                common.voice_signal = False
        time.sleep(0.1)
    do("right", 5)
    do("forward_q", 1)
    return "task2"

def task2(is_jump=False):
    """第二关：二层书架任务"""
    # 检查全局变量：如果手里已经有箱子了，就绝对不要再跑色块对齐逻辑！
    if not common.HandHaveBox:
        # 如果还在对齐或抓取过程中，直接结束本次函数，不往下走
        if not common.align_and_pick_cube("black"):
            return False 
        # 如果 align_and_pick_cube 返回了 True，HandHaveBox 已经被设为 True 了
        common.log(f"✨ 色块抓取成功，开始右转并寻找书架 (Tag-4)")
        do("box_turnright_q", 4)
    
    # 2. 对齐 Tag-4 放书
    cfg = [4, (0.17, 0, 0), (0.02, 0.04, 5)]
    if common.align_to_tag(cfg):
        common.log("\n\033[1;33m🔄 Tag-书架已对齐，开始前进...\033[0m")
        do("up_stair_1_good", 1)
        do("put_shelf_two", 1)
        common.HandHaveBox = False
        common.playmusic(11)
        do("back", 1)
        do("down_stair_1_good", 1)
        return "task2_to_task3"
    return False

def task2_to_task3(is_jump=False):
    cfg = [4, (0.24, 0, 8), (0.04, 0.06, 6)]
    if common.align_to_tag(cfg):
        common.log("\n\033[1;33m🔄 Tag-书架已对齐，开始撤离...\033[0m")
        do("right", 12)
        return "task3"
    return False

def task3(is_jump=False):
    """第三关：OCR识别"""
    cfg = [5, (0.08, 0, 0), (0.04, 0.04, 3)]
    # 1. 首先完成对齐
    if common.align_to_tag(cfg):
        common.log("\n\033[1;33m🔄 等待语音启动指令...\033[0m")
        waiting_for_voice = True
        while waiting_for_voice and not rospy.is_shutdown():
            if common.voice_signal:
                voice_word = common.voice_action_name
                if voice_word in VOICE_CONTROL_MAP:
                    target, cmd_type = VOICE_CONTROL_MAP[voice_word]

                    if target == "release_task3":
                        common.log(f"🎙️ 指令匹配成功: '{voice_word}' -> {target}。开始任务！")
                        common.voice_signal = False  # 消费信号
                        waiting_for_voice = False    # 跳出循环
                    else:
                        common.log(f"⏳ 收到指令({target})非目标指令，继续等待...")
                        common.voice_signal = False
                else:
                    common.voice_signal = False
            time.sleep(0.1)
        do("forward_q", 2)
        do("forward", 1)
        do("lean_back", 1)
        time.sleep(1)
        common.log("\033[1;36m📷 正在读取公告牌信息...\033[0m")
        category, color_name = common.get_ocr_result()
        common.log(f"\n\033[1;32m✅ OCR 结果：{category}, {color_name}\033[0m")
        time.sleep(2)
        do("end_lean_back", 1)
        return "task3_to_task4"
        
    return False

def task3_to_task4(is_jump=False):
    # 建议还是先对齐5再右移
    do("back", 3)
    do("right", 10)
    return "task4"

task4_step = "picking"
def task4(is_jump=False):
    global task4_step
    # --- 步骤 1：抱书 (仅在手里没书时执行) ---
    if task4_step == "picking":
        cfg = [6, (0.08, 0, 0), (0.03, 0.02, 5)]
        if common.align_to_tag(cfg):
            do("forward_q", 2)
            do("pick_box", 1)
            # 抱完之后，务必在 pick_box 内部或这里设置 HandHaveBox = True
            common.HandHaveBox = True 
            do("box_turnright_q", 8)
            task4_step = "approaching"
            return "task4"
        else:
            return False # 没对准书，退出等待下次循环

    # --- 步骤 2 & 3：趋近与投递 (仅在手里有书时执行) ---
    if task4_step == "approaching":
        common.HandHaveBox = True 
        # 这一步会阻塞，直到看到 Tag 3 或靠近蓝色
        common.walk_to_bigbox("blue", 16)
        common.log("🚩 从颜色大盒子，切换到Tag对齐")
        task4_step = "aligning"

    if task4_step == "aligning":
        # 投递
        common.HandHaveBox = True 
        cfg = [16, (0.08, 0, 180), (0.05, 0.02, 5)]
        if common.align_to_tag(cfg):
            do("box_forward_q", 3)   #refy这里改成抱cube快走
            do("drop_book_box", 1)
            common.HandHaveBox = False # 丢完了，重置状态
            common.playmusic(12)
            return "exit" 
            
    return False

# ==========================================
# 2. 主调度程序
# ==========================================

def main():
    rospy.init_node('image_listener', anonymous=True)

    # --- 模拟配置开关 ---
    common.SIMULATE_MODE = False
    common.HandHaveBox = False 
    
    common.start_background_services() 
    
    while common.ChestOrg is None:
        time.sleep(0.1)
    
    global current_stage
    _ = input(f'准备就绪，将从任务:{current_stage}开始，按下回车启动')
    common.start_time = time.time()

    # 1. 状态映射表
    stage_map = {
        "base_to_task1": base_to_task1,
        "base_to_task2": base_to_task2,
        "base_to_task3": base_to_task3,
        "base_to_task4": base_to_task4,
        "task1": task1,
        "task1_to_task2": task1_to_task2,
        "task2": task2,
        "task2_to_task3": task2_to_task3,
        "task3": task3,
        "task3_to_task4": task3_to_task4,
        "task4": task4,
    }
    
    
    # current_stage = "task4"
    is_jump_mode = False
    last_printed_stage = ""

    # --- 在 try 之前，确保定义好订阅回调 ---
    def voice_callback(msg):
        """ROS 订阅回调：接收 voice_control_node 发来的汉字 Key"""
        import robot_common as common
        # 这里的 msg.data 就是 "向右转动一步"、"暂停" 等 Key
        common.voice_action_name = msg.data
        common.voice_signal = True

    # 注册订阅者 (话题名必须与 voice_control_node.py 一致)
    rospy.Subscriber('/voice_cmd_raw', String, voice_callback)

    try:
        while not rospy.is_shutdown() and current_stage != "exit":
            
            # --- 1. 语音监听逻辑 ---
            if common.voice_signal:
                voice_word = common.voice_action_name
                common.log(f"🎤 收到语音指令: {voice_word}")

                from action import VOICE_CONTROL_MAP
                if voice_word in VOICE_CONTROL_MAP:
                    target, cmd_type = VOICE_CONTROL_MAP[voice_word]
                    
                    if cmd_type == "sys":
                        # 💡 注意：这里根据你 action.py 里的第一个值进行匹配
                        if target == "暂停": 
                            common.stop_all_tasks = True
                            common.log("🛑 语音确认：正在执行任务挂起...")
                        elif target == "继续":
                            common.stop_all_tasks = False
                            common.log("▶️ 语音确认：任务继续执行")
                    
                    elif cmd_type == "jump":
                        if common.stop_all_tasks: common.stop_all_tasks = False
                        current_stage = target
                        is_jump_mode = True
                        common.log(f"🎯 语音确认：跳转至 {target}")
                    
                    elif cmd_type == "action":
                        with common.action_lock:
                            do(target)
                
                # 处理完后重置信号
                common.voice_signal = False
                common.voice_action_name = ""
                continue

            # --- 2. 暂停拦截 ---
            if common.stop_all_tasks:
                time.sleep(0.1)
                continue

            # --- 3. 打印状态大框 ---
            if current_stage != last_printed_stage:
                common.log(f"\n\033[1;35m{'='*60}\033[0m") 
                common.log(f"\033[1;35m🚀 当前执行: {current_stage} | 模式: {'语音跳转' if is_jump_mode else '自动流'}\033[0m")
                common.log(f"\033[1;35m{'='*60}\033[0m")
                last_printed_stage = current_stage

            # --- 4. 执行当前函数并获取结果 ---
            func = stage_map.get(current_stage)
            if func:
                result = func(is_jump_mode)
                
                # 如果函数返回了下一个阶段的名字，则跳转
                if isinstance(result, str):
                    common.log(f"\n✅ 任务{current_stage} 完成！跳转至 {result}")
                    current_stage = result
                    is_jump_mode = False 
            
            time.sleep(0.1)

        common.log(f"\n\033[1;35m{'='*60}\033[0m") 
        common.log(f"\033[1;35m🌟 [SUCCESS] 任务全部完成！恭喜通关！🌟\033[0m")
        common.log(f"\033[1;35m{'='*60}\033[0m\n")

    finally:
        rospy.signal_shutdown("Mission Complete")
        sys.stdout.flush()
        os._exit(0)

if __name__ == '__main__':
    main()