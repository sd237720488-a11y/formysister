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
    gz_day_str = GAN[day.getDayGZ().tg] + ZHI[day.getDayGZ().dz]
    
    return {
        "date": target_date.strftime("%Y-%m-%d"),
        "display_date": target_date.strftime("%m月%d日"),
        "weekday": WEEK_MAP[target_date.weekday()],
        "gz_year": gz_year,
        "gz_month": gz_month,
        "gz_day": gz_day_str,
        "is_today": offset == 0,
        "is_past": offset < 0
    }

def get_ai_fortune(name, profile, target_info):
    """
    精准具象推演协议：1句话表达，拒绝废话。
    """
    day_label = "今日" if target_info['is_today'] else ("历史" if target_info['is_past'] else "明日")
    
    if name == "姐姐":
        role_style = "温柔疗愈型知心大姐姐。语气极简，多安慰鼓励。"
        persona_logic = "针对枭神夺食，给1句舒缓压力、接纳现状的出口。"
    else: # 妹妹
        role_style = "搞钱军师型。语气极简，直给利弊。"
        persona_logic = "针对从财格，给1句明确的利益指向或避坑指令。"

    prompt = f"""角色：{role_style}
请对 ({name}) 进行{day_label}推演。

【核心档案】：{profile['bazi_summary']}
【目标日期】：{target_info['gz_day']}日

【硬性指令】：
1. **极简表达**：每个版块严格执行【1句话精准表达】，禁止任何修饰词或废话。
2. **绝对具象**：必须指出1个具体的物（如：某件衣服、某顿饭）、1个具体的人（如：某位长辈、某位同事）或1个具体的物理触发点（如：手机震动、窗外雨声）。
3. **逻辑人设**：{persona_logic}

【输出模板】：
📅 **{day_label}是 {target_info['date']} ({target_info['gz_day']}日)**
**💰 财运：** [1句话点破钱财去向或具体进账场景]
**🤝 人际：** [1句话点破会遇到谁及其实际状态]
**😊 心情：** [1句话点破情绪背后的具体诱因]
---
**🔮 能量天气预报：** [1句话点破今日真相]
**🚫 避雷清单：** (1) [具体动作/场景] (2) [具体物件]
**✅ 转运清单：** (1) [具体动作] (2) **穿搭建议**：[具体材质/色系]
**💌 悄悄话：** [1句话专属贴士]

注意: 严禁使用 ### 标题。"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": f"你是一位极简主义的命理导师。风格：{role_style}"},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 故障: {str(e)}"

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
        offset = -3 
        info = get_target_info(offset=offset)
        
        sister_profile = {
            "current_luck": "2021-2030走【乙巳】大运",
            "bazi_summary": "1992壬申：身强水旺，枭神夺食。喜木火，忌金水。"
        }
        
        queen_profile = {
            "current_luck": "2021-2030走【癸丑】大运",
            "bazi_summary": "1997丙午：从财格火局。喜火土，忌金水。"
        }
        
        targets = [("姐姐", sister_profile, "orange"), ("妹妹", queen_profile, "purple")]
        for name, profile, color in targets:
            content = get_ai_fortune(name, profile, info)
            day_type = "真相" if offset <= 0 else "预言"
            custom_title = f"🌟 {info['display_date']} ({info['weekday']}) | {name}专属{day_type}"
            send_to_feishu(custom_title, content, color)
