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
    
    prompt = f"""你是一位精通子平、盲派逻辑，且深谙现代生活取象的顶级导师。
请对用户 ({name}) 进行{day_label}推演。

【时空全景】：
- 当前大运：{profile['current_luck']}
- 宏观流转：{target_info['gz_year']}年 {target_info['gz_month']}月
- 微观切片：目标日期 {target_info['gz_day']}日

【用户原局】：
{profile['bazi_summary']}

【导师精准象义指令】：
1. **拒绝抽象，具体取象**：不要只说“财运好/坏”，要翻译成具体行为。
   - 例如：偏财见食伤，可能是“突然想吃顿贵的”或“在购物平台上刷到心仪之物”。
   - 例如：印星重，可能是“想窝着不想说话”或“整理旧物”。
   - 例如：劫财透，可能是“被垃圾广告骚扰”或“不得不处理的人情琐事”。
2. **场景穿透**：结合干支刑冲，指出该能量最可能发生在哪个场景：办公室、卧室、商场、还是饭桌？
3. **针对壬水特质**：壬水喜动，关注水是被阻滞（土重）还是被疏导（木旺），指出是“思维受阻”还是“表达欲望强烈”。
4. **极简约束**：每个板块不超过2句结论，必须包含一个具体的生活细节象义。

【输出格式要求】：
 📅 **{day_label}是 {target_info['date']} ({target_info['gz_day']}日)**
 **💰 财运：** [直接给结论，必须提到一个具体的金钱流向或消费场景]
 **🤝 人际：** [指出你会遇到什么样的人或交流状态，拒绝“注意人际关系”这种废话]
 **😊 心情：** [点破情绪的物理诱因，如：因为杂物、因为美食、因为某条消息]
 ---
 **🔮 能量天气预报：**
    [用一句最毒舌或最犀利的象义点破今日核心生活切面]
 **🚫 禁忌清单：**
    (1) [具体的动作] (2) [具体的物件/场景]
 **✅ 转运清单：**
    (1) [具体的动作] (2) **穿搭建议**：[具体到风格或材质]
 **💌 悄悄话：** [一句话生活小贴士]

注意: 严禁使用 ### 标题。"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": "你是一位生活化、毒舌且极其精准的命理导师，擅长从干支中读出柴米油盐的细节。"},
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
            "current_luck": "2021-2030走【乙巳】大运（财运期）",
            "bazi_summary": "壬水身强偏印重。喜木火食伤泄秀，忌金水沉闷。注意：印重时容易想得多做得少，需火来破印。"
        }
        
        queen_profile = {
            "current_luck": "2021-2030走【癸丑】大运（劫财带官杀）",
            "bazi_summary": "壬寅日柱三合火局。喜木火灵动，忌癸水阴沉遮阳。注意：寅木是你的快乐源泉，一旦受损就会失去生活热忱。"
        }
        
        targets = [("姐姐", sister_profile, "orange"), ("妹妹", queen_profile, "purple")]
        for name, profile, color in targets:
            content = get_ai_fortune(name, profile, info)
            day_type = "验证" if offset <= 0 else "预报"
            custom_title = f"🌟 {info['display_date']} ({info['weekday']}) | {name}专属能量{day_type}"
            send_to_feishu(custom_title, content, color)
