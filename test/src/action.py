#!/usr/bin/python
# -*- coding: utf-8 -*-

# ACTION_MAP 结构: "Key": ["edu指令名称", "电脑操控按键", "动作幅度(厘米/度)"]
ACTION_MAP = {
    #空手系列
    "forward":      ["向前慢走1步", "w", "7"],
    "forward_s":    ["向前走2cm-稳定", "ws", "2"],
    "forward_q1":    ["向前快走1步", "wq1", "5"],
    "forward_q":    ["向前快走3步", "wq", "14"],
    
    "back":         ["向后慢走1步-修正前掌", "s", "10"],
    "back_3":         ["向后慢走3步", "s3", "27"],
    "back_s":       ["向后走2cm-稳定", "ss", "2"],
    "back_q":       ["向后快走1步", "sq", "4"],

    "left":         ["向左平移1步", "a", "5"],
    "left_s":       ["小左移", "as", "2"],
    "right":        ["向右平移1步", "d", "5"],
    "right_s":      ["小右移", "ds", "2"],

    "turnleft":     ["向左转动1步", "q", "22"],
    "turnleft_s":   ["小左转", "qs", "7"],
    "turnright":    ["向右转动1步", "e", "17"],
    "turnright_s":  ["小右转-镜像版2", "es", "2"],

    #抱方块的系列
    "box_forward":      ["抱快递慢走", "rw"],
    "box_forward_s":    ["box_forward_s_v3", "rws", "2"],   #"向前走2cm-稳定-抱箱"
    "box_forward_q":      ["向前快走3步-后仰10平手", "rwq"],

    "box_back":         ["向后慢走1步-修正前掌-抱箱", "rs"],   #"抱快递慢退"
    "box_back_s":       ["向后走2cm-稳定-抱箱", "rss", "2"],  #这个是4厘米
 
    "box_left":         ["抱快递左移", "ra", "5"],
    "box_left_s":       ["抱快递小左移-超紧", "ras", "2"],
    "box_right":        ["抱快递右移", "rd", "5"],
    "box_right_s":      ["抱快递小右移-超紧", "rds", "2"],

    "box_turnleft":     ["抱快递左转", "rq", "16"],
    # "box_turnleft_s":   ["", "rqs", "16"],  #抱快递右转
    "box_turnright":    ["抱快递右转2", "re"],
    # "box_turnright_s":  ["", "res"],
    "box_turnright_q":  ["box_turnright_q_v1", "req"],

    #特殊动作
    "pick_box":      ["配送-抱快递-夹得超紧", "f"],
    "put_box":     ["配送-放快递", "rf"],
    "up_stair_1_good":  ["无用-test上楼梯3","ri"],    #"上楼梯1厘米-抱箱-bx修正去头"
    "down_stair_1_good":       ["下楼梯1厘米-修正版", "k"],   #"上楼梯1厘米-双手下垂","上楼梯1厘米"

    "stand":  ["站立", "c"],
    "put_shelf_two":   ["书架-放二层3", "ro2"],    #"书架-放二层2",
    "put_shelf_one":   ["书架-放一层", "ro1"],
    "box_stand":   ["box_stand", "cf"],
    "drop_book_box":    ["配送-书籍箱子放快递", "rg"],
    "push_rag":  ["推抹布-贴胸准高慢延-11次", "p11"],
    # "push_rag_p10":  ["推抹布-消摩擦完美版-加循环-10次", "p10"],
    # "push_rag_p12":  ["推抹布-贴胸更高-12次", "p12"],
    "push_rag_p14":  ["推抹布-消摩擦完美版-加循环-14次", "p14"],
    "standup_front":  ["前倒地起身-超级自编完整版", "qian"],
    "standup_back":  ["后倒地起身-修正版", "hou"],
    "lean_back":    ["轻微后仰看字牌", "lean"], 
    "end_lean_back":    ["结束轻微后仰", "endlean"],   
    "shanglouti":    ["测试-动作", "endlean"],   

}

MUSIC_LIST = [
    "将少儿类书籍搬到绿色收纳筐内", #1
    "将少儿类书籍搬到蓝色收纳筐内",
    "将少儿类书籍搬到黄色收纳筐内",
    "将工具类书籍搬到绿色收纳筐内",
    "将工具类书籍搬到蓝色收纳筐内", #5
    "将工具类书籍搬到黄色收纳筐内",
    "将文学类书籍搬到绿色收纳筐内",
    "将文学类书籍搬到蓝色收纳筐内",
    "将文学类书籍搬到黄色收纳筐内",
    "开始清洁桌面",  #10
    "收纳完成",  #11
    "送达完毕", #12
]

# 语音映射表：[语音关键词] : [动作Key/跳转目标, 指令类型]
VOICE_CONTROL_MAP = {
    # 动作类
    "向前快走一步": ["forward_q", "action"],
    "向前慢走一步": ["forward", "action"],
    "向后慢走一步": ["back", "action"],
    "向左平移一步": ["left", "action"],
    "向右平移一步": ["right", "action"],
    "向左转动一步": ["turnleft", "action"],
    "向右转动一步": ["turnright", "action"],
    "抱箱子左转一步": ["box_turnleft", "action"],
    "抱箱子右转一步": ["box_turnright", "action"],
    "抱箱子猛烈右转一步": ["box_turnright_q", "action"],
    "上楼梯":       ["up_stair_1_good", "action"],
    "下楼梯":       ["down_stair_1_good", "action"],
    "站立":         ["stand", "action"],
    "放二层":       ["put_shelf_two", "action"],
    "推抹布":       ["push_rag", "action"],
    "前倒地起身":   ["standup_front", "action"],
    "后倒地起身":   ["standup_back", "action"],

    # 跳转类
    "跳转到第一关":       ["task1", "jump"],
    "跳转到第二关":       ["task2", "jump"],
    "跳转到第三关":       ["task3", "jump"],
    "跳转到第四关":       ["task4", "jump"],

    # 跳转类
    "基地到第一关":       ["base_to_task1", "jump"],
    "基地到第二关":       ["base_to_task2", "jump"],
    "基地到第三关":       ["base_to_task3", "jump"],
    "基地到第四关":       ["base_to_task4", "jump"],

    # 系统类
    "暂停":         ["暂停", "sys"],
    "继续":         ["继续", "sys"],
    "执行清洁桌面任务": ("release_task1", "sys"),
    "执行收纳任务": ("release_task2", "sys"),
    "识别任务板": ("release_task3", "sys"),
    
}

color_range = {
    'black':  [( 0, 0, 0 ),    ( 180, 99, 70 )],
    'yellow': [( 12, 60, 0 ),   ( 37, 255, 255 )], 
    'blue':   [( 100, 120, 0 ),  ( 117, 255, 255 )],  
    'green':  [( 73, 96, 20 ),   ( 100, 255, 80 )]
}