import sxtwl
import requests
import datetime
import json
from openai import OpenAI

# 配置信息
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/4738fb14-a6b1-4391-a05c-2507ef5a46ff"
client = OpenAI()

GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

def get_today_info():
    now = datetime.datetime.now()
    day = sxtwl.fromSolar(now.year, now.month, now.day)
    gz_day_idx = day.getDayGZ()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "gz_day": GAN[gz_day_idx.tg] + ZHI[gz_day_idx.dz],
        "tg": GAN[gz_day_idx.tg],
        "dz": ZHI[gz_day_idx.dz]
    }

def get_ai_fortune(name, profile, target_info):
    prompt = f"""
你是一位精通八字命理与心理疗愈的高维导航员。
请根据以下用户命盘和目标日期的干支，生成一份【{name}专属·每日能量指南】。

用户命盘 ({name}):
{profile}

目标日期: {target_info['date']} ({target_info['gz_day']}日)

要求:
1. 风格: 极简、通透、有共情力。文字要精炼，排版要疏朗，不要大段文字，多用短句和换行。
2. 格式: 
   - 📅 **今天是 {target_info['date']} · {target_info['gz_day']} 日**
   - **总评：这是一个 [核心基调] 的日子。**
   - ---
   - **🔮 能量天气预报：**
     (用2-3句优美的短句描述核心感受，并点出今日干支对命盘的关键影响)
   - **🚫 禁忌清单 (别做！)：**
     (给出2条精炼的避坑建议)
   - **✅ 转运清单 (去做！)：**
     (1) [具体行动建议]
     (2) **今日穿搭建议**：[幸运色] + [风格建议] (原理：结合五行喜忌)
   - **💌 悄悄话：**
     (一句简短有力的鼓励)

注意: 
- 严禁使用 ### 标题，必须使用 **粗体文字** 作为标题。
- 文字要少而精，让用户一眼看清，不要有阅读压力。
- 总评必须放在最上面。
"""
    
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "system", "content": "你是一位精通命理的专业导师。"},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def send_to_feishu(title, content, color="orange"):
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": color
            },
            "elements": [{"tag": "markdown", "content": content}]
        }
    }
    requests.post(FEISHU_WEBHOOK, json=payload)

if __name__ == "__main__":
    info = get_today_info()
    
    sister_profile = """
    - 八字: 壬申 戊申 壬午 壬寅
    - 格局: 身强比劫旺，枭神夺食（寅申冲），寅午半合火局。
    - 喜用: 木 (食伤)、火 (财)、燥土 (官杀)。
    - 忌神: 金 (印)、水 (比劫)、湿土 (晦火)。
    """
    
    queen_profile = """
    - 核心动力: 寅午戌三合火局（创造力、激情、从财格）。
    - 灵魂暗礁: 丑戌刑 + 庚金偏印（原生家庭牵绊、内耗焦虑、完美主义）。
    - 才华通道: 壬寅日柱（自坐食神/文昌/驿马，表达欲、灵性直觉）。
    """
    
    sister_content = get_ai_fortune("姐姐", sister_profile, info)
    send_to_feishu("🌟 姐姐专属·每日能量指南 (今日验证)", sister_content, "orange")
    
    queen_content = get_ai_fortune("妹妹", queen_profile, info)
    send_to_feishu("👑 妹妹专属·每日能量指南 (今日验证)", queen_content, "purple")
    
    print(f"Today's AI Fortune sent for verification.")
