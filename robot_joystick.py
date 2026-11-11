import sys
sys.path.append("/home/sunrise/catkin_ws/src/aelos_smart_ros")

from leju import *

leju_variable__E6_89_8B_E6_9F_84 = None



def main():
    nodes.node_initial()
    try:


        while 0 == 0:
            leju_variable__E6_89_8B_E6_9F_84 = get_key.key()
            if leju_variable__E6_89_8B_E6_9F_84 == 193:
                base_action.action('向前慢走1步')
            if leju_variable__E6_89_8B_E6_9F_84 == 196:
                base_action.action('向前走2cm-稳定')
            if leju_variable__E6_89_8B_E6_9F_84 == 195:
                base_action.action('向前快走1步')
            if leju_variable__E6_89_8B_E6_9F_84 == 194:
                base_action.action('向前快走3步')
            if leju_variable__E6_89_8B_E6_9F_84 == 197:
                base_action.action('向后慢走1步-修正前掌')
            if leju_variable__E6_89_8B_E6_9F_84 == 198:
                base_action.action('向后慢走3步')
            if leju_variable__E6_89_8B_E6_9F_84 == 199:
                base_action.action('向后走2cm-稳定')
            if leju_variable__E6_89_8B_E6_9F_84 == 200:
                base_action.action('向后快走1步')
            if leju_variable__E6_89_8B_E6_9F_84 == 201:
                base_action.action('向左转动1步')
            if leju_variable__E6_89_8B_E6_9F_84 == 205:
                base_action.action('小左移')
            if leju_variable__E6_89_8B_E6_9F_84 == 203:
                base_action.action('向右平移1步')
            if leju_variable__E6_89_8B_E6_9F_84 == 202:
                base_action.action('小右移')
            if leju_variable__E6_89_8B_E6_9F_84 == 206:
                base_action.action('向左转动1步')
            if leju_variable__E6_89_8B_E6_9F_84 == 207:
                base_action.action('小左转')
            if leju_variable__E6_89_8B_E6_9F_84 == 220:
                base_action.action('向左转动1步')
            if leju_variable__E6_89_8B_E6_9F_84 == 222:
                base_action.action('小右转-镜像版2')
            if leju_variable__E6_89_8B_E6_9F_84 == 223:
                base_action.action('抱快递慢走')
            if leju_variable__E6_89_8B_E6_9F_84 == 233:
                base_action.action('box_forward_s_v3')
            if leju_variable__E6_89_8B_E6_9F_84 == 235:
                base_action.action('向前快走3步-后仰10平手')
            if leju_variable__E6_89_8B_E6_9F_84 == 234:
                base_action.action('向后慢走1步-修正前掌-抱箱')
            if leju_variable__E6_89_8B_E6_9F_84 == 237:
                base_action.action('向后走2cm-稳定-抱箱')
            if leju_variable__E6_89_8B_E6_9F_84 == 239:
                base_action.action('抱快递左移')
            if leju_variable__E6_89_8B_E6_9F_84 == 241:
                base_action.action('抱快递小左移-超紧')
            if leju_variable__E6_89_8B_E6_9F_84 == 242:
                base_action.action('抱快递右移')
            if leju_variable__E6_89_8B_E6_9F_84 == 1:
                base_action.action('抱快递小右移-超紧')
            if leju_variable__E6_89_8B_E6_9F_84 == 2:
                base_action.action('抱快递左转')
            if leju_variable__E6_89_8B_E6_9F_84 == 3:
                base_action.action('抱快递右转2')
            if leju_variable__E6_89_8B_E6_9F_84 == 4:
                base_action.action('box_turnright_q_v1')
            if leju_variable__E6_89_8B_E6_9F_84 == 5:
                base_action.action('配送-抱快递-夹得超紧')
            if leju_variable__E6_89_8B_E6_9F_84 == 6:
                base_action.action('配送-放快递')
            if leju_variable__E6_89_8B_E6_9F_84 == 7:
                base_action.action('无用-test上楼梯3')
            if leju_variable__E6_89_8B_E6_9F_84 == 8:
                base_action.action('下楼梯1厘米-修正版')
            if leju_variable__E6_89_8B_E6_9F_84 == 9:
                base_action.action('书架-放二层3')
            if leju_variable__E6_89_8B_E6_9F_84 == 10:
                base_action.action('书架-放一层')
            if leju_variable__E6_89_8B_E6_9F_84 == 11:
                base_action.action('配送-书籍箱子放快递')
            if leju_variable__E6_89_8B_E6_9F_84 == 12:
                base_action.action('推抹布-消摩擦完美版-加循环-18')

    except Exception as e:
        nodes.serror(e)
        exit(2)
    finally:
        nodes.finishsend()
if __name__ == "__main__":
    print ("Run custom project")
    main()