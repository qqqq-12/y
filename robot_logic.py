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

# ==========================================
# 现场参数全部集中在 site_config.py 中，比赛当天只改那一个文件
# ==========================================
from site_config import (
    SHELF_LEVEL,
    BOOK_TAG,
    BOOK_ALIGN,
    BASKET_TAG,
    COLOR_KEY,
    STEPS,
    MATCH_TIME_LIMIT,
    START_STAGE,
    DEBUG_CATEGORY,
    DEBUG_COLOR,
    SIMULATE_MODE as CFG_SIMULATE_MODE,
    VOICE_WAIT_TIMEOUT,
)

current_stage = START_STAGE

# 读取任务板后保存的结果（task3 写入，task4 使用）
TASK_CATEGORY = None
TASK_COLOR = None


def wait_for_voice(target, timeout=VOICE_WAIT_TIMEOUT):
    """
    等待指定的语音启动指令。
    命中返回 True；超过 timeout 秒未命中则报警并自动继续（返回 False），避免永久卡死。
    """
    start = time.time()
    while not rospy.is_shutdown():
        if common.voice_signal:
            voice_word = common.voice_action_name
            common.voice_signal = False          # 消费信号
            if voice_word in VOICE_CONTROL_MAP:
                t, _ = VOICE_CONTROL_MAP[voice_word]
                if t == target:
                    common.log(f"🎙️ 指令匹配成功: '{voice_word}' -> {t}。开始任务！")
                    return True
                common.log(f"⏳ 收到指令({t})非目标指令，继续等待...")
        if time.time() - start > timeout:
            common.log(f"\033[1;31m⚠️ 等待语音({target})已超过 {timeout} 秒，自动继续本关！\033[0m")
            return False
        time.sleep(0.1)
    return False


task_step = "align-0"
def base_to_task1(is_jump=False):
    global task_step
    cfg = [0, (0.08, 0, 0), (0.05, 0.05, 8)]
    if task_step == "align-0":
        if common.align_to_tag(cfg):
            print("\n\033[1;33m🔄 Tag-0已对齐\033[0m")
            do("forward_q", STEPS["b1_forward"])
            task_step = "align-1"
    if task_step == "align-1":
        cfg = [1, (0.1843, 0, 0), (0.04, 0.04, 8)]   
        if common.align_to_tag(cfg):
            do("turnleft", STEPS["b1_turnleft"])
            do("forward_q", STEPS["b1_forward2"])
            return "task1"
    return False

base_to_task2_step = "align-1"
def base_to_task2(is_jump=False):
    global base_to_task2_step
    if base_to_task2_step == "align-1":
        # cfg = [1, (0.1843, 0, 0), (0.04, 0.04, 8)]
        # if common.align_to_tag(cfg):
        do("forward_q", STEPS["b2_forward"])
        base_to_task2_step = "align-5"
    if base_to_task2_step == "align-5":
        cfg = [5, (0.12, 0, 0), (0.04, 0.04, 3)]
        if common.align_to_tag(cfg):
            do("turnleft", STEPS["b2_turnleft"])
            do("forward_q", STEPS["b2_forward2"])
            base_to_task2_step = "align-3"
            return "task2"
    return False

def base_to_task3(is_jump=False):
    do("forward_q", STEPS["b3_forward"])
    return "task3"

base_to_task4_step = "forward5"
def base_to_task4(is_jump=False):
    global base_to_task4_step
    if base_to_task4_step == "forward5":
        # cfg = [1, (0.1843, 0, 0), (0.04, 0.04, 8)]
        # if common.align_to_tag(cfg):
        do("forward_q", STEPS["b4_forward"])
        base_to_task4_step = "align-5"
    if base_to_task4_step == "align-5":
        cfg = [5, (0.10, 0, 0), (0.05, 0.05, 8)]
        if common.align_to_tag(cfg):
            do("right", STEPS["b4_right"])
            return "task4"
    return False

def task1(is_jump=False):
    """第一关：推抹布任务"""
    cfg = [2, (0.16, 0, 0), (0.01, 0.02, 3)]
    if common.align_to_tag(cfg):
        common.log("\n\033[1;33m🔄 等待语音启动指令...\033[0m")
        wait_for_voice("release_task1")
        common.log("\033[1;32m🚀 正在前进并执行推抹布动作...\033[0m")
        do("forward_q", STEPS["t1_forward"])
        common.playmusic(10)
        do("left", STEPS["t1_left"])
        do("forward_s", 1)
        do("push_rag_p18", 1)
        return "task1_to_task2"
    return False

def task1_to_task2(is_jump=False):
    common.log("\n\033[1;33m🔄 等待语音启动指令...\033[0m")
    wait_for_voice("release_task2")
    do("right", STEPS["t1t2_right"])
    do("forward_q", STEPS["t1t2_forward"])
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
        do("box_turnright_q", STEPS["t2_turnright"])
    
    # 2. 对齐 Tag-4 放书
    cfg = [4, (0.17, 0, 0), (0.02, 0.04, 5)]
    if common.align_to_tag(cfg):
        common.log("\n\033[1;33m🔄 Tag-书架已对齐，开始前进...\033[0m")
        do("up_stair_1_good", 1)
        do("put_shelf_two" if SHELF_LEVEL == 2 else "put_shelf_one", 1)
        common.HandHaveBox = False
        common.playmusic(11)
        do("back", STEPS["t2_back"])
        do("down_stair_1_good", 1)
        return "task2_to_task3"
    return False

def task2_to_task3(is_jump=False):
    cfg = [4, (0.24, 0, 8), (0.04, 0.06, 6)]
    if common.align_to_tag(cfg):
        common.log("\n\033[1;33m🔄 Tag-书架已对齐，开始撤离...\033[0m")
        do("right", STEPS["t2t3_right"])
        return "task3"
    return False

def task3(is_jump=False):
    """第三关：OCR识别"""
    global TASK_CATEGORY, TASK_COLOR
    cfg = [5, (0.08, 0, 0), (0.04, 0.04, 3)]
    # 1. 首先完成对齐
    if common.align_to_tag(cfg):
        # 调试模式：跳过语音+OCR，直接用指定结果
        if DEBUG_CATEGORY:
            TASK_CATEGORY, TASK_COLOR = DEBUG_CATEGORY, DEBUG_COLOR
            common.log(f"\n\033[1;36m🐛 [调试] 跳过OCR：类别={TASK_CATEGORY}, 颜色={TASK_COLOR}\033[0m")
            return "task3_to_task4"
        common.log("\n\033[1;33m🔄 等待语音启动指令...\033[0m")
        wait_for_voice("release_task3")
        do("forward_q", STEPS["t3_forward"])
        do("forward", 1)
        do("lean_back", 1)
        time.sleep(1)
        common.log("\033[1;36m📷 正在读取公告牌信息...\033[0m")
        category, color_name = common.get_ocr_result()
        # 保存任务板结果，交给 task4（学无止境）使用
        TASK_CATEGORY, TASK_COLOR = category, color_name
        common.log(f"\n\033[1;32m✅ OCR 结果：类别={category}, 颜色={color_name}\033[0m")
        if TASK_CATEGORY == "未知" or TASK_COLOR == "未知":
            common.log("\033[1;31m⚠️ 任务板识别失败，task4 将使用默认参数，请现场检查！\033[0m")
        time.sleep(2)
        do("end_lean_back", 1)
        return "task3_to_task4"
        
    return False

def task3_to_task4(is_jump=False):
    # 建议还是先对齐5再右移
    # 调试模式跳过OCR时，机器人没有前移贴近公告牌，因此无需后退
    if not DEBUG_CATEGORY:
        do("back", STEPS["t3t4_back"])
    do("right", STEPS["t3t4_right"])
    do("forward", STEPS["t3t4_forward"])
    return "task4"

task4_step = "picking"
def task4(is_jump=False):
    global task4_step
    # 依据"读取任务板"的结果决定：搬哪本书、送到哪个颜色的收纳筐
    book_tag = BOOK_TAG.get(TASK_CATEGORY, BOOK_TAG["少儿"])
    basket_tag = BASKET_TAG.get(TASK_COLOR, BASKET_TAG["蓝色"])
    basket_color = COLOR_KEY.get(TASK_COLOR, "blue")
    # --- 步骤 1：抱书 (仅在手里没书时执行) ---
    if task4_step == "picking":
        common.log(f"📚 任务板：{TASK_CATEGORY}类书 -> {TASK_COLOR}收纳筐 | 书Tag={book_tag} 筐Tag={basket_tag}")
        target, tol = BOOK_ALIGN.get(book_tag, BOOK_ALIGN[6])
        cfg = [book_tag, target, tol]
        if common.align_to_tag(cfg):
            do("forward_q", STEPS["t4_forward"])
            do("pick_box", 1)
            do("box_back", 1)
            # 抱完之后，务必在 pick_box 内部或这里设置 HandHaveBox = True
            common.HandHaveBox = True 
            do("box_turnright_q", STEPS["t4_turnright"])
            task4_step = "approaching"
            return "task4"
        else:
            return False # 没对准书，退出等待下次循环

    # --- 步骤 2 & 3：趋近与投递 (仅在手里有书时执行) ---
    if task4_step == "approaching":
        common.HandHaveBox = True 
        # 这一步会阻塞，直到看到目标 Tag 或靠近目标颜色
        common.walk_to_bigbox(basket_color, basket_tag)
        common.log("🚩 从颜色大盒子，切换到Tag对齐")
        task4_step = "aligning"

    if task4_step == "aligning":
        # 投递
        common.HandHaveBox = True 
        cfg = [basket_tag, (0.08, 0, 180), (0.05, 0.02, 5)]
        if common.align_to_tag(cfg):
            do("box_forward_q", STEPS["t4_forward2"])   #refy这里改成抱cube快走
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

    # --- 模拟配置开关（统一在 site_config.py 中）---
    common.SIMULATE_MODE = CFG_SIMULATE_MODE
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
    timeup_warned = False

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

            # --- 2.5 比赛总时长提醒（赛题规定 8 分钟）---
            elapsed = time.time() - common.start_time
            if not timeup_warned and elapsed > MATCH_TIME_LIMIT - 60:
                timeup_warned = True
                common.log(f"\033[1;31m⏰ 距规定时长仅剩约 {int(MATCH_TIME_LIMIT - elapsed)} 秒，"
                           f"优先保证已完成的任务！\033[0m")

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