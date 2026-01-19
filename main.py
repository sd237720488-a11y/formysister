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

def get_target_info(offset=1):
    """
    获取目标日期的全方位干支信息
    offset=1: 明天 (默认推送使用)
    offset=0: 今天 (验证使用)
    offset=-1: 昨天 (验证使用)
    """
    # 转换为北京时间并应用偏移量
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    target_date = now + datetime.timedelta(days=offset)
    
    day = sxtwl.fromSolar(target_date.year, target_date.month, target_date.day)
    
    gz_year = GAN[day.getYearGZ().tg] + ZHI[day.getYearGZ().dz]
    gz_month = GAN[day.getMonthGZ().tg] + ZHI[day.getMonthGZ().dz]
    gz_day = GAN[day.getDayGZ().tg] + ZHI[day.getDayGZ().dz]
    
    return {
        "date": target_date.strftime("%Y-%m-%d"),
        "display_date": target_date.strftime("%m月%d日"),
        "weekday": WEEK_MAP[target_date.weekday()],
        "gz_year": gz_year,
        "gz_month": gz_month,
        "gz_day": gz_day,
        "is_today": offset == 0,
        "is_past": offset < 0
    }

def get_ai_fortune(name, profile, target_info):
    """
    全息扫描协议极简版：强制短句输出，直击痛点。
    """
    # 根据日期状态动态调整 Prompt 称呼
    day_label = "今日" if target_info['is_today'] else ("历史" if target_info['is_past'] else "明日")
    
    prompt = f"""你是一位精通子平、盲派逻辑的顶级导师。
请对用户 ({name}) 进行{day_label}推演。

【时空全景】：
- 当前大运：{profile['current_luck']}
- 宏观流转：{target_info['gz_year']}年 {target_info['gz_month']}月
- 微观切片：目标日期 {target_info['gz_day']}日

【用户原局】：
{profile['bazi_summary']}

【导师极致精准指令】：
1. **全方位检索**：基于流日干支与原局、大运、流年的刑冲合害（尤其是天干清浊与地支相穿）进行深度判定。
2. **心情逻辑修正**：严禁见到“财星受克”或“食伤生财”就断心情差。
   - 区分【主动消费】与【被动破财】。主动花钱买乐、购物或宴请，是能量顺畅排泄（食伤生财），主心情愉悦。
   - 壬水日主若流日地支有根（如辰、申、亥），即便见财官，往往代表有底气去掌控局面，主心态自信。
3. **极简输出控制**：严禁废话，每个版块（财运、人际、心情）只允许输出不超过2句话的精准结论。

【输出格式要求】：
 📅 **{day_label}是 {target_info['date']} ({target_info['gz_day']}日)**
 **💰 财运：** [直接给结论，描述损益情况]
 **🤝 人际：** [直接给结论，指出社交真相]
 **😊 心情：** [区分主被动能量，直点情绪真相]
 ---
 **🔮 能量天气预报：**
    [用一句最犀利的话点破该日核心气场真相]
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
        # --- 验证开关 ---
        # offset = 1: 获取明天 (正常推送)
        # offset = 0: 获取今天 (验证)
        # offset = -1: 获取昨天 (验证)
        # offset = -2: 获取前天 (验证)
        offset = 0 
        
        info = get_target_info(offset=offset)
        
        sister_profile = {
            "current_luck": "2021-2030走【乙巳】大运；2031-2040走【甲辰】大运",
            "bazi_summary": "壬水身强，偏印当令。喜木火（食伤生财），忌金水（印比夺食）。注意壬水在流日见根气时（如辰土）的心理底气。"
        }
        
        queen_profile = {
            "current_luck": "2021-2030走【癸丑】大运；2031-2040走【甲寅】大运",
            "bazi_summary": "壬寅日柱，地支三合火局（从财意向）。喜木火，忌金水。注意壬水日主极反感癸水遮阳，但喜食伤（木）泄秀生财的主动快乐。"
        }
        
        targets = [("姐姐", sister_profile, "orange"), ("妹妹", queen_profile, "purple")]
        for name, profile, color in targets:
            content = get_ai_fortune(name, profile, info)
            day_type = "验证" if offset <= 0 else "预报"
            custom_title = f"🌟 {info['display_date']} ({info['weekday']}) | {name}专属能量{day_type}"
            send_to_feishu(custom_title, content, color)
