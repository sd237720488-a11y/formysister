import os
import requests
import json
from openai import OpenAI

# --- Configuration ---
# 飞书机器人 Webhook 地址
FEISHU_WEBHOOK_URL = os.environ.get("FEISHU_WEBHOOK_URL", "https://open.feishu.cn/open-apis/bot/v2/hook/4738fb14-a6b1-4391-a05c-2507ef5a46ff")
# OpenAI 客户端会自动从环境中读取 OPENAI_API_KEY
client = OpenAI()

def generate_fortune_guide():
    """使用 LLM 生成每日能量指南内容。"""
    print("正在生成每日能量指南内容...")
    
    # 系统提示词，定义 AI 的角色和输出格式要求
    system_prompt = (
        "你是一位专业的命理分析师，现在需要为用户生成一份'妹妹专属·每日能量指南'。 "
        "请严格按照以下要求生成内容，并使用 Markdown 格式返回，以便于飞书展示。 "
        "报告标题必须是 '妹妹专属·每日能量指南'。"
    )
    
    # 用户提示词，包含具体的内容要求和假设的“命盘”信息
    user_prompt = (
        f"请生成今天的每日能量指南。今天的日期是 {os.popen('date +%Y年%m月%d日').read().strip()}。"
        "请提供今日的整体运势分析，并基于'命盘'深度分析：用户今日需要关注人际关系和情绪稳定。 "
        "内容必须包含以下两个部分：\n"
        "1. **🚫 禁忌清单 (别做！)**：提供今日应避免的行为，至少3条。\n"
        "2. **✅ 转运清单 (去做！)**：提供今日应采取的积极行动，至少3条。"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        content = response.choices[0].message.content
        print("内容生成成功。")
        return content
    except Exception as e:
        print(f"内容生成失败: {e}")
        return None

def send_to_feishu(content):
    """将生成的 Markdown 内容通过飞书 Webhook 推送。"""
    if not FEISHU_WEBHOOK_URL or "YOUR_FEISHU_WEBHOOK_URL" in FEISHU_WEBHOOK_URL:
        print("错误：飞书 Webhook URL 未配置。")
        return False

    if not content:
        print("错误：内容为空，无法发送。")
        return False

    # 飞书机器人的 'post' 消息类型支持富文本
    payload = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": "妹妹专属·每日能量指南",
                    "content": [
                        [
                            {
                                "tag": "text",
                                "text": content
                            }
                        ]
                    ]
                }
            }
        }
    }

    print(f"正在发送消息到飞书 Webhook...")
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(FEISHU_WEBHOOK_URL, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print("消息发送成功！")
                return True
            else:
                print(f"飞书 API 返回错误: {result.get('msg')}")
                return False
        else:
            print(f"HTTP 请求失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"发送请求时发生异常: {e}")
        return False

def main():
    """主函数，执行生成和推送流程。"""
    guide_content = generate_fortune_guide()
    if guide_content:
        print("\n--- 生成的指南内容 ---\n")
        print(guide_content)
        print("\n----------------------\n")
        
        success = send_to_feishu(guide_content)
        if success:
            print("任务执行完毕：每日能量指南已成功推送到飞书。")
        else:
            print("任务执行失败：请检查 Webhook URL 和网络连接。")
    else:
        print("任务执行失败：未能生成指南内容。")

if __name__ == "__main__":
    main()
