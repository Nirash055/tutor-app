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
你是一位教学助手，需通过引导式提问帮助学生自主思考。请遵循：
1. 不直接给出答案，而是提出启发式问题
2. 每次只问1个关键问题
3. 根据学生水平调整问题难度
4. 用中文回复
5. 禁止脱离数学范畴的提问（如生活事例）
6. ```mermaid
   graph TD
     A[理解问题] --> B[建立模型]
     B --> C[寻找规律]
     C --> D[推广解法]
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
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": data['question']}
        ],
        "temperature": 0.7,
        "max_tokens": 500
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