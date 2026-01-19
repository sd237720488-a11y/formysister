import sxtwl
import requests
import datetime
import os
from openai import OpenAI

# 环境变量获取
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK", "").strip().strip('"').strip("'")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
WEEK_MAP = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

def get_target_info(offset=1):
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    target_date = now + datetime.timedelta(days=offset)
    day = sxtwl.fromSolar(target_date.year, target_date.month, target_date.day)
    gz_day_str = GAN[day.getDayGZ().tg] + ZHI[day.getDayGZ().dz]
    return {
        "date": target_date.strftime("%Y-%m-%d"),
        "display_date": target_date.strftime("%m月%d日"),
        "weekday": WEEK_MAP[target_date.weekday()],
        "gz_day": gz_day_str,
        "is_today": offset == 0
    }

def get_ai_fortune(name, profile, target_info):
    day_label = "今日" if target_info['is_today'] else "明日"
    
    # 终极逻辑补丁：处理阴晴圆缺、天干盖头、伏吟等细节
    if name == "姐姐":
        role_style = "温柔疗愈型知心大姐姐，极简表达。"
        logic_patch = f"""
        - 关键补丁：判断‘枭印化水’。若流日天干见金、地支见水，代表‘想得美但做得累’。
        - 出口逻辑：识别‘甲/乙木’。木能泄水，若见木，结论必须是‘表达出来、写下来就会好’。
        - 关系：申辰合、申子辰三合，代表社交圈的扩大或资源的重新整合。
        """
    else: # 妹妹
        role_style = "搞钱军师型，犀利直接，极简表达。"
        logic_patch = f"""
        - 关键补丁：区分‘壬水’和‘癸水’。壬水日可‘借势搞钱’，癸水日必‘阴郁闭关’（乌云遮日）。
        - 库门逻辑：识别‘戌/辰’。辰是晦火，戌是暖炉。若流日地支与原局地支伏吟（再见午火），代表‘过度亢奋导致决策失误’。
        - 逻辑：喜火土，忌湿气。
        """

    prompt = f"""角色：{role_style}
推演对象：({name}) | 目标日期：{target_info['gz_day']}

【底层算法核心】：
{profile['bazi_summary']}
{logic_patch}

【神准判定指令】：
1. **阴阳细分**：必须区分壬癸水、辰戌土的细微差别。
2. **伏吟/合化判断**：若流日地支与日支相同，断为‘原地踏步’。若地支合化，断为‘性质转换’。
3. **物理钩子**：必须锁定一个生活中的具体实物（如：颜色异常的包装、某个特定的App通知、丢失的钥匙）。

【输出模板】：
📅 **{day_label}是 {target_info['date']} ({target_info['gz_day']}日)**

📊 **能量收支看板**：
- 💰 财富：[变多/变少/持平] · [原因]
- 😊 心情：[变好/变坏/平静] · [诱因]

---
**💰 财运：** [1句话具体流向。若天干克地支（如戊子），写明‘虎头蛇尾’的表现]
**🤝 人际：** [1句话具体人物。若伏吟，写明是哪个‘老熟人’]
**😊 心情：** [1句话物理诱因。点破是因为哪个字导致的光明或阴影]
**🔮 能量预报：** [1句话真相]
**🚫 避雷清单：** (1) [具体动作] (2) [具体场景]
**✅ 转运清单：** (1) [具体动作] (2) **穿搭建议**：[材质/色系]
**💌 悄悄话：** [1句话专属贴士]

注意: 禁止使用 ### 标题。"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": f"你是一位能看透命运细枝末节、拒绝套话的极简主义导师。{role_style}"},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"算法正在对抗由于地支冲克带来的干扰: {str(e)}"

def send_to_feishu(title, content, color="orange"):
    if not FEISHU_WEBHOOK.startswith("http"): return
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": title}, "template": color},
            "elements": [{"tag": "markdown", "content": content}]
        }
    }
    requests.post(FEISHU_WEBHOOK, json=payload, timeout=15)

if __name__ == "__main__":
    if FEISHU_WEBHOOK and DEEPSEEK_API_KEY:
        offset = -1 
        info = get_target_info(offset=offset)
        
        profiles = [
            ("姐姐", {"bazi_summary": "1992壬申：身强水旺，忌金水。怕申亥穿。喜木火，怕枭神夺食。"}, "orange"),
            ("妹妹", {"bazi_summary": "1997丙午：从财格火局。忌癸水（遮光）、湿土（辰/丑）。喜火土（丙/丁/戌）。"}, "purple")
        ]
        
        for name, profile, color in profiles:
            content = get_ai_fortune(name, profile, info)
            send_to_feishu(f"🌟 {info['display_date']} | {name}专属推演", content, color)
