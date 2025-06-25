import requests
import json

def run_dify_workflow():
    url = "http://120.53.15.242:8091/v1/workflows/run" # 替换为实际 Dify API 地址
    api_key = "app-mdx5mQM01vTf9rx0I0Fb6f5P" # 替换为你的 API 密钥
    user_id = "user123" # 用户标识

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json;charset=UTF-8"
    }

    payload = {
        "inputs": {"input": "请输入你的任务描述"},
        "response_mode": "streaming", # 流式模式
        "user": user_id
    }

    try:
        response = requests.post(url, headers=headers, json=payload, stream=True)
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return

        print("开始接收流式响应...")
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8').strip()
                if decoded_line.startswith('data:'):
                    data = json.loads(decoded_line[5:].strip())
                    print("收到数据:", json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"请求发生错误: {e}")

if __name__ == "__main__":
    run_dify_workflow()