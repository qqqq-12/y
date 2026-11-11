# -*- coding: utf-8 -*-
"""
============================================================
 赛前现场参数集中配置（比赛当天只改这一个文件）
============================================================
 本文件不 import 任何项目模块，可被 action.py / robot_common.py /
 robot_logic.py 任意引用，不会产生循环依赖。

 核对顺序建议：
   一、赛题变量  —— 官方"赛前调试阶段"公布，必须现场填
   二、颜色阈值  —— 换场地 / 换灯光 必调
   三、视觉对准  —— 换场地 / 换桌子高度 必调
   四、动作步数  —— 换机器人 必调
   五、流程参数
============================================================
"""

# ============================================================
# 一、赛题变量（赛题第 5 条：赛前调试阶段公布）
# ============================================================

# 1. 收纳任务：书放书架第几层（1 或 2）
SHELF_LEVEL = 2

# 2. 学无止境：任务板类别 -> 该书所在位置的 Tag 码
#    用 python debug_artag.py 实测后填写
BOOK_TAG = {
    "少儿": 6,
    "工具": 7,
    "文学": 8,
}

# 3. 学无止境：任务板颜色 -> 该颜色收纳筐的 Tag 码
BASKET_TAG = {
    "蓝色": 16,
    "黄色": 15,
    "绿色": 17,
}

# 任务板颜色中文 -> 颜色识别用的英文键（与 COLOR_RANGE 的 key 对应）
COLOR_KEY = {
    "蓝色": "blue",
    "黄色": "yellow",
    "绿色": "green",
}

# 4. 学无止境：每本书 Tag 对齐参数 (Tag码 -> ((目标X,目标Y,目标Yaw), (容差X,容差Y,容差Yaw)))
#    把机器人摆到正确的抱书位置，用 debug_artag.py 实测后填写目标值
BOOK_ALIGN = {
    6: ((0.039, -0.0135, 4.3), (0.03, 0.02, 5)),   # 少儿（实测）
    7: ((0.055, -0.002, -0.3),  (0.03, 0.02, 5)),   # 工具（实测，最终位置）
    8: ((0.064, -0.008, -1.7),  (0.03, 0.02, 5)),   # 文学（实测）
}


# ============================================================
# 二、颜色阈值（HSV）
#    场地光线不同会漂移。取色方法：
#      cd debug
#      python camera_shoot.py
#      python hsvSelectTools.py -i ./captured/xxx.jpg
# ============================================================
COLOR_RANGE = {
    'black':  [(0, 0, 0),      (180, 99, 70)],
    'yellow': [(12, 60, 0),    (37, 255, 255)],
    'blue':   [(100, 120, 0),  (117, 255, 255)],
    'green':  [(73, 96, 20),   (100, 255, 80)],
}


# ============================================================
# 三、视觉对准
# ============================================================

# --- 3.1 抱方块（收纳任务）的画面像素对准 ---
BOX_CONFIG = {
    'x': {
        'target': 320, 'tol': 40, 'big_step': 80,
        'pos_actions': ['right_s', 'right'],   # 误差为正：偏右，右移
        'neg_actions': ['left_s', 'left']      # 误差为负：偏左，左移
    },
    'y': {
        'target': 440, 'tol': 20, 'big_step': 60,
        'pos_actions': ['back_s', 'back_s'],   # 误差为正：太近，后退
        'neg_actions': ['forward_s', 'forward']  # 误差为负：太远，前进
    }
}

# 抱方块时屏蔽的图像区域（像素）：屏蔽上半部分和左侧，去掉干扰
# 换场地后若一直抓不到，优先检查这里是不是把真目标裁掉了
CUBE_MASK_ROWS = 240   # mask[0:CUBE_MASK_ROWS, :] = 0
CUBE_MASK_COLS = 130   # mask[:, 0:CUBE_MASK_COLS] = 0

# --- 3.2 走向颜色大盒子 ---
BIGBOX_CENTER_X = 320      # 图像中心 X
BIGBOX_TOLERANCE = 40      # 左右对齐容差（像素）
BIGBOX_STOP_Y = 420        # 色块 Y 超过该值视为已到达
BIGBOX_SWITCH_X = 0.30     # 看到目标 Tag 且 X 小于该值（米）则切换到 Tag 对齐

# --- 3.3 Tag 对齐策略表 ---
# 格式: (维度, 误差判断逻辑, 空手动作, 抱箱动作, 日志名称)
# 优先级从上到下。这里的阈值是"走几步能到"的经验值，换机器人必须重调，
# 否则会出现左右来回横跳（容差太小）或一股脑冲过去（容差太大）。
ALIGN_STRATEGY = [
    # 后退判断：实时值 < (目标值 - 阈值) -> 靠太近了
    ('x', lambda val, tar, tol: val < tar - 0.27,     'back',          'box_back',        "太近-后退"),
    ('x', lambda val, tar, tol: val < tar - 0.10,     'back',          'box_back',        "太近-后退"),
    ('x', lambda val, tar, tol: val < tar - 0.02,     'back_s',        'box_back_s',      "太近-后退"),
    # 大角度纠偏
    ('theta', lambda val, tar, tol: val > tar + 13,   'turnleft',      'box_turnleft',    "大偏-左转"),
    ('theta', lambda val, tar, tol: val < tar - 13,   'turnright',     'box_turnright',   "大偏-右转"),
    # 左右平移粗调
    ('y', lambda val, tar, tol: val > tar + 0.05,     'left',          'box_left',        "侧偏-左移"),
    ('y', lambda val, tar, tol: val < tar - 0.05,     'right',         'box_right',       "侧偏-右移"),
    # 远距离快速靠近
    ('x', lambda val, tar, tol: val > tar + 0.14,     'forward_q',     'box_forward_q',   "太远-快进"),
    # 角度微调
    ('theta', lambda val, tar, tol: val > tar + tol,  'turnleft_s',    'box_turnleft',    "微调-左转"),
    ('theta', lambda val, tar, tol: val < tar - tol,  'turnright_s',   'box_turnright',   "微调-右转"),
    # 平移微调
    ('y', lambda val, tar, tol: val > tar + tol,      'left_s',        'box_left_s',      "微调-左移"),
    ('y', lambda val, tar, tol: val < tar - tol,      'right_s',       'box_right_s',     "微调-右移"),
    # 最终接近（前后精度最大约 3cm，不能再小，否则超调）
    ('x', lambda val, tar, tol: val > tar + 0.08,     'forward',       'box_forward',     "微调-前进7cm"),
    ('x', lambda val, tar, tol: val > tar + tol,      'forward_s',     'box_forward_s',   "精调-前进2cm"),
]


# ============================================================
# 四、动作步数（换机器人必调）
#    同一句动作，不同机器步幅不同，靠调这里补偿。
#    理想做法：每段路先用 Tag 对齐，这里的步数只做最后的微调。
# ============================================================
STEPS = {
    # --- 基地 -> 任务1（茶水区 / 清洁桌面）---
    "b1_forward":       1,
    "b1_turnleft":      5,
    "b1_forward2":      2,

    # --- 基地 -> 任务2（收纳区）---
    "b2_forward":       5,
    "b2_turnleft":      8,
    "b2_forward2":      5,

    # --- 基地 -> 任务3（任务发布区）---
    "b3_forward":       5,

    # --- 基地 -> 任务4（学无止境区）---
    "b4_forward":       5,
    "b4_right":         10,

    # --- 清洁桌面 ---
    "t1_forward":       2,
    "t1_left":          2,

    # --- 清洁 -> 收纳 衔接 ---
    "t1t2_right":       5,
    "t1t2_forward":     1,

    # --- 收纳 ---
    "t2_turnright":     8,
    "t2_back":          1,

    # --- 收纳 -> 任务板 衔接 ---
    "t2t3_right":       12,

    # --- 任务板 ---
    "t3_forward":       2,

    # --- 任务板 -> 学无止境 衔接 ---
    "t3t4_back":        3,
    "t3t4_right":       18,
    "t3t4_forward":     1,

    # --- 学无止境 ---
    "t4_forward":       1,
    "t4_turnright":     8,
    "t4_forward2":      3,
}


# ============================================================
# 五、流程参数
# ============================================================

# 单场比赛总时长（秒）。赛题规定 8 分钟，剩余 60 秒时终端会提示。
MATCH_TIME_LIMIT = 8 * 60

# 起始关卡（调试用）：base_to_task1 / task1 / task2 / task3 / task4 ...
START_STAGE = "task3"

# 调试开关：跳过OCR，直接指定任务板结果（None 表示走正常OCR流程）
DEBUG_CATEGORY = "工具"   # "少儿" / "工具" / "文学"
DEBUG_COLOR = "蓝色"      # "蓝色" / "黄色" / "绿色"

# 模拟模式：True 只识别不发动作，用于快速验证流程逻辑
SIMULATE_MODE = False

# 文字识别开关
USE_OCR = True

# 等待语音启动指令的超时时间（秒）。
# 超时后只在终端报警并自动继续本关，不会永久卡死。
# 现场语音识别不稳时可适当调大；裁判要求"必须听到指令才开始"时也要调大。
VOICE_WAIT_TIMEOUT = 30

# 单个 Tag 连续对齐失败的最大轮次（主循环约 0.6 秒/轮，100 轮≈1 分钟）。
# 超过后强制放行并报警，避免在一个 Tag 上卡到比赛结束。
ALIGN_MAX_RETRY = 100
