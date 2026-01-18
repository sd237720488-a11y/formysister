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

def get_tomorrow_info():
    # 转换为北京时间并获取明天日期
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    tomorrow = now + datetime.timedelta(days=1)
    
    day = sxtwl.fromSolar(tomorrow.year, tomorrow.month, tomorrow.day)
    gz_day_idx = day.getDayGZ()
    return {
        "date": tomorrow.strftime("%Y-%m-%d"),
        "gz_day": GAN[gz_day_idx.tg] + ZHI[gz_day_idx.dz],
        "tg": GAN[gz_day_idx.tg],
        "dz": ZHI[gz_day_idx.dz]
    }

def get_ai_fortune(name, profile, target_info):
    # 核心 Prompt：融入梁湘润、盲派、子平、陆致极理论体系
    prompt = f"""你是一位综合了梁湘润（禄命/调候）、盲派（取象/干支互动）、子平（格用/生克）及陆致极（现代命理视角）理论精髓的命理导师。
请根据以下用户命盘和明天的干支，进行深度穿透分析，生成【{name}专属·明日能量指南】。

用户命盘 ({name}):{profile}
目标日期: {target_info['date']} ({target_info['gz_day']}日)

分析原则：
1. 理论支撑：结合流日干支对原局的刑冲破害、神煞变换（如驿马、禄神、羊刃）、纳音气场进行推演。
2. 真实推演：不要使用固定的形容词，要根据“干支真实作用关系”给出具体的预测。

输出格式:
- 📅 **明天是 {target_info['date']} · {target_info['gz_day']} 日**
- **💰 财运：** (基于财星、食伤与日主的动态关系，给出具体的财务气场描述)
- **🤝 人际：** (基于官杀、比劫的制化关系，给出人情往来的真实反馈)
- **😊 心情：** (基于调候用神、印星虚实，描述神智与心理的真实波动)
- ---
- **🔮 能量天气预报：**
    (用2-3句优美的短句描述核心感受，并点出明日干支对命盘的关键影响)
    - **🚫 禁忌清单 (别做！)：**
    (给出2条精炼的避坑建议)
    - **✅ 转运清单 (去做！)：**
    (1) [具体行动建议]
    (2) **明日穿搭建议**：[幸运色] + [风格建议] (原理：结合五行喜忌)
    - **💌 悄悄话：**
    (一句简短有力的鼓励)
注意: 严禁使用 ### 标题，必须使用 **粗体文字** 作为标题。文字少而精，总评放在最上面。"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": "你是一位命理造诣极深、融合各家所长、言辞犀利中正的专业导师。"},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 生成失败: {str(e)}"

def send_to_feishu(title, content, color="orange"):
    if not FEISHU_WEBHOOK.startswith("http"):
        print(f"Error: Webhook 地址无效: {FEISHU_WEBHOOK}")
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
    try:
        res = requests.post(FEISHU_WEBHOOK, json=payload, timeout=15)
        res.raise_for_status()
        print(f"成功推送: {title}")
    except Exception as e:
        print(f"推送失败: {str(e)}")

if __name__ == "__main__":
    if not FEISHU_WEBHOOK or not DEEPSEEK_API_KEY:
        print("Error: 环境变量缺失")
    else:
        info = get_tomorrow_info()
        
        # 姐姐命盘配置
        sister_profile = """
    - 核心格局: 壬水生于申月，偏印当令，身强比劫旺。
    - 关键神煞: 寅申冲（驿马逢冲）、枭神夺食。
    - 五行喜忌: 喜木（食伤泄秀）、火（财星制印）；忌金（印星）、水（比劫）。
    - 能量特点: 行动力强但易有内耗，需以火木调候化解申金之寒。
    """
        
        # 妹妹命盘配置
        queen_profile = """
    - 核心格局: 壬水坐寅，日柱壬寅，地支三合火局（从财/财旺）。
    - 关键神煞: 丑戌相刑（官杀内刑）、文昌贵人、偏印透干。
    - 五行喜忌: 喜火（财星顺局）、木（食伤生财）；忌水（比劫夺财）、金（印星逆局）。
    - 能量特点: 灵感极强且才华横溢，但官杀刑伤易带来潜在压力与完美主义倾向。
    """
        
        # 生成并推送
        targets = [
            ("姐姐", sister_profile, "orange"),
            ("妹妹", queen_profile, "purple")
        ]
        
        for name, profile, color in targets:
            print(f"正在为 {name} 进行深度命理推演...")
            content = get_ai_fortune(name, profile, info)
            send_to_feishu(f"🌟 {name}专属·明日能量指南", content, color)
        
        print(f"任务执行完毕，已发送明日 ({info['date']}) 的能量指南。")
