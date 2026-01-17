import sxtwl
import requests
import datetime
import os
from openai import OpenAI

# 环境变量获取
# 自动清洗 Webhook 地址，防止因为复制粘贴带入的引号或空格导致 URL 报错
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK", "").strip().strip('"').strip("'")

# 尝试从多个可能的变量名获取 Key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")

# 初始化 DeepSeek 客户端 (使用 OpenAI 兼容 SDK)
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com" # 指定 DeepSeek 的服务器地址
)

GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

def get_tomorrow_info():
    # GitHub Actions 运行在 UTC 时间，需转换为北京时间 (UTC+8)
    # 然后再增加 1 天，获取明天的信息
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
    prompt = f"""你是一位精通八字命理与心理疗愈的高维导航员。请根据以下用户命盘和目标日期的干支，生成一份【{name}专属·明日能量指南】。
用户命盘 ({name}):{profile}
目标日期: {target_info['date']} ({target_info['gz_day']}日)
要求:
1. 风格: 极简、通透、有共情力。文字要精炼，排版要疏朗，不要大段文字，多用短句和换行。
2. 格式:
    - 📅 **明天是 {target_info['date']} · {target_info['gz_day']} 日**
    - **总评：这是一个 [核心基调] 的日子。**
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
        # 使用 deepseek-chat 模型
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": "你是一位精通命理的专业导师。"},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 生成失败: {str(e)}"

def send_to_feishu(title, content, color="orange"):
    # 再次检查 URL 是否合法
    if not FEISHU_WEBHOOK.startswith("http"):
        print(f"Error: 飞书 Webhook 地址格式不合法。请检查 GitHub Secrets 配置。当前值: {FEISHU_WEBHOOK}")
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
        result = res.json()
        if result.get("code") != 0:
            print(f"飞书平台返回错误: {result.get('msg')} (错误码: {result.get('code')})")
        else:
            print(f"成功推送至飞书: {title}")
    except requests.exceptions.HTTPError as err:
        print(f"HTTP 请求错误: {err}")
    except Exception as e:
        print(f"推送过程发生意外错误: {str(e)}")

if __name__ == "__main__":
    # 调试信息
    print(f"Debug: FEISHU_WEBHOOK 存在: {bool(FEISHU_WEBHOOK)}")
    print(f"Debug: DEEPSEEK_API_KEY 存在: {bool(DEEPSEEK_API_KEY)}")

    if not FEISHU_WEBHOOK:
        print("Error: 环境变量 FEISHU_WEBHOOK 为空，请检查 GitHub Secrets 和 YAML 配置。")
    elif not DEEPSEEK_API_KEY:
        print("Error: 环境变量 DEEPSEEK_API_KEY 为空，请检查 GitHub Secrets 和 YAML 配置。")
    else:
        info = get_tomorrow_info()
        
        sister_profile = """
        - 八字: 壬申 戊申 壬午 壬寅
        - 格局: 身强比劫旺，枭神夺食（寅申冲），寅午半合火局。
        - 喜用: 木 (食伤)、火 (财)、燥土 (官杀)。
        - 忌神: 金 (印)、水 (比劫) 、湿土 (晦火)。
        """
        
        queen_profile = """
        - 核心动力: 寅午戌三合火局（创造力、激情、从财格）。
        - 灵魂暗礁: 丑戌刑 + 庚金偏印（原生家庭牵绊、内耗焦虑、完美主义）。
        - 才华通道: 壬寅日柱（自坐食神/文昌/驿马，表达欲、灵性直觉）。
        """
        
        # 批量获取并推送
        targets = [
            ("姐姐", sister_profile, "orange"),
            ("妹妹", queen_profile, "purple")
        ]
        
        for name, profile, color in targets:
            print(f"正在为 {name} 生成明日指南...")
            content = get_ai_fortune(name, profile, info)
            send_to_feishu(f"🌟 {name}专属·明日能量指南", content, color)
        
        print(f"所有推送任务已尝试执行完毕: 明日日期 {info['date']}")
