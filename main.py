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
    
    # 注入隐藏逻辑补丁
    if name == "姐姐":
        role_style = "温柔疗愈型知心大姐姐，极简表达。"
        logic_patch = """
        - 补充逻辑：警惕‘金多水浊’。若流日金旺（申/酉/丑），不仅是累，更是‘枭神夺食’引发的沟通误会或自我怀疑。
        - 亥水预警：申亥穿是‘内耗’，重点提醒不要在洗手间或阴冷处发呆。
        """
    else: # 妹妹
        role_style = "搞钱军师型，犀利直接，极简表达。"
        logic_patch = """
        - 补充逻辑：警惕‘湿木不生火’（如寅亥合）。若见亥水，不是简单的克，是‘羁绊’。会让你的‘从财格’使不上劲，变成功亏一篑。
        - 湿土预警：辰/丑日是‘晦火’，代表项目被搁置或遇到‘软钉子’。
        """

    prompt = f"""角色：{role_style}
推演对象：({name}) | 目标日期：{target_info['gz_day']}

【底层算法】：
{profile['bazi_summary']}
{logic_patch}

【神准判定指令】：
1. **穿透地支真相**：判断当日地支({target_info['gz_day'][1]})与原局的冲、穿、合、破。
2. **拒绝空洞**：必须包含一个‘物理钩子’（如：某个特定颜色的图标、手机掉电快、某个姓氏的人）。
3. **收支看板**：明确财富和心情的涨跌方向。

【输出模板】：
📅 **{day_label}是 {target_info['date']} ({target_info['gz_day']}日)**

📊 **能量收支看板**：
- 💰 财富：[变多/变少/持平] · [原因]
- 😊 心情：[变好/变坏/平静] · [诱因]

---
**💰 财运：** [1句话具体流向。忌神日需写明是被谁‘割韭菜’]
**🤝 人际：** [1句话人物特征。喜神日写明谁是‘财神’]
**😊 心情：** [1句话物理诱因。点破是因为哪个字导致的心理变化]
**🔮 能量预报：** [1句话真相]
**🚫 避雷清单：** (1) [具体动作] (2) [具体物件]
**✅ 转运清单：** (1) [具体动作] (2) **穿搭建议**：[具体材质/色系]
**💌 悄悄话：** [1句话贴士]

注意: 禁止使用 ### 标题。"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": f"你是一位精通地支细节、拒绝废话的命理大师。{role_style}"},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"系统开小差了: {str(e)}"

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
        offset = -3 
        info = get_target_info(offset=offset)
        
        profiles = [
            ("姐姐", {"bazi_summary": "1992壬申：身强水旺，忌金水，怕申亥穿。喜木火，怕枭神夺食。"}, "orange"),
            ("妹妹", {"bazi_summary": "1997丙午：从财格火局，忌金水湿土，怕亥合熄火。喜火土，怕湿木不生火。"}, "purple")
        ]
        
        for name, profile, color in profiles:
            content = get_ai_fortune(name, profile, info)
            send_to_feishu(f"🌟 {info['display_date']} | {name}专属推演", content, color)
