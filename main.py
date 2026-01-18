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
    # 核心 Prompt：聚焦于财运、人际和心情
    prompt = f"""你是一位精通八字命理的导航员。请根据以下用户命盘和明天的干支，生成一份【{name}专属·明日能量指南】。
用户命盘 ({name}):{profile}
目标日期: {target_info['date']} ({target_info['gz_day']}日)

要求:
1. 风格: 中正、客观、精炼。
2. 格式:
    - 📅 **明天是 {target_info['date']} · {target_info['gz_day']} 日**
    - **💰 财运指数：[用1-5颗星表示]**
    - **🤝 人际指数：[用1-5颗星表示]**
    - **😊 心情指数：[用1-5颗星表示]**
    - ---
    - **🔮 能量天气预报：**
    (根据干支生克，用1-2句短句客观描述明日核心气场)
    - **🚫 禁忌：** [精炼建议]
    - **✅ 转运：** [精炼建议]
    - **👗 穿搭：** [幸运色+五行风格建议]
注意: 严禁使用 ### 标题，必须使用 **粗体文字** 作为标题。文字少而精，不要有阅读压力。"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": "你是一位精通命理、言辞中正的专业导师。"},
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
        print("Error: 环境变量缺失，请检查 GitHub Secrets 配置。")
    else:
        # 获取明天信息
        info = get_tomorrow_info()
        
        # 姐姐命盘配置 (统一为中正的学术描述)
        sister_profile = """
    - 核心格局: 壬水生于申月，偏印当令，身强比劫旺。
    - 关键神煞: 寅申冲（驿马逢冲）、枭神夺食。
    - 五行喜忌: 喜木（食伤泄秀）、火（财星制印）；忌金（印星）、水（比劫）。
    - 能量特点: 行动力强但易有内耗，需以火木调候化解申金之寒。
    """
        
        # 妹妹命盘配置 (统一为中正的学术描述)
        queen_profile = """
    - 核心格局: 壬水坐寅，日柱壬寅，地支三合火局（从财/财旺）。
    - 关键神煞: 丑戌相刑（官杀内刑）、文昌贵人、偏印透干。
    - 五行喜忌: 喜火（财星顺局）、木（食伤生财）；忌水（比劫夺财）、金（印星逆局）。
    - 能量特点: 灵感极强且才华横溢，但官杀刑伤易带来潜在压力与完美主义倾向。
    """
        
        # 生成并推送姐姐的指南
        print("正在生成姐姐的明日指南...")
        sister_content = get_ai_fortune("姐姐", sister_profile, info)
        send_to_feishu("🌟 姐姐专属·明日能量指南", sister_content, "orange")
        
        # 生成并推送妹妹的指南
        print("正在生成妹妹的明日指南...")
        queen_content = get_ai_fortune("妹妹", queen_profile, info)
        send_to_feishu("👑 妹妹专属·明日能量指南", queen_content, "purple")
        
        print(f"任务执行完毕，已发送明日 ({info['date']}) 的能量指南。")
