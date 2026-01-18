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
# 定义星期映射
WEEK_MAP = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

def get_tomorrow_info():
    # 转换为北京时间并获取【明天】日期
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    tomorrow = now + datetime.timedelta(days=1)
    
    day = sxtwl.fromSolar(tomorrow.year, tomorrow.month, tomorrow.day)
    gz_day_idx = day.getDayGZ()
    
    # 获取星期几
    weekday = WEEK_MAP[tomorrow.weekday()]
    
    return {
        "date": tomorrow.strftime("%Y-%m-%d"),
        "display_date": tomorrow.strftime("%m月%d日"),
        "weekday": weekday,
        "gz_day": GAN[gz_day_idx.tg] + ZHI[gz_day_idx.dz],
        "tg": GAN[gz_day_idx.tg],
        "dz": ZHI[gz_day_idx.dz]
    }

def get_ai_fortune(name, profile, target_info):
    # 强化版的命理逻辑 Prompt
    prompt = f"""你是一位综合了梁湘润（流年造诣）、盲派（取象直觉）、子平（格用神平衡）及陆致极（现代生活映射）理论体系的顶级命理导师。
请对以下用户进行深度穿透分析。

用户命盘 ({name}):{profile}
明日干支: {target_info['date']} ({target_info['gz_day']}日)

【导师分析指令】：
1. 辩证看生克：不要看到“比劫夺财”就断定心情不好。若原局财重身轻，比劫流日反而是“助身担财”，表现为“主动慷慨消费、社交愉悦、掌控感增强”。
2. 穿透看地支：分析流日地支与原局的刑冲破害及“入库/培根”关系（如寅见辰为食神培根，主灵感与舒畅）。
3. 现代象义：区分“被动破财”与“主动消费”。壬水日主往往在水旺之日更具自信和豪爽气场。

输出格式要求 (文字要具备穿透力，拒绝套话):
 📅 **明天是 {target_info['date']} · {target_info['gz_day']} 日**
 **💰 财运：** (分析是“财来找我”还是“我去找财”，是主动消费还是意外损耗)
 **🤝 人际：** (分析比劫是“争夺”还是“陪伴/助力”，官杀是“压力”还是“动力”)
 **😊 心情：** (结合调候用神。分析神智是“郁结”还是“舒展”。注意区分“花钱后的爽快”与“财损后的郁闷”)
 ---
 **🔮 能量天气预报：**
    (用2-3句优美的短句描述核心感受，并点出明日干支对命盘的关键影响)
     **🚫 禁忌清单 (别做！)：**
    (给出2条精炼的避坑建议)
     **✅ 转运清单 (去做！)：**
    (1) [具体行动建议]
    (2) **明日穿搭建议**：[幸运色] + [风格建议] (原理：结合五行喜忌)
     **💌 悄悄话：**
    (一句简短有力的鼓励)

注意: 严禁使用 ### 标题，必须使用 **粗体文字** 作为标题。"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": "你是一位言辞犀利、直击灵魂、不落俗套的专业命理导师。"},
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
        # 获取明天信息
        info = get_tomorrow_info()
        
        sister_profile = """
    - 格局: 偏印当令，壬水身强，驿马逢冲（寅申）。
    - 喜忌: 喜火木（财食），忌金水（印比）。
    """
        
        queen_profile = """
    - 格局: 壬寅日柱，地支三合火局（财旺身弱/从财意向）。
    - 特点: 文昌坐命，偏印透干，官杀内刑（丑戌）。
    - 喜忌: 喜火木（顺局），忌金水（逆局/夺财）。但身极弱时，微水（比肩）助身反主自信。
    """
        
        targets = [("姐姐", sister_profile, "orange"), ("妹妹", queen_profile, "purple")]
        for name, profile, color in targets:
            content = get_ai_fortune(name, profile, info)
            # 修改点：动态生成标题，包含日期和星期
            custom_title = f"🌟 {info['display_date']} ({info['weekday']}) | {name}专属能量指南"
            send_to_feishu(custom_title, content, color)
