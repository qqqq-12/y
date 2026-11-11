#!/usr/bin/python
# pyright: reportUndefinedVariable=false
# -*- coding: utf-8 -*-
import time
import cv2
import threading
import numpy as np
import rospy
import math
from functools import wraps
import sys
import os
import tf
from ar_track_alvar_msgs.msg import AlvarMarkers

sys.path.append("/home/sunrise/catkin_ws/src/aelos_smart_ros")
from leju import base_action,music   # type: ignore
from datetime import datetime

from action import ACTION_MAP,color_range,MUSIC_LIST
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


# 保证 cv_bridge 能找到 ROS 库
ros_path = '/opt/ros/noetic/lib'
if ros_path not in os.environ.get('LD_LIBRARY_PATH', ''):
    os.environ['LD_LIBRARY_PATH'] = os.environ.get('LD_LIBRARY_PATH', '') + ':' + ros_path

debug_pub = None
# 实例化桥接器，用于将 OpenCV 格式转换回 ROS 格式
bridge = CvBridge()

mask_pub = None


voice_signal = False      # 语音信号：是否有语音指令要插播
voice_action_name = ""    # 存放语音识别到的动作名
action_lock = threading.Lock() # 确保发指令不冲突
stop_all_tasks = False

USE_OCR = True    # 文字识别开关
# --- 模拟模式开关：True 为手动模拟（不发指令），False 为真实执行 ---
SIMULATE_MODE = False

#定义一些参数
ChestOrg = None

HaveBox = False
huave_box = None
chest_circle_x = None
chest_circle_y = None

KEY_TO_ACTION = {info[1]: key for key, info in ACTION_MAP.items()}
def do(name, n=1):
    """
    统一动作执行入口。
    name: 必须是 ACTION_MAP 里的英文 Key (如 "forward")
    """
    global HandHaveBox, last_status
    
    if name not in ACTION_MAP:
        log("\033[1;31m❌ 动作未定义: {}\033[0m".format(name))
        return

    cmd = ACTION_MAP[name][0]  # 获取指令名，忽略按键位

    for i in range(n):
        now = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        count_str = " ({}/{})".format(i+1, n) if n > 1 else ""
        
        # 打印执行日志
        tag = "[模拟执行]" if SIMULATE_MODE else "[真实执行]"
        log("🤖 {} {} -> {}".format(tag, name, cmd + count_str))

        if not SIMULATE_MODE:
            try:
                base_action.action(cmd)
                timeout = 10 
                while ChestOrg is None and timeout > 0:
                    time.sleep(0.05)
                    timeout -= 1
            except Exception as e:
                log("⚠️ 硬件异常: {}".format(e))
                break
        else:
            time.sleep(1)
    
    # 自动维护 HandHaveBox 状态
    if name == "pickup_cube": HandHaveBox = True
    elif name == "putdown_cube": HandHaveBox = False

def playmusic(id):
    """
    id: 列表索引。注意：传 1 代表播放列表第 1 项（索引 0）。
    为了对应你注释里的 #1, #12，我们内部减 1。
    """
    try:
        # 如果你习惯按注释的编号传参（1-12），这里需要减 1
        idx = id - 1 
        if 0 <= idx < len(MUSIC_LIST):
            file_name = MUSIC_LIST[idx]
            # 注意：如果 music_play 需要的是完整文件名，
            # 确保 MUSIC_LIST 里的字符串和 SD 卡里的文件名一致。
            music.music_play(file_name)
            log(f"🎵 播放语音: {file_name}")
        else:
            log(f"⚠️ 音效编号 {id} 超出范围")
    except Exception as e:
        log(f"⚠️ 播放异常: {e}")

# --- 全局变量初始化 ---
ChestOrg = None  # 原始图像
ret = False      # 图像状态标志位

def chest_image_callback(msg):
    """
    代替原 ImgConverter 类的回调函数
    直接将 ROS 消息转换为 OpenCV 格式并存入全局变量
    """
    global ChestOrg, ret
    try:
        # 1. 快速转换：字节流 -> numpy -> reshape
        img_np = np.frombuffer(msg.data, dtype=np.uint8)
        img_cv2 = img_np.reshape((msg.height, msg.width, 3)) 
        
        # 2. 颜色空间转换：ROS(RGB) -> OpenCV(BGR)
        ChestOrg = cv2.cvtColor(img_cv2, cv2.COLOR_RGB2BGR)
        ret = True
    except Exception as e:
        ret = False

def get_img():
    global ChestOrg, debug_pub, bridge
    
    # 1. 建立订阅：直接指向上面定义的 callback
    rospy.Subscriber('/usb_cam_chest/image_raw', Image, chest_image_callback)
    
    print("🚀 摄像头感知系统已启动...") 
    camera_shown = False 

    # 2. 循环处理与 Debug 发布
    while not rospy.is_shutdown():
        if ChestOrg is not None:
            if not camera_shown:
                print("✅ 摄像头数据流已就绪")
                camera_shown = True
            
            # --- 发布 Debug 画面 ---
            if debug_pub is not None:
                try:
                    # 注意：如果网页显示发黄，这里可以用 cv2.cvtColor(ChestOrg, cv2.COLOR_BGR2RGB)
                    debug_pub.publish(bridge.cv2_to_imgmsg(ChestOrg, "rgb8"))
                except:
                    pass
            
            time.sleep(0.05) # 20fps 的处理频率
        else:
            # 还没有数据时，稍微多等一下
            time.sleep(0.2)

BOX_CONFIG = {
    'x': {
        'target': 320, 'tol': 40, 'big_step': 80, 
        'pos_actions': ['right_s', 'right'], # 误差为正，说明偏右，执行右移
        'neg_actions': ['left_s', 'left']    # 误差为负，说明偏左，执行左移
    },
    'y': {
        'target': 440, 'tol': 20, 'big_step': 60,
        'pos_actions': ['back_s', 'back_s'],  # 误差为正，说明太近，执行后退
        'neg_actions': ['forward_s', 'forward'] # 误差为负，说明太远，执行前进
    }
}
def align_and_pick_cube(color_name):
    """
    识别特定颜色方块、纠偏并完成抓取 (紧凑对齐版)
    """
    global chest_circle_x, chest_circle_y, HandHaveBox
    
    # --- 1. 感知层 ---
    img = ChestOrg
    if img is None: return False

    box_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR) 
    box_img_hsv = cv2.cvtColor(box_img, cv2.COLOR_BGR2HSV)
    box_img_mask = cv2.inRange(box_img_hsv, color_range[color_name][0], color_range[color_name][1])
    
    # 强制抹除上半和左半部分的“黑色干扰”
    box_img_mask[0:240, :] = 0
    box_img_mask[:, 0:130] = 0

    mask_cleaned = cv2.erode(box_img_mask, np.ones((3, 3), np.uint8))
    mask_cleaned = cv2.dilate(mask_cleaned, np.ones((5, 5), np.uint8))

    contours, _ = cv2.findContours(mask_cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        if int(time.time() * 10) % 20 == 0: 
            log(f"\033[1;34m🔍 正在寻找 {color_name} 方块...\033[0m")
        return False

    max_contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(max_contour) < 200: return False

    (chest_circle_x, chest_circle_y), _ = cv2.minEnclosingCircle(max_contour)
    current = {'x': chest_circle_x, 'y': chest_circle_y}

    # --- 2. 格式化工具 (与 Tag 对齐风格一致) ---
    RED, BLUE, RESET = "\033[1;31m", "\033[1;34m", "\033[0m"

    def get_axis_str(dim):
        val = current[dim]
        tar = BOX_CONFIG[dim]['target']
        tol = BOX_CONFIG[dim]['tol']
        color = BLUE if abs(val - tar) <= tol else RED
        # 结果类似于: (330/320±30)
        inner = f"{color}{val:>3.0f}{BLUE}/{tar:>3.0f}±{tol:>2.0f}{RESET}"
        return f"{BLUE}{dim.upper()}:({inner}{BLUE}){RESET}"

    # --- 3. 决策与对齐打印 ---
    # 按照优先级遍历维度
    for dim in ['x', 'y']:
        conf = BOX_CONFIG[dim]
        val = current[dim]
        error = val - conf['target']

        if abs(error) > conf['tol']:
            # 确定动作
            step_idx = 1 if abs(error) > conf['big_step'] else 0
            if error < 0:
                action_cmd = conf['neg_actions'][step_idx]
                label = "太偏左" if dim == 'x' else "太远"
            else:
                action_cmd = conf['pos_actions'][step_idx]
                label = "太偏右" if dim == 'x' else "太近"
            
            # 生成对齐行
            head = f"{BLUE}[方块对齐]-{color_name} {label:<5} | 执行:{action_cmd:<10} | {RESET}"
            line = f"{head}{get_axis_str('x')}  {get_axis_str('y')}"
            log(line)
            do(action_cmd)
            return False 

    # --- 4. 执行层 ---
    log(f"\n\033[1;32m🎯 坐标达标! X:{chest_circle_x:.0f} Y:{chest_circle_y:.0f} -> 开始抱箱\033[0m")
    do("pick_box", 1)
    HandHaveBox = True
    return True


class TagConverter():
    def __init__(self):
        self.sub = rospy.Subscriber('/chest/ar_pose_marker', AlvarMarkers, self.sub_cb)
        self.markers = []

    def sub_cb(self, msg):
        markers_load = []
        # 处理时间戳，增加判空保护
        time_sec = msg.header.stamp.secs if msg.header.stamp else 0
        
        for marker in msg.markers:
            pos = marker.pose.pose.position
            quat = marker.pose.pose.orientation

            # 四元数转欧拉角
            rpy = tf.transformations.euler_from_quaternion([quat.x, quat.y, quat.z, quat.w])
            rpy_arc = [0, 0, 0]
            for i in range(len(rpy)):
                rpy_arc[i] = rpy[i] / math.pi * 180

            markers_load.append([marker.id, pos.x, pos.y, rpy_arc[2], time_sec])

        self.markers = markers_load.copy()

    def get_all_markers(self):
        """
        获取当前视野中所有识别到的标签列表
        返回格式: [[ID, x, y, yaw, time], ...]
        """
        # 返回副本，防止主程序修改列表影响到类内部的回调
        return self.markers.copy() if self.markers else []

    def get_nearest_marker(self):
        # 输入多帧采样累积的标签列表，通过勾股定理计算并返回其中物理距离最近的 [ID, x, y, yaw] 数据列表，若无目标则返回空列表 []
        accumulated_markers = []
        # 采样 20 次以过滤视觉抖动
        for _ in range(20):
            time.sleep(0.01)
            accumulated_markers += self.markers
        if not accumulated_markers:
            return []
        nearest_marker = None
        min_distance = float('inf') # 初始化为无穷大
        for marker in accumulated_markers:
            # marker[1] 是 x, marker[2] 是 y
            # 计算欧氏距离：x^2 + y^2 (开方不影响大小比较，可以省略以提高性能)
            dist_sq = marker[1]**2 + marker[2]**2
            if dist_sq < min_distance:
                min_distance = dist_sq
                nearest_marker = marker
        return nearest_marker if nearest_marker else []

    def get_marker_by_id(self, target_id):
        """
        通过 ID 获取指定的标签数据
        """
        # 复制快照以保证线程安全
        current_markers = self.markers.copy()
        
        for marker in current_markers:
            # marker[0] 是 ID
            if marker[0] == target_id:
                return marker
        return []



import time

# 初始化为 0
start_time = 0

def get_time_stamp():
    """计算相对于 start_time 的分:秒"""
    global start_time
    if start_time == 0:
        return "0:00:000"
    
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    return f"{minutes}:{seconds:02d}"

def log(message):
    ts = get_time_stamp()
    # \r 是回到行首，\033[K 是清除从光标到行尾的内容
    prefix = "\r\033[K" 
    
    if isinstance(message, str) and message.startswith('\n'):
        # 处理带换行符的消息：换行符放在最前面，然后接清行指令
        print('\n' + prefix + f"[{ts}] {message.lstrip()}")
    else:
        print(prefix + f"[{ts}] {message}")

# --- artag码动作策略配置表 (按照你的精髓：直接比对实时值与目标值) ---
# 格式: (维度, 误差判断逻辑, 空手动作, 抱箱动作, 日志名称)  #策略表，决定不同位置触发动作的优先级。
STRATEGY_TABLE = [
    # 1. 后退判断：实时值 < (目标值 - 容差) -> 说明靠太近了
    ('x', lambda val, tar, tol: val < tar - 0.27,       'back',       'box_back',  "太近-后退"),
    ('x', lambda val, tar, tol: val < tar - 0.10,       'back',       'box_back',  "太近-后退"),  
    ('x', lambda val, tar, tol: val < tar - 0.02,       'back_s',       'box_back_s',  "太近-后退"), 
    # 2. 大角度纠偏：直接看角度绝对偏差是否超过太多 (强制纠偏)
    ('theta', lambda val, tar, tol: val > tar + 13,    'turnleft',    'box_turnleft', "大偏-左转"),
    ('theta', lambda val, tar, tol: val < tar - 13,    'turnright',    'box_turnright', "大偏-右转"),
    # 3. 左右平移粗调：实时 y > 目标 y + 容差 + 0.05
    ('y', lambda val, tar, tol: val > tar + 0.05, 'left',    'box_left', "侧偏-左移"),
    ('y', lambda val, tar, tol: val < tar - 0.05, 'right',    'box_right', "侧偏-右移"),
    # 4. 远距离快速靠近：实时 x > 目标 x + 0.2
    ('x', lambda val, tar, tol: val > tar + 0.14,         'forward_q',    'box_forward_q',     "太远-快进"),
    # 5. 角度微调
    ('theta', lambda val, tar, tol: val > tar + tol,    'turnleft_s',    'box_turnleft', "微调-左转"),
    ('theta', lambda val, tar, tol: val < tar - tol,    'turnright_s',    'box_turnright', "微调-右转"),
    # 6. 平移微调
    ('y', lambda val, tar, tol: val > tar + tol,         'left_s',    'box_left_s', "微调-左移"),
    ('y', lambda val, tar, tol: val < tar - tol,         'right_s',    'box_right_s', "微调-右移"),
    # 7. 最终接近
    ('x', lambda val, tar, tol: val > tar + 0.08,         'forward',      'box_forward',      "微调-前进7cm"),  #此处前后精度最大为3，不能再小了，否则会超调
    ('x', lambda val, tar, tol: val > tar + tol,         'forward_s',      'box_forward_s',      "精调-前进2cm"),
]
    
tag_inst = TagConverter()
def align_to_tag(cfg):
    """
    极致紧凑对齐版：
    1. 数值内部 (8.1/8.0±2.0) 紧凑无空格。
    2. X, Y, YAW 三组数据之间保持垂直对齐。
    3. 全行仅蓝红两色。
    """
    # 1. 解包参数
    target_tag, target_pose, tolerances_tuple = cfg
    x_off, y_off, t_off = target_pose
    x_tol, y_tol, t_tol = tolerances_tuple
    
    # 2. 获取标签实时信息
    marker = tag_inst.get_marker_by_id(target_tag)
    if len(marker) == 0:
        if int(time.time() * 10) % 20 == 0: 
             log(f"\033[1;34m⚠️ 正在搜索 Tag {target_tag}...\033[0m")
        return False

    # 3. 解析实时值
    dis_x, dis_y, theta = marker[1], marker[2], marker[3] + 90
    
    current_values = {'x': dis_x, 'y': dis_y, 'theta': theta}
    offsets = {'x': x_off, 'y': y_off, 'theta': t_off}
    tolerances = {'x': x_tol, 'y': y_tol, 'theta': t_tol}

    # 4. 颜色常量
    RED = "\033[1;31m"
    BLUE = "\033[1;34m"
    RESET = "\033[0m"

    # 5. 核心：构造紧凑的轴信息字符串
    def get_axis_str(dim):
        val, tar, tol = current_values[dim], offsets[dim], tolerances[dim]
        is_ok = abs(val - tar) <= tol
        
        # 转换单位
        v_f = val * 100 if dim != 'theta' else val
        t_f = tar * 100 if dim != 'theta' else tar
        l_f = tol * 100 if dim != 'theta' else tol

        # 实时值颜色判定
        v_color = BLUE if is_ok else RED
        
        # 内部紧凑拼接，不留任何多余空格
        # 结果类似于: (8.1/8.0±2.0)
        inner_content = f"{v_color}{v_f:.1f}{BLUE}/{t_f:.1f}±{l_f:.1f}{RESET}"
        full_axis_str = f"{BLUE}({inner_content}{BLUE}){RESET}"
        
        return full_axis_str

    # 6. 预生成 X, Y, YAW (每个整体占固定宽度，保证列对齐)
    # 给整体加宽度，确保 X/Y/YAW 的起始位置固定
    str_x = get_axis_str('x')
    str_y = get_axis_str('y')
    str_yaw = get_axis_str('theta')

    # 7. 策略匹配与动作执行
    for dim, check_logic, empty_func, box_func, label in STRATEGY_TABLE:
        cur_val, cur_off, cur_tol = current_values[dim], offsets[dim], tolerances[dim]
        
        if check_logic(cur_val, cur_off, cur_tol):
            func_to_run = box_func if HandHaveBox else empty_func
            
            # --- 紧凑头部 ---
            head = f"{BLUE}[Tag对齐-{target_tag}] {label:<5} | 执行:{func_to_run:<12} | {RESET}"
            
            # --- 垂直对齐：通过对齐前缀和整体宽度 ---
            # 这里的 22 是估算的整体字符串长度（包含不可见的颜色代码）
            # 由于颜色代码占位数但不占显示位，我们手动拼接
            line = f"{head}{BLUE}X:{RESET}{str_x}  {BLUE}Y:{RESET}{str_y}  {BLUE}YAW:{RESET}{str_yaw}"

            # --- 替换原来的 globals()[func_to_run](1) ---
            # from robot_common import do # 确保能调用到
            log(line)
            
            if func_to_run:
                # 💡 既然 func_to_run 是字符串（如 "forward_q"），直接传给 do
                do(func_to_run, 1) 
            
            return False

    # 8. 对齐完成
    log(f"\n\033[1;32m✅ Tag-{target_tag} 码已对齐 (X:{dis_x*100:.1f} Y:{dis_y*100:.1f} YAW:{theta:.1f})\033[0m")
    return True


def walk_to_bigbox(color_name, target_tag):
    """
    【全独立版】识别颜色、监控Tag、自动趋近。
    不依赖外部 find_box，内部完成所有图像计算。
    """
    global HandHaveBox, ChestOrg
    tag_reader = TagConverter() 
    
    # --- 寻物参数配置 ---
    CENTER_X = 320      # 图像中心 X 坐标
    TOLERANCE = 40      # 左右对齐容差
    
    log(f"\n\033[1;35m--- 开启趋近模式: 目标颜色 [{color_name}] | 监控Tag: [{target_tag}] ---\033[0m")

    while not rospy.is_shutdown():
        # --- 1. 优先级最高：Tag 截断检测 ---
        marker = tag_reader.get_marker_by_id(target_tag)
        if len(marker) > 0:
            tag_x = marker[1]
            # 只有当 ID 匹配 且 X 坐标进入 0.30 以内时才切逻辑
            if abs(tag_x) < 0.30:
                log(f"\n\033[1;32m🛑 看到目标 Tag [{target_tag}] 且位置达标 (X:{tag_x:.2f})，切换至对齐！\033[0m")
                break 
            else:
                # 虽然看到了码，但太偏了，继续靠颜色微调
                if int(time.time() * 10) % 20 == 0:
                    log(f"🔍 已发现 Tag {target_tag}，但位置偏远 (X:{tag_x:.2f})，继续趋近...")

        # --- 2. 图像获取与预处理 (原本 find_box 的逻辑) ---
        img = ChestOrg
        if img is None:
            time.sleep(0.1)
            continue

        # 转换颜色空间并创建掩码
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)    #如果颜色反了，这里就改BGR
        mask = cv2.inRange(hsv, color_range[color_name][0], color_range[color_name][1])
        
        # 简单形态学处理（去噪）
        mask = cv2.erode(mask, np.ones((5, 5), np.uint8))
        mask = cv2.dilate(mask, np.ones((5, 5), np.uint8))


        # === 插入这段代码进行排查 ===
        if mask_pub is not None and mask is not None:
            try:
                # 注意：mask 是二值化黑白图，必须用 mono8 编码
                mask_msg = bridge.cv2_to_imgmsg(mask, "mono8")
                mask_pub.publish(mask_msg)
                # log("DEBUG: 已向 /usb_cam_chest/image_mask 发送一帧数据")
            except Exception as e:
                log(f"DEBUG: 发布 Mask 失败: {e}")

        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        bx, by = None, None
        if len(contours) > 0:
            # 找到面积最大的色块
            max_cnt = max(contours, key=cv2.contourArea)
            if cv2.contourArea(max_cnt) > 200: # 过滤极小噪点
                (bx, by), _ = cv2.minEnclosingCircle(max_cnt)

        # --- 3. 调试画面绘制 (直接发布到 debug_pub) ---
        if debug_pub is not None:
            debug_show = img.copy()
            # 画两条黄色参考线
            cv2.line(debug_show, (CENTER_X - TOLERANCE, 0), (CENTER_X - TOLERANCE, 480), (0, 255, 255), 1)
            cv2.line(debug_show, (CENTER_X + TOLERANCE, 0), (CENTER_X + TOLERANCE, 480), (0, 255, 255), 1)
            
            if bx is not None:
                cv2.circle(debug_show, (int(bx), int(by)), 10, (0, 255, 0), -1)
                cv2.putText(debug_show, f"{color_name} X:{int(bx)}", (int(bx), int(by)-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            else:
                cv2.putText(debug_show, "SEARCHING COLOR...", (200, 240), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            try:
                debug_pub.publish(bridge.cv2_to_imgmsg(debug_show, "bgr8"))
            except: pass

        # --- 4. 决策与动作执行 ---
        RED    = "\033[1;31m"   # 不达标红
        WHITE  = "\033[1;37m"   # 基础白
        BLUE   = "\033[1;34m"   # 标题蓝
        PURPLE = "\033[1;35m"   # 模式紫
        RESET  = "\033[0m"

        prefix = f"{BLUE}[趋近-{color_name}]{RESET}"

        if bx is None:
            log(f"{prefix} {BLUE}搜索中...| 执行:box_turnright_q | 状态: 未发现色块{RESET}")
            do("box_turnright_q", 1)
            time.sleep(0.2)
            continue

        error_x = bx - CENTER_X
        is_ok = abs(error_x) <= TOLERANCE

        # 判定动作
        if error_x < -TOLERANCE:
            label, exec_cmd, status = "左转", "box_turnleft", "偏左"
        elif error_x > TOLERANCE:
            label, exec_cmd, status = "右转", "box_turnright", "偏右"
        else:
            label, exec_cmd, status = "直走", "box_forward_q", "对正"

        # --- 核心：仅实时值变色，其余白色 ---
        v_color = WHITE if is_ok else RED
        # 结果类似于: (13.5/0.0±40.0) 其中仅 13.5 可能变红
        err_str = f"{BLUE}({v_color}{error_x:.1f}{BLUE}/0.0±{TOLERANCE})"
        
        # --- 构造对齐头部并打印 ---
        # 头部格式对标 [Tag对齐-6] 侧偏-左转 | 执行:turnleft
        head = f"{BLUE}[趋近-{color_name}] {label:<5} | {BLUE}执行:{exec_cmd:<14} | "
        log(f"{head}误差:{err_str} | 状态:{status}{RESET}")

        # --- 执行与保护 ---
        if by > 420:
            log(f"\033[1;32m🎯 已到达目标附近 (Y:{by:.1f})，停止趋近。\033[0m")
            break
            
        do(exec_cmd, 2 if label == "直走" else 1)


_ocr_engine = None

def init_ocr():
    global _ocr_engine
    if _ocr_engine is None:
        import os
        import sys
        
        # 1. 物理级拦截：备份并重定向 stderr
        stderr_fd = sys.stderr.fileno()
        copy_stderr_fd = os.dup(stderr_fd)
        
        try:
            with open(os.devnull, 'w') as devnull:
                # 开启静默
                os.dup2(devnull.fileno(), stderr_fd)
                
                # --- 核心修改：连 import 都要在静默区执行 ---
                from rapidocr_onnxruntime import RapidOCR
                _ocr_engine = RapidOCR(providers=['CPUExecutionProvider'])
                # ----------------------------------------
                
        except Exception as e:
            # 如果出错了，先恢复 stderr 再打印，否则你看不到报错信息
            os.dup2(copy_stderr_fd, stderr_fd)
            log(f"❌ RapidOCR 初始化失败: {e}")
        finally:
            # 2. 彻底恢复 stderr，确保后续正常的 log 和日志能看到
            os.dup2(copy_stderr_fd, stderr_fd)
            os.close(copy_stderr_fd)
            
        print("✅ OCR初始化成功")

def get_ocr_result():
    global ChestOrg, _ocr_engine
    if not USE_OCR:
        return ("模拟返回", "模拟返回")
    
    if _ocr_engine is None: init_ocr()

    try:
        # 推理并获取结果
        result, _ = _ocr_engine(ChestOrg)
        
        full_text = ""
        if result:
            # RapidOCR 结果结构：[ [[坐标], "文本", 置信度], ... ]
            full_text = "".join([str(line[1]) for line in result])
        
        log(f"🔍 识别结果: {full_text}")

        # 匹配逻辑
        found_cat = next((c for c in ["少儿", "文学", "工具"] if c in full_text), "未知")
        found_color = next((col for col in ["蓝色", "黄色", "绿色"] if col in full_text), "未知")
        
        if found_cat != "未知" and found_color != "未知":
            music.music_play(f"将{found_cat}类书籍搬到{found_color}收纳筐内")
                
        return (found_cat, found_color)
    except Exception as e:
        log(f"⚠️ OCR 异常: {e}")
        return ("错误", "错误")


def start_background_services():
    # 1. 启动摄像头线程 (原本就有的)
    # 只有当这个函数被调用时（此时主程序已经 init_node 了），才创建发布者
    global debug_pub,mask_pub
    if debug_pub is None:
        debug_pub = rospy.Publisher('/usb_cam_chest/image_debug', Image, queue_size=1)
        # log("✅ 调试图像发布者已注册")
    if mask_pub is None:
        mask_pub = rospy.Publisher('/usb_cam_chest/image_mask', Image, queue_size=1)
        # log("✅ 掩码图像发布者已注册")

    import threading 
    th2 = threading.Thread(target=get_img)
    th2.setDaemon(True)
    th2.start()
    # log("✅ 摄像头采集线程已启动")

    # 2. 只有开关打开，才初始化 OCR 引擎
    if USE_OCR:
        init_ocr()