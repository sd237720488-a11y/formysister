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
    
    # 强化人设差异化指令与准确感补全
    if name == "姐姐":
        role_style = "你是一位极具同理心、温柔、知性的女性命理疗愈师。语气要像知心大姐姐，多安慰鼓励，少讲大道理。"
        role_instruction = """
        - 必须使用【疗愈、舒缓、安抚】的语气。
        - 针对‘比劫夺财’和‘枭神夺食’，重点给姐姐找‘出口’，比如木火代表的快乐消费、美食或阳光运动。
        - 即使是忌神日，也要温柔地告诉她这只是暂时的疲累，鼓励她休息，不要过度解读小摩擦。
        """
    else: # 妹妹
        role_style = "你是一位犀利、直接、极具商业洞察力的‘搞钱军师’。语气带点江湖气和打鸡血的劲头。"
        role_instruction = """
        - 必须使用【搞钱、杀伐果断、直接】的语气。
        - 针对‘从财格’，所有分析都要围绕‘利益、效率、避坑’展开。
        - 看到金水湿土直接点名‘小人烂事’，不留情面地给进攻或撤退指令，帮她看清谁在耽误她搞钱。
        """

    prompt = f"""{role_style}
请对用户 ({name}) 进行{day_label}推演。

【用户信息】：
{profile['bazi_summary']}
当前大运：{profile['current_luck']}

【时空全景】：
- 宏观流转：{target_info['gz_year']}年 {target_info['gz_month']}月
- 微观切片：目标日期 {target_info['gz_day']}日

【导师强制性指令 - 必须让人觉得“神准”】：
1. **角色锁定**：{role_instruction}
2. **具象取象补全（严禁抽象）**：
3. **场景穿透**：结合干支关系（如刑冲合害），断定能量爆发的具体场所。
4. **应验点钩子**：必须描述一个物理诱因。
5. **极简约束**：每个板块不超过2句，必须包含一个生活细节。

【输出格式要求】：
📅 **{day_label}是 {target_info['date']} ({target_info['gz_day']}日)**
**💰 财运：** [给句准话，必须提到一个具体的金钱流向，如：买了XX、因为XX破财、或是XX给你带来了进账]
**🤝 人际：** [指出你会遇到什么样的人或哪种风格的交流，直接点出那个人的特征]
**😊 心情：** [点破那个最具体的心理触发点，如：因为没回的消息、因为乱糟糟的房间、因为一句莫名其妙的话]---
**🔮 能量天气预报：**
   [针对{name}的特质，用一句话犀利或温柔地戳破今日的生活真相]
**🚫 避雷清单：**
   (1) [具体的动作，如：别在下午3点后喝咖啡] (2) [具体的物件/场景，如：别理会那个戴眼镜的男性]
**✅ 转运清单：**
   (1) [具体的动作] (2) **穿搭建议**：[具体到材质或色系，如：丝绸质地的米白色系]
**💌 悄悄话：** [针对{name}性格的专属贴士]

注意: 严禁使用 ### 标题。"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": f"{role_style} 你擅长从干支中精准读出生活的柴米油盐，说话要有画面感。"},
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
