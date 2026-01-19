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
    """
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
    全息扫描协议生活化版：拒绝套话，细化具体生活场景。
    """
    day_label = "今日" if target_info['is_today'] else ("历史" if target_info['is_past'] else "明日")
    
    # 根据用户角色动态调整语气和侧重点
    if name == "姐姐":
        role_style = "你是一位极具同理心、温柔、知性的女性命理疗愈师。语气要像知心大姐姐，多安慰鼓励，少讲大道理。"
        focus_logic = "侧重情绪疏导。看到木火要鼓励她充电社交，看到金水要安抚她避开内耗。"
    else: # 妹妹
        role_style = "你是一位犀利、直接、极具商业洞察力的‘搞钱军师’。语气带点江湖气和打鸡血的劲头。"
        focus_logic = "侧重搞钱和避坑。看到火土要给进攻指令，看到金水直接点名‘湿土烂人’和‘亏钱坑’。"

    prompt = f"""{role_style}
请对用户 ({name}) 进行{day_label}推演。

【用户信息】：
{profile['bazi_summary']}
当前大运：{profile['current_luck']}

【时空全景】：
- 宏观流转：{target_info['gz_year']}年 {target_info['gz_month']}月
- 微观切片：目标日期 {target_info['gz_day']}日

【导师精准象义指令】：
1. **拒绝抽象，具体取象**：
   - **官杀**：具体到“老公管得宽”、“找茬的甲方”、“没眼力见的男人”或“罚单/法律麻烦”。
   - **财星**：具体到“账户进账”、“买了件发光的裙子”、“想吃顿贵的”或“不得不交的智商税”。
   - **比劫**：具体到“陪你吐槽的姐妹”或“来分你蛋糕的讨厌鬼”。
2. **场景穿透**：结合干支刑冲，指出能量发生在哪个场景：办公室、卧室、商场、还是饭桌？
3. **角色逻辑嵌入**：{focus_logic}
4. **极简约束**：每个板块不超过2句，必须包含一个具体的生活细节象义。

【输出格式要求】：
📅 **{day_label}是 {target_info['date']} ({target_info['gz_day']}日)**
**💰 财运：** [直接给结论，必须提到一个具体的金钱流向或消费场景]
**🤝 人际：** [指出你会遇到什么样的人或交流状态，拒绝废话]
**😊 心情：** [点破情绪的物理诱因，如：因为美食、因为某条消息、因为杂物]---
**🔮 能量天气预报：**
   [针对{name}的特质，用一句话犀利点破今日核心生活切面]
**🚫 避雷清单：**
   (1) [具体的动作] (2) [具体的物件/场景]
**✅ 转运清单：**
   (1) [具体的动作] (2) **穿搭建议**：[具体到材质或气场风格]
**💌 悄悄话：** [针对{name}性格的专属生活小贴士]

注意: 严禁使用 ### 标题。"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": "你是一位生活化、擅长把命理读成柴米油盐的顶级导师。"},
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
        # offset = 1: 明天; 0: 今天; -1: 昨天
        offset = -1 
        info = get_target_info(offset=offset)
        
        sister_profile = {
            "current_luck": "2021-2030走【乙巳】大运",
            "bazi_summary": "👩 姐姐 (1992壬申)：身强水旺，比劫夺财，枭神夺食。痛点：焦虑情绪化、累。喜木火（开心/搞钱），忌金水（抑郁）。"
        }
        
        queen_profile = {
            "current_luck": "2021-2030走【癸丑】大运",
            "bazi_summary": "👸 妹妹 (1997丙午)：从财格，寅午戌火局。痛点：怕亏钱，怕湿土烂人。喜火土（进攻/收网），忌金水（避坑）。"
        }
        
        targets = [("姐姐", sister_profile, "orange"), ("妹妹", queen_profile, "purple")]
        for name, profile, color in targets:
            content = get_ai_fortune(name, profile, info)
            day_type = "真相" if offset <= 0 else "预言"
            custom_title = f"🌟 {info['display_date']} ({info['weekday']}) | {name}专属{day_type}"
            send_to_feishu(custom_title, content, color)
