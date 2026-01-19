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
    """获取目标日期的全方位干支信息"""
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    target_date = now + datetime.timedelta(days=offset)
    day = sxtwl.fromSolar(target_date.year, target_date.month, target_date.day)
    
    return {
        "date": target_date.strftime("%Y-%m-%d"),
        "display_date": target_date.strftime("%m月%d日"),
        "weekday": WEEK_MAP[target_date.weekday()],
        "gz_year": GAN[day.getYearGZ().tg] + ZHI[day.getYearGZ().dz],
        "gz_month": GAN[day.getMonthGZ().tg] + ZHI[day.getMonthGZ().dz],
        "gz_day": GAN[day.getDayGZ().tg] + ZHI[day.getDayGZ().dz],
        "is_today": offset == 0,
        "is_past": offset < 0
    }

def get_ai_fortune(name, profile, target_info):
    """
    全息扫描协议：分角色深度具象定制版。
    """
    day_label = "今日" if target_info['is_today'] else ("历史" if target_info['is_past'] else "明日")
    
    # 根据用户角色动态调整系统指令和 Prompt
    if name == "姐姐":
        role_description = "你是一位极具同理心、温柔、知性的女性命理疗愈师。语气要像知心大姐姐，多安慰鼓励，少讲大道理。"
        custom_logic = """
        - 重点观察“枭神夺食”和“比劫夺财”的缓解情况。
        - 看到木火（喜神）：告诉她那是能量的充电宝，鼓励她去社交、去花钱、去感受阳光。
        - 看到金水（忌神）：安慰她这只是暂时的乌云，提醒她要松弛，不要内耗。
        """
    else:  # 妹妹
        role_description = "你是一位犀利、直接、极具商业洞察力的‘搞钱军师’。语气要带点儿江湖气和打鸡血的劲头。"
        custom_logic = """
        - 重点观察从财格的火局是否稳固。
        - 看到火土（喜神）：给出明确的进攻指令，告诉她这就是收网或搞钱的好时机。
        - 看到金水（忌神）：直接预警，告诉她哪些是“湿土烂人”，哪些坑必须避开，说话要扎心。
        """

    prompt = f"""{role_description}
请对用户 ({name}) 进行{day_label}推演。

【用户信息】：
{profile['bazi_summary']}
当前大运：{profile['current_luck']}

【时空切片】：
目标日期 {target_info['gz_day']}日 ({target_info['gz_year']}年 {target_info['gz_month']}月)

【深度推演逻辑】：
1. **十神具象为人与事**：
   - 官杀：别只说压力。结合喜忌，它是“帅气但管得严的老公”、“找茬的甲方”还是“让你升职的责任”。
   - 财星：它是“让你心动的高级定制”、“账户里的数字增长”还是“不得不交的智商税”。
   - 比劫：是“陪你吐槽的姐妹”还是“来分你蛋糕的讨厌鬼”。
2. **场景穿透**：结合干支关系，描述一个生活场景。例如：在温暖的咖啡馆、在杂乱的办公室、还是在热闹的商场。
3. **{name}专属逻辑**：{custom_logic}

【输出格式要求】：
 📅 **{day_label}是 {target_info['date']} ({target_info['gz_day']}日)**
 **💰 财运：** [具象描述金钱流向。是进攻、防守、还是快乐地‘消费疗愈’？]
 **🤝 人际：** [今天谁会出现？是带来光的人，还是让你想翻白眼的烂人？描述其特征。]
 **😊 心情：** [点破情绪的物理诱因。是因为一顿美食、一个拥抱、还是一个没回的微信？]
 ---
 **🔮 能量天气预报：**
    [一句话点评今日核心磁场，要求具象且有力度。]
 **🚫 避雷清单：**
    (1) [具体的动作或场景] (2) [具体的某类人或心态]
 **✅ 转运清单：**
    (1) [能量疏导的具体动作] (2) **穿搭建议**：[具体到材质和给人传递的气场]
 **💌 悄悄话：** [针对{name}性格的专属叮嘱]

注意: 严禁使用 ### 标题。"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": role_description},
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
        offset = -3 
        info = get_target_info(offset=offset)
        
        sister_profile = {
            "current_luck": "2021-2030走【乙巳】大运",
            "bazi_summary": "1992壬申年，身强水旺。痛点：比劫夺财、枭神夺食（易焦虑累）。喜：木火。忌：金水。"
        }
        
        queen_profile = {
            "current_luck": "2021-2030走【癸丑】大运",
            "bazi_summary": "1997丙午女，从财格，寅午戌三合火局。痛点：怕亏钱，怕湿土（烂人烂事）。喜：火土。忌：金水。"
        }
        
        targets = [("姐姐", sister_profile, "orange"), ("妹妹", queen_profile, "purple")]
        for name, profile, color in targets:
            content = get_ai_fortune(name, profile, info)
            day_type = "真相" if offset <= 0 else "预言"
            custom_title = f"🌟 {info['display_date']} ({info['weekday']}) | {name}专属{day_type}"
            send_to_feishu(custom_title, content, color)
