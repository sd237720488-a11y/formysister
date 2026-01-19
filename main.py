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
    全息扫描协议犀利版：具象、有情绪、直击生活真相。
    """
    day_label = "今日" if target_info['is_today'] else ("历史" if target_info['is_past'] else "明日")
    
    prompt = f"""你是一位嘴毒心热、一眼看穿生活狗血剧情的顶级命理导师。
请对用户 ({name}) 进行{day_label}推演。

【时空全景】：
- 当前大运：{profile['current_luck']}
- 宏观流转：{target_info['gz_year']}年 {target_info['gz_month']}月
- 微观切片：目标日期 {target_info['gz_day']}日

【用户原局】：
{profile['bazi_summary']}

【导师毒舌取象指令】：
1. **情感化与具象化**：
   - 严禁温吞。如果流日不好，直接骂醒用户；如果好，就疯狂怂恿。
   - **官杀**：别只说压力。结合宫位，分析是“那个没眼力见的男人（官杀入婚宫）”、“想让你加班的脑残领导（官杀克身）”还是“路口蹲点的交警（官杀刑穿）”。
   - **财星**：分析是“买了件让你发光的裙子（食伤生财）”还是“不得不交的智商税（财损）”。
   - **比劫**：是“拉着你吐槽的烦人精”还是“能陪你喝酒的真哥们”。
2. **场景还原**：根据干支刑冲，描述一个具体的冲突或快乐点。比如：是在地铁上被踩脚，还是在拆快递时心花怒放？
3. **极简输出**：每个板块不超过2句，要犀利、要像老友聊天一样直接。

【输出格式要求】：
 📅 **{day_label}是 {target_info['date']} ({target_info['gz_day']}日)**
 **💰 财运：** [谁在打你钱包主意？或者你该去哪儿爽快花钱？给句准话。]
 **🤝 人际：** [今天谁会让你翻白眼？或者谁会给你递橄榄枝？直接点名这类人的特征。]
 **😊 心情：** [点破你今天那点儿小心思：是想摆烂、想发火、还是想恋爱？]
 ---
 **🔮 能量天气预报：**
    [一句话毒舌点评：今日气场的本质是“涅槃”还是“原地爆炸”？]
 **🚫 避雷清单：**
    (1) [具体的动作或场景] (2) [具体的某类人]
 **✅ 爽歪歪建议：**
    (1) [如何优雅地消费或发泄能量] (2) **穿搭灵魂**：[具体到材质和给人传递的气场]
 **💌 悄悄话：** [一句话扎心或暖心提醒]

注意: 严禁使用 ### 标题。"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": "你是一位言辞犀利、深谙人性弱点、能把玄学说成生活的顶级毒舌宗师。"},
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
            "bazi_summary": "壬水身强偏印重。喜木火。印重的人别整天想那些有的没的，多去花钱、多去社交，把体内的积水排出去。"
        }
        
        queen_profile = {
            "current_luck": "2021-2030走【癸丑】大运",
            "bazi_summary": "壬寅日柱三合火局。喜木火。寅木是你的命根子，谁动它你就跟谁急。癸水透干时，你就容易看谁都不顺眼。"
        }
        
        targets = [("姐姐", sister_profile, "orange"), ("妹妹", queen_profile, "purple")]
        for name, profile, color in targets:
            content = get_ai_fortune(name, profile, info)
            day_type = "真相" if offset <= 0 else "预言"
            custom_title = f"🌟 {info['display_date']} ({info['weekday']}) | {name}专属{day_type}"
            send_to_feishu(custom_title, content, color)
