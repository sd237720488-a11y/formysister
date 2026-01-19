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
    全息扫描协议客观中性版：拒绝恐吓式命理，还原磁场双面性。
    """
    day_label = "今日" if target_info['is_today'] else ("历史" if target_info['is_past'] else "明日")
    
    prompt = f"""你是一位推崇“道法自然、福祸相依”的命理宗师，视角冷静且中正客观。
请对用户 ({name}) 进行{day_label}推演。

【时空全景】：
- 当前大运：{profile['current_luck']}
- 宏观流转：{target_info['gz_year']}年 {target_info['gz_month']}月
- 微观切片：目标日期 {target_info['gz_day']}日

【用户原局】：
{profile['bazi_summary']}

【导师中正推演指令】：
1. **中性象义呈现**：
   - 严禁预设“好坏”。能量只有“聚散、强弱、流向”。
   - **官杀（克我者）**：它是“契约与边界”。正面为自律、效率、达成共识；负面为束缚、压力、摩擦。
   - **比劫（同我者）**：它是“共鸣与竞争”。正面为助力、归属感；负面为意见不合、资源瓜分。
   - **印星（生我者）**：它是“吸收与沉淀”。正面为领悟、受助、安稳；负面为迟缓、过度思虑。
2. **二元应验逻辑**：
   - 描述某种能量时，请同时点出其“顺势”的做法。
   - 错误：你会破财。
   - 正确：今日财星受制，主能量向内收敛。若主动消费或配置资源则顺应磁场，若被动守财则易生拉扯。
3. **具体生活镜像**：拒绝玄学黑话，将其翻译为具体的：社交姿态、金钱流转方向、精神专注点。
4. **极简约束**：每个板块不超过2句，只给客观的能量走向描述。

【输出格式要求】：
 📅 **{day_label}是 {target_info['date']} ({target_info['gz_day']}日)**
 **💰 财运：** [金钱流动的物理特征：是扩张、收缩、还是平衡？]
 **🤝 人际：** [磁场碰撞的形态：是由于什么力量导致了什么样的互动倾向？]
 **😊 心情：** [精神世界的状态描述：是松弛、紧致、奔流还是静止？]
 ---
 **🔮 能量天气预报：**
    [一句话客观描述：今日这组干支交汇下，最明显的磁场底色是什么？]
 **🚫 风险预警：**
    (1) [哪些动作会与今日磁场产生逆向摩擦] (2) [哪些心智状态容易导致错判]
 **✅ 顺势建议：**
    (1) [如何利用今日磁场实现能量闭环] (2) **风格参考**：[意象与材质]
 **💌 悄悄话：** [一句话点拨当下]

注意: 严禁使用 ### 标题。"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": "你是一位客观、冷静、不带个人情感色彩的命理研究者，擅长分析磁场规律。"},
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
            "current_luck": "2021-2030走【乙巳】大运（财运期）",
            "bazi_summary": "壬水身强偏印重。喜木火食伤泄秀。流日见刑穿时，主内在能量的重新排布，而非单纯的破坏。"
        }
        
        queen_profile = {
            "current_luck": "2021-2030走【癸丑】大运（劫财带官杀）",
            "bazi_summary": "壬寅日柱三合火局。喜木火。原局寅木是能量的触角，关注其在流日磁场中的伸展或收缩。"
        }
        
        targets = [("姐姐", sister_profile, "orange"), ("妹妹", queen_profile, "purple")]
        for name, profile, color in targets:
            content = get_ai_fortune(name, profile, info)
            day_type = "验证" if offset <= 0 else "预报"
            custom_title = f"🌟 {info['display_date']} ({info['weekday']}) | {name}专属能量{day_type}"
            send_to_feishu(custom_title, content, color)
