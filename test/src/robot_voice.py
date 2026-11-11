#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
from std_msgs.msg import String
import subprocess
import sherpa_onnx
import numpy as np
import os
import sys
from thefuzz import fuzz
from pypinyin import lazy_pinyin
from action import VOICE_CONTROL_MAP

class VoiceControlNode:
    def __init__(self):
        rospy.init_node('voice_control_node', anonymous=True)
        
        # --- 1. ROS 发布者 ---
        # 发送识别到的汉字 Key，例如 "向右转动一步"
        self.pub = rospy.Publisher('/voice_cmd_raw', String, queue_size=10)

        # --- 2. ASR 配置参数 ---
        self.MODEL_DIR = "../ASR/sherpa-onnx-streaming-zipformer-zh-int8-2025-06-30"
        self.HW_DEVICE = "hw:0,0"
        self.MIC_RATE = 48000  
        self.ASR_RATE = 16000  

        # --- 3. 提取词表与拼音预计算 ---
        self.VOICE_COMMANDS = list(VOICE_CONTROL_MAP.keys())
        self.PINYIN_TO_VOICE = {self._to_pinyin_str(k): k for k in self.VOICE_COMMANDS}

        # --- 4. ASR 引擎实例化 ---
        print("正在加载语音模型，请耐心等待约40秒...")
        self.recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
            tokens=f"{self.MODEL_DIR}/tokens.txt",
            encoder=f"{self.MODEL_DIR}/encoder.int8.onnx",
            decoder=f"{self.MODEL_DIR}/decoder.onnx",
            joiner=f"{self.MODEL_DIR}/joiner.int8.onnx",
            num_threads=1,
            sample_rate=self.ASR_RATE,
            feature_dim=80,
            decoding_method="greedy_search",
        )
        self.stream = self.recognizer.create_stream()
        self.last_full_text = ""
        print("✅ 语音独立节点已启动。您可以开始说话了")

    def _to_pinyin_str(self, text):
        """汉字转拼音工具"""
        return "".join(lazy_pinyin(text))

    def send_cmd(self, voice_key):
        """通过 ROS 发射识别到的汉字键"""
        self.pub.publish(voice_key)
        # 在独立窗口中，打印可以非常显眼
        print(f"\n\033[1;32m🎯 [命中并已发送]: {voice_key}\033[0m")

    def process_and_trigger(self, text):
        if not text.strip(): return False
        
        # 过滤单字噪音，防止“基”、“二”等碎音误触
        if len(text.strip()) < 2: 
            return False

        found_any = False
        # 按指令长度从长到短排序
        sorted_cmds = sorted(self.VOICE_COMMANDS, key=len, reverse=True)
        temp_text = text
        
        # --- 阶段 1：汉字消耗匹配 ---
        for voice_cmd in sorted_cmds:
            while voice_cmd in temp_text:
                # 动作前缀拦截逻辑
                if "基地" in text and "基地" not in voice_cmd and "到" in voice_cmd:
                    break
                if "跳转" in text and "跳转" not in voice_cmd and "到" in voice_cmd:
                    break
                
                # 数字强匹配校验
                check_digits = ["一", "二", "三", "四", "五"]
                text_digit = next((d for d in check_digits if d in text), None)
                cmd_digit = next((d for d in check_digits if d in voice_cmd), None)
                
                # 只有当两者都有数字且不一致时才拦截
                if text_digit and cmd_digit and text_digit != cmd_digit:
                    break

                self.send_cmd(voice_cmd)
                found_any = True
                # 抹除已匹配项
                temp_text = temp_text.replace(voice_cmd, " [DONE] ", 1)

        # --- 阶段 2：局部拼音模糊匹配 ---
        if not found_any and len(temp_text.strip()) >= 2:
            input_pinyin = self._to_pinyin_str(temp_text)
            best_voice_cmd = None
            max_score = 0
            
            for cmd_pinyin, voice_cmd in self.PINYIN_TO_VOICE.items():
                # 使用局部匹配，解决复读机长串问题
                score = fuzz.partial_ratio(input_pinyin, cmd_pinyin)
                
                # 针对短指令（如“继续”）要求极高匹配分，防止单音节误触
                min_score = 98 if len(voice_cmd) <= 2 else 90

                # 拼音阶段的数字校验
                check_digits = ["一", "二", "三", "四", "五"]
                found_digit = next((d for d in check_digits if d in voice_cmd), None)
                if found_digit and found_digit not in temp_text:
                    continue

                if score >= min_score:
                    if score > max_score:
                        max_score = score
                        best_voice_cmd = voice_cmd

            if best_voice_cmd:
                self.send_cmd(best_voice_cmd)
                found_any = True

        return found_any

    def run(self):
        # 启动录音进程
        record_cmd = ["arecord", "-D", self.HW_DEVICE, "-f", "S16_LE", "-r", str(self.MIC_RATE), "-c", "1", "-t", "raw", "-q"]
        proc = subprocess.Popen(record_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        
        try:
            while not rospy.is_shutdown():
                in_data = proc.stdout.read(9600)
                if not in_data: break
                
                audio_data = np.frombuffer(in_data, dtype=np.int16)[::3]
                samples = audio_data.astype(np.float32) / 32768.0
                self.stream.accept_waveform(self.ASR_RATE, samples)
                
                while self.recognizer.is_ready(self.stream):
                    self.recognizer.decode_stream(self.stream)
                
                current_text = self.recognizer.get_result(self.stream).strip()
                if current_text and current_text != self.last_full_text:
                    # 在独立窗口刷新，不再影响主程序日志
                    print(f"\r\033[K🎤 实时识别: {current_text}", end="", flush=True)
                    self.last_full_text = current_text
                    
                    if self.process_and_trigger(current_text):
                        # 命中后重置流，准备下一次听取
                        self.stream = self.recognizer.create_stream()
                        self.last_full_text = ""
        except Exception as e:
            print(f"\n❌ 语音节点崩溃: {e}")
        finally:
            proc.terminate()

if __name__ == "__main__":
    node = VoiceControlNode()
    node.run()