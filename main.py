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

def get_today_info():
    """获取【今天】的全方位干支信息，用于验证准确度"""
    # 转换为北京时间
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    
    day = sxtwl.fromSolar(now.year, now.month, now.day)
    
    gz_year = GAN[day.getYearGZ().tg] + ZHI[day.getYearGZ().dz]
    gz_month = GAN[day.getMonthGZ().tg] + ZHI[day.getMonthGZ().dz]
    gz_day = GAN[day.getDayGZ().tg] + ZHI[day.getDayGZ().dz]
    
    return {
        "date": now.strftime("%Y-%m-%d"),
        "display_date": now.strftime("%m月%d日"),
        "weekday": WEEK_MAP[now.weekday()],
        "gz_year": gz_year,
        "gz_month": gz_month,
        "gz_day": gz_day
    }

def get_ai_fortune(name, profile, target_info):
    """
    全息扫描协议升级版：强制 AI 执行地支+天干全关系动态检索。
    """
    prompt = f"""你是一位精通子平格局、盲派取象及《命理指要》逻辑的顶级命理导师。
请对用户 ({name}) 进行今日推演。

【时空全景】：
- 当前大运：{profile['current_luck']}
- 宏观流转：{target_info['gz_year']}年 {target_info['gz_month']}月
- 微观切片：今日 {target_info['gz_day']}日

【用户原局】：
{profile['bazi_summary']}

【导师全息分析指令（杜绝全盲区版）】：
1. **地支全关系检索**：
   - 依次扫描流日地支与【原局、大运、流年】的：合化、冲战、刑穿、六破。
   - 分析动作的优先级。例如：是否有“合中带穿”或“以冲破合”的象。
2. **天干动态扫描**：
   - **合化检索**：流日天干是否与大运、流年或原局天干构成“五合”？（如戊癸合、丁壬合）。合化后是变质为用神还是忌神？
   - **生克护卫**：流日天干是否造成了“伤官见官”、“枭神夺食”或“劫财夺财”？是否有财来破印的危机？
   - **虚实判定**：分析流日天干在流日地支中是否有根（如丙火见巳为实，见子为虚）。虚透之干主“虚象/幻想”，落地之支主“实事”。
3. **现代生活映射**：
   - 将复杂的生克关系翻译为：财务、人际、情绪三个维度的具体反馈。

【输出格式要求】：
 📅 **今天是 {target_info['date']} ({target_info['gz_day']}日)**
 **💰 财运：** (结合干支虚实，分析财星是被引动、克损、还是合入。区分“意外之财”与“消费支出”)
 **🤝 人际：** (分析干支合冲映射的社交真相，尤其是天干合化带来的关系变动)
 **😊 心情：** (结合天干清浊。重点分析天干是否受到大运压制或流日助长。忌神透干必主阴郁迷茫)
 ---
 **🔮 能量天气预报：**
    (犀利总结：在宏观大运背景下，今日流日气场最关键的一点“命理化学反应”。)
 **🚫 禁忌清单 (必做2点)：**
 **✅ 转运清单 (必做2点)：**
    (1) [具体的动作建议]
    (2) **穿搭建议**：[幸运色+风格]
 **💌 悄悄话：**

注意: 严禁使用 ### 标题。"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": "你是一位言辞犀利、中正客观、能透视命运底层逻辑的导师。"},
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
        # 已改为获取今天信息
        info = get_today_info()
        
        sister_profile = {
            "current_luck": "2021-2030走【乙巳】大运（巳火财星运）；2031-2040走【甲辰】大运",
            "bazi_summary": "壬水身强，偏印当令。喜木火（食伤生财），忌金水（印比夺食）。注意：大运乙木透干被原局偏印克制的情况。"
        }
        
        queen_profile = {
            "current_luck": "2021-2030走【癸丑】大运（丑土运，忌神透干）；2031-2040走【甲寅】大运",
            "bazi_summary": "壬寅日柱，地支三合火局（从财意向）。喜木火，忌金水。注意：壬水日主极反感癸水透干之“乌云蔽日”对格局的干扰，及流日天干与癸水的合化关系。"
        }
        
        targets = [("姐姐", sister_profile, "orange"), ("妹妹", queen_profile, "purple")]
        for name, profile, color in targets:
            content = get_ai_fortune(name, profile, info)
            custom_title = f"🌟 {info['display_date']} ({info['weekday']}) | {name}专属能量指南"
            send_to_feishu(custom_title, content, color)
