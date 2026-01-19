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
    全息扫描协议人格化版：将十神转化为具体的人物和场景。
    """
    day_label = "今日" if target_info['is_today'] else ("历史" if target_info['is_past'] else "明日")
    
    prompt = f"""你是一位精通盲派取象、擅长辩证逻辑、拒绝机械套公式的顶级命理导师。
请对用户 ({name}) 进行{day_label}推演。

【时空全景】：
- 当前大运：{profile['current_luck']}
- 宏观流转：{target_info['gz_year']}年 {target_info['gz_month']}月
- 微观切片：目标日期 {target_info['gz_day']}日

【用户原局】：
{profile['bazi_summary']}

【导师取象逻辑链指令】：
1. **官杀（克我者）的多维分析**：
   - 严禁机械对应。请结合【宫位】和【神煞】分析官杀的真实象义：
     * 若官杀动及日支（夫妻宫）：分析是否为配偶带来的压力、管束或亲密关系的摩擦。
     * 若官杀伴随刑穿：分析是否为“麻烦、官非、违章、病痛或不讲理的强制力”。
     * 若官杀在天干透出且被印化：分析是否为“领导的指令、正向的责任、或公家事务”。
2. **比劫（同我者）的辩证分析**：
   - 区分“助力”还是“分夺”。分析是闺蜜间的下午茶，还是有人在背后嚼舌根、抢功劳。
3. **财星（我克者）的虚实**：
   - 分析是“欲望的宣泄（花钱购物）”还是“利益的纠葛（谈钱伤感情）”。
4. **拒绝温吞话**：每个板块不超过2句，必须给出一个基于逻辑推导出的“确定性场景”。

【输出格式要求】：
 📅 **{day_label}是 {target_info['date']} ({target_info['gz_day']}日)**
 **💰 财运：** [谁在动你的钱？是欲望驱使、他人索取还是合同变动？]
 **🤝 人际：** [谁会找你？这种互动的本质是关怀、控制、竞争还是求助？点破背后的人格面具]
 **😊 心情：** [情绪的根源：是因为被束缚、被理解、还是因为事情脱离了掌控？]
 ---
 **🔮 能量天气预报：**
    [用最犀利的一句话点破：在今天这组干支下，哪种力量在主导你的生活切面？]
 **🚫 禁忌清单：**
    (1) [动作/对象] (2) [心智陷阱]
 **✅ 转运清单：**
    (1) [具体的破局动作] (2) **穿搭建议**：[材质与风格]
 **💌 悄悄话：** [一句话点拨本质]

注意: 严禁使用 ### 标题。"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": "你是一位说话刻薄但洞察力惊人的导师，擅长通过干支推演复杂的人性和具体的麻烦。"},
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
            "bazi_summary": "壬水身强偏印重。喜木火食伤泄秀。注意印旺则自省过度，流日见官杀易产生莫名负罪感或法律合规焦虑。"
        }
        
        queen_profile = {
            "current_luck": "2021-2030走【癸丑】大运（劫财带官杀）",
            "bazi_summary": "壬寅日柱三合火局。喜木火。注意原局寅木（食神）与流日官杀的‘食神制杀’或‘伤官见官’关系，判定是搞定麻烦还是自找麻烦。"
        }
        
        targets = [("姐姐", sister_profile, "orange"), ("妹妹", queen_profile, "purple")]
        for name, profile, color in targets:
            content = get_ai_fortune(name, profile, info)
            day_type = "验证" if offset <= 0 else "预报"
            custom_title = f"🌟 {info['display_date']} ({info['weekday']}) | {name}专属能量{day_type}"
            send_to_feishu(custom_title, content, color)
