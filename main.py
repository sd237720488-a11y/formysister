import sxtwl
import requests
import datetime
import os
from openai import OpenAI

# 环境变量获取
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK", "").strip().strip('"').strip("'")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")

# 初始化 DeepSeek 客户端
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
WEEK_MAP = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

def get_today_info():
    """获取【今天】的全方位干支信息，用于验证准确度"""
    # 转换为北京时间
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    
    day = sxtwl.fromSolar(now.year, now.month, now.day)
    
    gz_year = GAN[day.getYearGZ().tg] + ZHI[day.getYearGZ().dz]
    gz_month = GAN[day.getMonthGZ().tg] + ZHI[day.getMonthGZ().dz]
    gz_day = GAN[day.getDayGZ().tg] + ZHI[day.getDayGZ().dz]
    
    return {
        "date": now.strftime("%Y-%m-%d"),
        "display_date": now.strftime("%m月%d日"),
        "weekday": WEEK_MAP[now.weekday()],
        "gz_year": gz_year,
        "gz_month": gz_month,
        "gz_day": gz_day
    }

def get_ai_fortune(name, profile, target_info):
    """
    全息扫描协议极简版：强制短句输出，直击痛点。
    """
    prompt = f"""你是一位精通子平、盲派逻辑的顶级导师。
请对用户 ({name}) 进行今日推演。

【时空全景】：
- 当前大运：{profile['current_luck']}
- 宏观流转：{target_info['gz_year']}年 {target_info['gz_month']}月
- 微观切片：今日 {target_info['gz_day']}日

【用户原局】：
{profile['bazi_summary']}

【导师极致精准指令】：
1. **全方位检索**：基于流日干支与原局、大运、流年的刑冲合害（尤其是天干清浊与地支相穿）进行深度判定。
2. **极简输出控制**：严禁废话，严禁分析过程。**每个版块（财运、人际、心情）只允许输出不超过2句话的精准结论**。

【输出格式要求】：
 📅 **今天是 {target_info['date']} ({target_info['gz_day']}日)**
 **💰 财运：** [直接给结论，描述损益情况]
 **🤝 人际：** [直接给结论，指出社交真相]
 **😊 心情：** [直接给结论，点破情绪根源]
 ---
 **🔮 能量天气预报：**
    [用一句最犀利的话点破今日核心气场真相]
 **🚫 禁忌清单：**
    (1) [动作] (2) [动作]
 **✅ 转运清单：**
    (1) [动作] (2) **穿搭建议**：[颜色风格]
 **💌 悄悄话：** [一句话叮嘱]

注意: 严禁使用 ### 标题。"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": "你是一位言辞极简、直击本质、拒绝任何分析过程的命理导师。"},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 生成失败: {str(e)}"

def send_to_feishu(title, content, color="orange"):
    if not FEISHU_WEBHOOK.startswith("http"):
        return
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
    requests.post(FEISHU_WEBHOOK, json=payload, timeout=15)

if __name__ == "__main__":
    if FEISHU_WEBHOOK and DEEPSEEK_API_KEY:
        info = get_today_info()
        
        sister_profile = {
            "current_luck": "2021-2030走【乙巳】大运；2031-2040走【甲辰】大运",
            "bazi_summary": "壬水身强，偏印当令。喜木火（食伤生财），忌金水（印比夺食）。"
        }
        
        queen_profile = {
            "current_luck": "2021-2030走【癸丑】大运；2031-2040走【甲寅】大运",
            "bazi_summary": "壬寅日柱，地支三合火局（从财意向）。喜木火，忌金水。注意：壬水日主极反感癸水透干之“乌云蔽日”。"
        }
        
        targets = [("姐姐", sister_profile, "orange"), ("妹妹", queen_profile, "purple")]
        for name, profile, color in targets:
            content = get_ai_fortune(name, profile, info)
            custom_title = f"🌟 {info['display_date']} ({info['weekday']}) | {name}专属能量指南"
            send_to_feishu(custom_title, content, color)
