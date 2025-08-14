from flask import Flask, request, jsonify, render_template
import requests
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)
# CORS(app)  # 添加这行启用CORS

# 系统提示词 - 定义AI的教学行为
SYSTEM_PROMPT = """
# 角色
你是一位教学助手，专注通过引导式提问引导学生解决问题。每次只提1个递进式问题，问题必须：
- 直接关联最终解法
- 有明确思考方向
- 基于学生上步回答
- 杜绝抽象表述
# 背景
学生会问你问题，学生问的第一个问题是需要解决的最终问题
# 约束
1. **问题设计铁律**：
   - 每次仅提1个关键问题 禁止多问
   - 当学生无法回答你的启发式问题（即学生说“不知道”等等话语时），你需要对学生无法回答的启发式问题进行简要回答，并进一步提出一个新的启发式问题
2. 用中文回复
3. 禁止脱离数学范畴的提问（如生活事例）
4. 你问的启发式问题必须与最终解法有关系，能够引导学生思考
5. 你问的启发式问题必须层层递进，能够一步步帮助学生理解问题
6. 你问的启发式问题不能过于抽象，例如“你能描述这个问题的约束吗？”是一个很抽象的问题
7. 禁止在回答时对学生问的数学问题进行大篇分析
"""

# 从环境变量获取API密钥
API_KEY = 'sk-1bbab15bb7e34c49989550da814c0526'
# API_KEY = os.getenv('DEEPSEEK_API_KEY')
API_URL = "https://api.deepseek.com/v1/chat/completions"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/tutor', methods=['POST'])
def tutor():
    data = request.json
    if 'question' not in data:
        return jsonify({"error": "Missing 'question' field"}), 400
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 模型和推理配置
    model_version = "deepseek-chat"  # 使用通用对话模型
    
    # 深度思考配置
    deep_thought_config = {
        "step_deep": True,          # 启用逐步推理
        "reasoning_depth": "high",   # 高深度推理
        "chain_of_thought": True,    # 思维链推理
        "pedagogical_focus": True    # 教学专注模式
    }
    
    payload = {
        "model": model_version,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": data['question']}
        ],
        "temperature": 0.8,        # 稍低的温度确保专注
        "max_tokens": 400,          # 控制响应长度
        **deep_thought_config       # 应用深度思考配置
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()  # 检查HTTP错误
        response_data = response.json()
        
        # 提取AI回复内容
        if 'choices' in response_data and response_data['choices']:
            ai_reply = response_data['choices'][0]['message']['content']
            return jsonify({"reply": ai_reply})
        else:
            return jsonify({"error": "No response from AI service"}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API request failed: {str(e)}"}), 500
    except ValueError:
        return jsonify({"error": "Invalid JSON response from API"}), 500

if __name__ == '__main__':
    # 从环境变量获取端口（Vercel 会自动设置）
    port = int(os.environ.get('PORT', 5000))
    # 关闭调试模式（生产环境必须）
    app.run(host='0.0.0.0', port=port, debug=False)