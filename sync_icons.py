import os
import json
import requests
from urllib.parse import urlparse

# ================= 配置 =================
# 目标源 JSON（Vercel 源）
SOURCE_URL = "https://emby-icon.vercel.app/TFEL-Emby.json"
# 保存的 JSON 文件名
OUTPUT_JSON_NAME = "TFEL-Emby-Mirror.json"
# 图片保存目录
ICONS_DIR = "icons"
# 目标分支名称 (存放图片和JSON的分支)
TARGET_BRANCH = "cdn"
# =======================================

def run():
    # 1. 获取当前仓库信息
    repo_full_name = os.environ.get("GITHUB_REPOSITORY")
    if not repo_full_name:
        print("错误：无法获取 GITHUB_REPOSITORY 环境变量")
        return

    # 构造 Base URL，注意这里强制使用了 TARGET_BRANCH (cdn)
    # 最终格式: https://ghproxy.net/https://raw.githubusercontent.com/用户/仓库/cdn/icons/
    base_url = f"https://ghproxy.net/https://raw.githubusercontent.com/{repo_full_name}/{TARGET_BRANCH}/{ICONS_DIR}/"
    
    print(f"当前仓库: {repo_full_name}")
    print(f"目标分支: {TARGET_BRANCH}")
    print(f"图片基准路径: {base_url}")

    # 2. 创建目录
    if not os.path.exists(ICONS_DIR):
        os.makedirs(ICONS_DIR)

    # 3. 下载原始 JSON
    print("正在下载原始 JSON...")
    try:
        resp = requests.get(SOURCE_URL, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"下载 JSON 失败: {e}")
        return

    # 4. 遍历并处理
    items = data if isinstance(data, list) else data.get("icons", [])
    print(f"找到 {len(items)} 个图标，开始同步...")

    count = 0
    for item in items:
        original_url = item.get('url') or item.get('Url')
        if not original_url: continue

        parsed = urlparse(original_url)
        filename = os.path.basename(parsed.path)
        if not filename: continue

        # A. 下载图片
        save_path = os.path.join(ICONS_DIR, filename)
        if not os.path.exists(save_path):
            try:
                img_resp = requests.get(original_url, timeout=15)
                if img_resp.status_code == 200:
                    with open(save_path, "wb") as f:
                        f.write(img_resp.content)
                else:
                    print(f"[ERR] 图片 404: {filename}")
            except Exception as e:
                print(f"[ERR] 下载异常 {filename}: {e}")
        
        # B. 修改链接指向 cdn 分支
        new_link = base_url + filename
        if 'url' in item: item['url'] = new_link
        if 'Url' in item: item['Url'] = new_link
        
        count += 1

    # 5. 保存 JSON
    with open(OUTPUT_JSON_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f
