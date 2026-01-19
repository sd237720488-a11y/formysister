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

# 嵌入用户提供的六十甲子深度逻辑数据库
DAYS_DATABASE = {
    "甲子": {"Sister": {"Level": "C", "Tag": "子水生木", "Advice": "心情尚可，但容易花钱"}, "User": {"Level": "D", "Tag": "子午大冲", "Advice": "破财日！心脏不适，千万别交易"}},
    "乙丑": {"Sister": {"Level": "C", "Tag": "湿土克水", "Advice": "郁闷，觉得被管束"}, "User": {"Level": "C", "Tag": "丑戌相刑", "Advice": "晦气，内耗，容易和家里吵架"}},
    "丙寅": {"Sister": {"Level": "B", "Tag": "寅申相冲", "Advice": "头痛，焦虑，但也算动起来了"}, "User": {"Level": "S", "Tag": "寅午戌合", "Advice": "大吉！灵感爆发，财运起飞"}},
    "丁卯": {"Sister": {"Level": "A", "Tag": "丁壬相合", "Advice": "贵人运，有人请吃饭，开心"}, "User": {"Level": "A", "Tag": "卯戌合火", "Advice": "顺遂，适合恋爱或合作"}},
    "戊辰": {"Sister": {"Level": "B", "Tag": "申子辰水", "Advice": "平淡，甚至有点懒，想躺平"}, "User": {"Level": "D", "Tag": "辰戌大冲", "Advice": "动荡！根基受损，别出远门"}},
    "己巳": {"Sister": {"Level": "A", "Tag": "刑中带贵", "Advice": "虽然纠结，但能解决大问题"}, "User": {"Level": "A", "Tag": "火旺暖局", "Advice": "自信，搞钱，效率极高"}},
    "庚午": {"Sister": {"Level": "B", "Tag": "枭神夺食", "Advice": "有点委屈，但有财运补偿"}, "User": {"Level": "S", "Tag": "帝旺复辉", "Advice": "超级大吉！全场C位，收割财富"}},
    "辛未": {"Sister": {"Level": "A", "Tag": "燥土止水", "Advice": "稳重，踏实，适合处理家事"}, "User": {"Level": "S", "Tag": "午未合火", "Advice": "锁财日！利润入库，安全感满满"}},
    "壬申": {"Sister": {"Level": "D", "Tag": "伏吟+冲", "Advice": "极度抑郁，身体痛，甚至想哭"}, "User": {"Level": "C", "Tag": "冲日支", "Advice": "奔波，劳累，容易崴脚或受伤"}},
    "癸酉": {"Sister": {"Level": "C", "Tag": "金水太旺", "Advice": "冷漠，不想理人，社恐"}, "User": {"Level": "C", "Tag": "泄气", "Advice": "无聊，提不起劲，不想动"}},
    "甲戌": {"Sister": {"Level": "A", "Tag": "食神制杀", "Advice": "掌权，说话有分量，受人尊重"}, "User": {"Level": "S", "Tag": "火库大开", "Advice": "搞钱日！直觉最准，大胆操作"}},
    "乙亥": {"Sister": {"Level": "B", "Tag": "水木清华", "Advice": "温和，适合美容养生"}, "User": {"Level": "C", "Tag": "合绊", "Advice": "被拖累，资金被锁，想动动不了"}},
    "丙子": {"Sister": {"Level": "C", "Tag": "水克火", "Advice": "为了钱发愁，或者花销大"}, "User": {"Level": "D", "Tag": "子午冲", "Advice": "大凶！防血光、防大跌、闭关"}},
    "丁丑": {"Sister": {"Level": "C", "Tag": "争合", "Advice": "感情纠葛，容易吃醋"}, "User": {"Level": "C", "Tag": "丑戌刑", "Advice": "别扭，看谁都不顺眼，别买东西"}},
    "戊寅": {"Sister": {"Level": "C", "Tag": "寅申冲", "Advice": "受伤，开车小心，容易吵架"}, "User": {"Level": "A", "Tag": "三合火", "Advice": "启动！新的机会来了，抓住它"}},
    "己卯": {"Sister": {"Level": "B", "Tag": "官星合身", "Advice": "有桃花，或者工作顺利"}, "User": {"Level": "A", "Tag": "合火", "Advice": "人缘好，适合混圈子，聊八卦"}},
    "庚辰": {"Sister": {"Level": "B", "Tag": "拱水", "Advice": "糊涂，容易做错事，别签合同"}, "User": {"Level": "C", "Tag": "辰戌冲", "Advice": "又冲！情绪爆炸，想骂人"}},
    "辛巳": {"Sister": {"Level": "B", "Tag": "合水", "Advice": "暧昧，或者暗中有人帮忙"}, "User": {"Level": "A", "Tag": "火长生", "Advice": "回暖，看到希望，心情变好"}},
    "壬午": {"Sister": {"Level": "C", "Tag": "自刑", "Advice": "纠结，想买东西又心疼钱"}, "User": {"Level": "B", "Tag": "伏吟", "Advice": "亢奋，但有点乱，适合发泄(消费)"}},
    "癸未": {"Sister": {"Level": "A", "Tag": "杀印相生", "Advice": "解决难题，效率高"}, "User": {"Level": "S", "Tag": "合财", "Advice": "最稳的一天！也是买入的好时机"}},
    "甲申": {"Sister": {"Level": "D", "Tag": "比肩夺食", "Advice": "被抢功劳，甚至丢东西"}, "User": {"Level": "C", "Tag": "冲日支", "Advice": "身体不适，出行受阻，烦躁"}},
    "乙酉": {"Sister": {"Level": "C", "Tag": "杀旺", "Advice": "压力大，感觉被针对"}, "User": {"Level": "C", "Tag": "金克木", "Advice": "不爽，才华施展不出，别硬撑"}},
    "丙戌": {"Sister": {"Level": "S", "Tag": "偏财入库", "Advice": "发财日！可能有大红包"}, "User": {"Level": "S", "Tag": "火库归位", "Advice": "全盛时期！做最重要的决定"}},
    "丁亥": {"Sister": {"Level": "A", "Tag": "正财合身", "Advice": "幸福，有人宠，适合约会"}, "User": {"Level": "C", "Tag": "合绊", "Advice": "别买股票！容易被套牢"}},
    "戊子": {"Sister": {"Level": "C", "Tag": "水土混杂", "Advice": "浑浊，是非多，少说话"}, "User": {"Level": "D", "Tag": "子午大冲", "Advice": "极度危险！防诈骗，防破产"}},
    "己丑": {"Sister": {"Level": "C", "Tag": "湿土", "Advice": "最晦气，什么都不想做"}, "User": {"Level": "C", "Tag": "刑伤", "Advice": "家庭矛盾，或者是为了房子烦心"}},
    "庚寅": {"Sister": {"Level": "C", "Tag": "冲提纲", "Advice": "容易受伤，别去危险地方"}, "User": {"Level": "A", "Tag": "长生", "Advice": "生机勃勃，适合开始新计划"}},
    "辛卯": {"Sister": {"Level": "C", "Tag": "金克木", "Advice": "破财，买东西买贵了"}, "User": {"Level": "A", "Tag": "合火", "Advice": "顺利，怎么做都对"}},
    "壬辰": {"Sister": {"Level": "B", "Tag": "比肩入库", "Advice": "朋友聚会，花钱买开心"}, "User": {"Level": "C", "Tag": "冲库", "Advice": "动荡，可能要出一笔大钱"}},
    "癸巳": {"Sister": {"Level": "A", "Tag": "贵人", "Advice": "小确幸，心情不错"}, "User": {"Level": "A", "Tag": "临官", "Advice": "稳步上升，适合积累"}},
    "甲午": {"Sister": {"Level": "A", "Tag": "食神生财", "Advice": "才华变现，被人夸奖"}, "User": {"Level": "S", "Tag": "木火通明", "Advice": "巅峰！魅力最大的一天"}},
    "乙未": {"Sister": {"Level": "A", "Tag": "木库", "Advice": "舒服，有人依靠"}, "User": {"Level": "S", "Tag": "合火", "Advice": "存钱日，落袋为安"}},
    "丙申": {"Sister": {"Level": "C", "Tag": "偏财受克", "Advice": "想赚钱但赚不到，急"}, "User": {"Level": "C", "Tag": "冲驿马", "Advice": "忙乱，容易出错"}},
    "丁酉": {"Sister": {"Level": "B", "Tag": "财星长生", "Advice": "小钱进账"}, "User": {"Level": "C", "Tag": "金旺", "Advice": "平淡，没什么波澜"}},
    "戊戌": {"Sister": {"Level": "A", "Tag": "七杀", "Advice": "霸气，搞定难搞的人"}, "User": {"Level": "S", "Tag": "火库", "Advice": "地基稳固，适合置业"}},
    "己亥": {"Sister": {"Level": "B", "Tag": "官星合身", "Advice": "平稳，按部就班"}, "User": {"Level": "C", "Tag": "合绊", "Advice": "别动，容易踩坑"}},
    "庚子": {"Sister": {"Level": "C", "Tag": "金沉水底", "Advice": "绝望，看不到希望"}, "User": {"Level": "D", "Tag": "冲太岁", "Advice": "大凶！这一天躲起来！"}},
    "辛丑": {"Sister": {"Level": "C", "Tag": "入墓", "Advice": "自闭，不想说话"}, "User": {"Level": "C", "Tag": "刑", "Advice": "别扭，情绪低落"}},
    "壬寅": {"Sister": {"Level": "C", "Tag": "伏吟+冲", "Advice": "内耗，自己跟自己打架"}, "User": {"Level": "A", "Tag": "伏吟", "Advice": "自我觉醒，关注自己"}},
    "癸卯": {"Sister": {"Level": "B", "Tag": "水生木", "Advice": "懒散，享受生活"}, "User": {"Level": "A", "Tag": "桃花", "Advice": "美美的一天"}},
    "甲辰": {"Sister": {"Level": "B", "Tag": "拱水", "Advice": "随大流"}, "User": {"Level": "C", "Tag": "冲", "Advice": "脾气大，看谁都不爽"}},
    "乙巳": {"Sister": {"Level": "A", "Tag": "三刑带贵", "Advice": "虽然累，但收获很大"}, "User": {"Level": "A", "Tag": "木火", "Advice": "开心，适合打扮"}},
    "丙午": {"Sister": {"Level": "C", "Tag": "比劫夺财", "Advice": "钱被抢了，心疼"}, "User": {"Level": "S", "Tag": "伏吟", "Advice": "这就是我！自信爆棚"}},
    "丁未": {"Sister": {"Level": "S", "Tag": "合财", "Advice": "大吉！所有好事都来了"}, "User": {"Level": "S", "Tag": "合财", "Advice": "太稳了，躺赢"}},
    "戊申": {"Sister": {"Level": "C", "Tag": "杀印", "Advice": "压力大，但能扛"}, "User": {"Level": "C", "Tag": "冲", "Advice": "身体累"}},
    "己酉": {"Sister": {"Level": "B", "Tag": "官印", "Advice": "面子光鲜"}, "User": {"Level": "C", "Tag": "泄气", "Advice": "没意思"}},
    "庚戌": {"Sister": {"Level": "A", "Tag": "印库", "Advice": "想通了，变豁达了"}, "User": {"Level": "S", "Tag": "火库", "Advice": "搞钱搞钱搞钱"}},
    "辛亥": {"Sister": {"Level": "C", "Tag": "金水", "Advice": "冷漠，只想搞钱不谈感情"}, "User": {"Level": "C", "Tag": "合绊", "Advice": "又被套住了"}},
    "壬子": {"Sister": {"Level": "C", "Tag": "羊刃", "Advice": "暴躁，想打人"}, "User": {"Level": "D", "Tag": "最凶冲", "Advice": "灾难日。千万小心"}},
    "癸丑": {"Sister": {"Level": "C", "Tag": "湿土", "Advice": "像陷进泥里"}, "User": {"Level": "C", "Tag": "刑", "Advice": "烦死了"}},
    "甲寅": {"Sister": {"Level": "C", "Tag": "冲提", "Advice": "受伤，一定要小心"}, "User": {"Level": "S", "Tag": "长生", "Advice": "灵感之神降临"}},
    "乙卯": {"Sister": {"Level": "A", "Tag": "伤官", "Advice": "骂人，解气"}, "User": {"Level": "A", "Tag": "桃花", "Advice": "美美的一天"}},
    "丙辰": {"Sister": {"Level": "B", "Tag": "水库", "Advice": "平淡"}, "User": {"Level": "C", "Tag": "冲", "Advice": "不顺"}},
    "丁巳": {"Sister": {"Level": "A", "Tag": "合财", "Advice": "有钱拿"}, "User": {"Level": "S", "Tag": "帮身", "Advice": "给力"}},
    "戊午": {"Sister": {"Level": "A", "Tag": "杀印", "Advice": "有威严"}, "User": {"Level": "S", "Tag": "火土", "Advice": "靠山稳"}},
    "己未": {"Sister": {"Level": "A", "Tag": "燥土", "Advice": "帮身，有底气"}, "User": {"Level": "S", "Tag": "合", "Advice": "舒服"}},
    "庚申": {"Sister": {"Level": "D", "Tag": "伏吟", "Advice": "哭，想家"}, "User": {"Level": "C", "Tag": "冲", "Advice": "别出门"}},
    "辛酉": {"Sister": {"Level": "C", "Tag": "纯金", "Advice": "铁石心肠"}, "User": {"Level": "C", "Tag": "忌神", "Advice": "冷淡"}},
    "壬戌": {"Sister": {"Level": "A", "Tag": "财库", "Advice": "意外惊喜"}, "User": {"Level": "A", "Tag": "比肩坐库", "Advice": "有人带着赚钱"}},
    "癸亥": {"Sister": {"Level": "D", "Tag": "大水", "Advice": "大破财，捂紧口袋"}, "User": {"Level": "D", "Tag": "大忌", "Advice": "绝对空仓"}},
}

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
    day_label = "今日" if target_info['is_today'] else "当日"
    gz = target_info['gz_day']
    
    # 查找数据库逻辑
    db_entry = DAYS_DATABASE.get(gz, {})
    person_key = "Sister" if name == "姐姐" else "User"
    logic_from_db = db_entry.get(person_key, {"Level": "B", "Tag": "平稳", "Advice": "顺其自然"})
    
    if name == "姐姐":
        role_style = "温柔疗愈型知心大姐姐，极简表达。"
        persona_logic = "你是身强水旺的壬申姐姐，忌金水，喜木火。你需要排解压抑感。"
    else: # 妹妹
        role_style = "搞钱军师型，犀利直接，极简表达。"
        persona_logic = "你是从财格的丙午妹妹，火局女王。忌金水湿土。你需要高效搞钱。"

    prompt = f"""角色：{role_style}
推演对象：({name}) | 目标日期：{gz} ({target_info['date']})
【官方判词】：等级 {logic_from_db['Level']} | 标签 {logic_from_db['Tag']} | 核心建议：{logic_from_db['Advice']}

【底层逻辑】：
{persona_logic}

【任务指令】：
1. **严格对齐**：必须以【官方判词】的等级和建议为核心，进行生活化解读。
2. **当日总结置顶**：必须将核心建议放在输出的最开始。
3. **极简主义**：拒绝废话，每项1句话。
4. **物理钩子**：必须包含一个具体的物理实物。

【输出模板】：
💡 **当日总结**：
- {logic_from_db['Advice']}

📅 **{day_label}是 {target_info['date']} ({gz}日)**
评分：【{logic_from_db['Level']}】 | 标签：#{logic_from_db['Tag']}#

---
**💰 财运：** [结合官方建议的1句话流向]
**🤝 人际：** [1句话具体人物特征]
**😊 心情：** [结合官方建议的1句话心理表现]
**🔮 能量预报：** {logic_from_db['Advice']}
**🚫 避雷清单：** (1) [动作] (2) [场景]
**✅ 转运清单：** (1) [动作] (2) **穿搭建议**：[具体材质/色系]
**💌 悄悄话：** [1句话贴士]

注意: 禁止使用 ### 标题。"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "system", "content": f"你是一位完全遵循指定命理判词库进行解读的极简导师。{role_style}"},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"逻辑链受地支波动干扰: {str(e)}"

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
        # 修改这里：循环验证前4天到明天（共6天：-4, -3, -2, -1, 0, 1）
        for offset in range[0]:
            info = get_target_info(offset=offset)
            
            profiles = [
                ("姐姐", {}, "orange"),
                ("妹妹", {}, "purple")
            ]
            
            for name, profile, color in profiles:
                content = get_ai_fortune(name, profile, info)
                # 标题修改：增加日期和周几
                prefix = f"【验证D{offset}】" if offset != 1 else "【明日预告】"
                title_text = f"{prefix} 🌟 {info['display_date']} ({info['weekday']}) | {name}"
                send_to_feishu(title_text, content, color)
