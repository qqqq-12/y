#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os
from datetime import datetime

# 路径配置
sys.path.append("/home/sunrise/catkin_ws/src/aelos_smart_ros")
try:
    from leju import nodes, base_action, music
except ImportError:
    # 仅提供接口定义，不含任何 sleep 延迟
    class Mock:
        def action(self, name): pass
        def music_play(self, name): pass
        def node_initial(self): pass
    nodes, base_action, music = Mock(), Mock(), Mock()

# 加载公共配置
from action import ACTION_MAP, MUSIC_LIST

# 全局状态
HandHaveBox = False
last_status = "系统已就绪"
# 生成反向映射表：按键 -> Key
KEY_TO_ACTION = {info[1]: key for key, info in ACTION_MAP.items()}

def render_ui(mode, status):
    """渲染交互界面"""
    os.system('clear')
    h_tag = "\033[1;33m[ 抱箱状态 ]\033[0m" if HandHaveBox else "\033[1;32m[ 空手状态 ]\033[0m"
    
    if mode == "KEYBOARD":
        print(" 【终端控制】 " + h_tag)
        print("-" * 50)
        print("  移动: w/a/s/d/q/e  | 抱箱移动: rw/ra/rs/rd/rq/re")
        print("  动作: f (抓取) / rf (放下) / c (站立)")
        print("  音乐: u1, u2...    | 切换显示: m")
    else:
        print(" 【指令映射清单】")
        print("-" * 50)
        for k, v in sorted(ACTION_MAP.items()):
            print("  键位: {:<5} -> 动作: {}".format(v[1], k))
        print("-" * 50)
        print("  输入映射键位直接执行 | [ m ] 返回")

    print("\n 日志: " + status)
    sys.stdout.flush()

def main():
    global last_status, HandHaveBox
    nodes.node_initial()
    ui_mode = "KEYBOARD"

    while True:
        render_ui(ui_mode, last_status)
        
        try:
            # 获取输入，不再有额外的 sleep
            user_input = getattr(__builtins__, 'raw_input', input)(" >> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input: continue

        # 2. 音乐播放 (u1, u2...)
        if user_input.startswith('u') and user_input[1:].isdigit():
            m_idx = int(user_input[1:]) - 1
            if 0 <= m_idx < len(MUSIC_LIST):
                m_name = MUSIC_LIST[m_idx]
                last_status = "正在播放: " + m_name
                render_ui(ui_mode, last_status)
                music.music_play(m_name)
                last_status = "播放指令已发出"
            continue

        # 3. 动作执行核心
        if user_input in KEY_TO_ACTION:
            action_key = KEY_TO_ACTION[user_input]
            cmd_internal = ACTION_MAP[action_key][0]
            
            last_status = "执行中: " + action_key
            render_ui(ui_mode, last_status)
            
            # 直接调用硬件接口，不添加额外 sleep
            base_action.action(cmd_internal)
            
            # 自动维护搬运状态
            if action_key == "pickup_cube": HandHaveBox = True
            elif action_key == "putdown_cube": HandHaveBox = False
            
            last_status = "执行完成: " + action_key
        else:
            last_status = "错误: 未知指令 [" + user_input + "]"

    print("\n已安全退出")

if __name__ == "__main__":
    main()