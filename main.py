import sxtwl
import requests
import datetime
import os
from openai import OpenAI

# 环境变量获取
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")
# 建议在 GitHub Secrets 中统一命名，或者将下方变量名改为你设置的名字
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")

# 初始化 DeepSeek 客户端 (使用 OpenAI 兼容 SDK)
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com" # 指定 DeepSeek 的服务器地址
)

GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

def get_today_info():
    # 修正：GitHub Actions 运行在 UTC 时间，需转换为北京时间 (UTC+8)
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    day = sxtwl.fromSolar(now.year, now.month, now.day)
    gz_day_idx = day.getDayGZ()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "gz_day": GAN[gz_day_idx.tg] + ZHI[gz_day_idx.dz],
        "tg": GAN[gz_day_idx.tg],
        "dz": ZHI[gz_day_idx.dz]
    }

def get_ai_fortune(name, profile, target_info):
    prompt = f"""你是一位精通八字命理与心理疗愈的高维导航员。请根据以下用户命盘和目标日期的干支，生成一份【{name}专属·每日能量指南】。
用户命盘 ({name}):{profile}
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
注意: 严禁使用 ### 标题，必须使用 **粗体文字** 作为标题。文字少而精，总评放在最上面。"""
    
    try:
        # 使用 deepseek-chat 模型
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": "你是一位精通命理的专业导师。"},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 生成失败: {str(e)}"

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
    if not FEISHU_WEBHOOK or not DEEPSEEK_API_KEY:
        print("Error: Missing Environment Variables (FEISHU_WEBHOOK or DEEPSEEK_API_KEY)")
    else:
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
        
        for person in [("姐姐", sister_profile, "orange"), ("妹妹", queen_profile, "purple")]:
            content = get_ai_fortune(person[0], person[1], info)
            send_to_feishu(f"🌟 {person[0]}专属·每日能量指南", content, person[2])
        
        print(f"Daily Push Completed via DeepSeek: {info['date']}")
