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
    gz_day = GAN[day.getDayGZ().dz] # 注意：此处应为日柱干支
    # 修正：获取日柱干支
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
    精准具象推演协议：拒绝废话，直击痛点。
    """
    day_label = "今日" if target_info['is_today'] else ("历史" if target_info['is_past'] else "明日")
    
    if name == "姐姐":
        role_style = "温柔疗愈型知心大姐姐。语气多安慰、多鼓励，严禁讲大道理。"
        persona_logic = """
        - 针对身强水旺、枭神夺食：重点找‘出口’。
        - 喜木火，忌金水。
        - 任务：化解她的焦虑和累，让她觉得‘不想动’也是可以被接纳的，并引导她去做开心的‘木火’小事。
        """
    else: # 妹妹
        role_style = "搞钱军师型。语气犀利、直接、打鸡血，只给搞钱和避坑指令。"
        persona_logic = """
        - 针对从财格火局：重点找‘钱’和‘收网机会’。
        - 喜火土，忌金水。
        - 任务：帮她识别‘湿土烂人’，给出明确的进攻或防守指令，让她感觉到你在带她赢。
        """

    prompt = f"""角色：{role_style}
请对 ({name}) 进行{day_label}推演。

【核心档案】：
{profile['bazi_summary']}
当前大运：{profile['current_luck']}

【时空切片】：
- 目标日期：{target_info['gz_day']}日 ({target_info['date']})

【硬性指令】：
1. **人设：** {persona_logic}
2. **具象化：** 严禁出现“财运不佳”“注意情绪”等废话。
   - 财星：必须说出是买了什么（如：裙子、贵价餐）、丢了什么或赚了什么。
   - 官杀：必须说出具体是谁（如：没眼力的男领导、查岗的老公）。
   - 场景：必须锁定场景（如：堆满纸箱的玄关、嘈杂的地铁站、亮如白昼的餐厅）。
3. **钩子：** 必须包含一个物理触发点（如：手机屏幕碎裂、收到迟到的快递、闻到某款香水味）。

【输出模板】：
📅 **{day_label}是 {target_info['date']} ({target_info['gz_day']}日)**
**💰 财运：** [具体结论 + 生活细节象义]
**🤝 人际：** [遇到的具体人物特征 + 交流状态]
**😊 心情：** [点破最具体的心理诱因]
---
**🔮 能量天气预报：** [一句话犀利/温柔点破今日核心真相]
**🚫 避雷清单：** (1) [具体动作] (2) [具体物件/场景]
**✅ 转运清单：** (1) [具体动作] (2) **穿搭建议**：[具体材质/色系]
**💌 悄悄话：** [专属贴士]

注意: 不要返回 ### 这种 Markdown 标题。"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": f"你是一位擅长取象、极其具象的导师。你的风格是：{role_style}"},
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
        # 1 为预报明天，0 为验证今天
        offset = -1 
        info = get_target_info(offset=offset)
        
        sister_profile = {
            "current_luck": "2021-2030走【乙巳】大运",
            "bazi_summary": "👩 姐姐 (1992壬申)：身强水旺，比劫夺财，枭神夺食。喜木火，忌金水。痛点：焦虑情绪化、累。"
        }
        
        queen_profile = {
            "current_luck": "2021-2030走【癸丑】大运",
            "bazi_summary": "👸 妹妹 (1997丙午)：从财格，三合火局。喜火土，忌金水。痛点：怕亏钱，怕湿土烂人。"
        }
        
        targets = [("姐姐", sister_profile, "orange"), ("妹妹", queen_profile, "purple")]
        for name, profile, color in targets:
            content = get_ai_fortune(name, profile, info)
            day_type = "真相" if offset <= 0 else "预言"
            custom_title = f"🌟 {info['display_date']} ({info['weekday']}) | {name}专属{day_type}"
            send_to_feishu(custom_title, content, color)
