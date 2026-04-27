import os
import json
import requests
import copy
from urllib.parse import urlparse

# ================= 配置 =================
# 目标源 JSON
SOURCE_URL = "https://emby-icon.vercel.app/TFEL-Emby.json"

# 输出文件名 1 (ghproxy)
OUTPUT_GHPROXY = "TFEL-Emby-Mirror.json"
# 输出文件名 2 (jsDelivr)
OUTPUT_JSDELIVR = "TFEL-Emby-Jsdelivr.json"

# 图片保存目录
ICONS_DIR = "icons"
# 目标分支名称
TARGET_BRANCH = "icon"
# =======================================

def process_items(items, base_url, download=False):
    """
    处理列表中的 URL：
    1. 如果 download=True，下载图片到本地
    2. 将 URL 替换为 base_url + 文件名
    """
    count = 0
    for item in items:
        original_url = item.get('url') or item.get('Url')
        if not original_url: continue

        parsed = urlparse(original_url)
        filename = os.path.basename(parsed.path)
        if not filename: continue

        # 仅在第一次处理时下载图片
        if download:
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

        # 替换链接
        new_link = base_url + filename
        if 'url' in item: item['url'] = new_link
        if 'Url' in item: item['Url'] = new_link
        
        count += 1
    return count

def run():
    repo_full_name = os.environ.get("GITHUB_REPOSITORY")
    if not repo_full_name:
        print("错误：无法获取 GITHUB_REPOSITORY 环境变量")
        return

    # 1. 定义两个加速域名的 Base URL
    # Ghproxy: https://ghproxy.net/https://raw.githubusercontent.com/用户/仓库/分支/icons/
    url_gh = f"https://ghproxy.net/https://raw.githubusercontent.com/{repo_full_name}/{TARGET_BRANCH}/{ICONS_DIR}/"
    
    # jsDelivr: https://cdn.jsdelivr.net/gh/用户/仓库@分支/icons/
    # 注意：jsDelivr 推荐使用 @分支名 来定位
    url_js = f"https://cdn.jsdelivr.net/gh/{repo_full_name}@{TARGET_BRANCH}/{ICONS_DIR}/"

    print(f"当前仓库: {repo_full_name}")
    print(f"Ghproxy Base: {url_gh}")
    print(f"jsDelivr Base: {url_js}")

    if not os.path.exists(ICONS_DIR):
        os.makedirs(ICONS_DIR)

    # 2. 下载原始数据
    print("正在下载原始 JSON...")
    try:
        resp = requests.get(SOURCE_URL, timeout=30)
        resp.raise_for_status()
        original_data = resp.json()
    except Exception as e:
        print(f"下载 JSON 失败: {e}")
        return

    # 3. 准备两份数据副本
    data_gh = copy.deepcopy(original_data)
    data_js = copy.deepcopy(original_data)

    items_gh = data_gh if isinstance(data_gh, list) else data_gh.get("icons", [])
    items_js = data_js if isinstance(data_js, list) else data_js.get("icons", [])

    print(f"找到 {len(items_gh)} 个图标，开始处理...")

    # 4. 处理数据
    # 第一遍：生成 ghproxy 数据，同时负责下载图片 (download=True)
    process_items(items_gh, url_gh, download=True)
    
    # 第二遍：生成 jsDelivr 数据，不需要再下载图片了 (download=False)
    process_items(items_js, url_js, download=False)

    # 5. 保存两个 JSON 文件
    with open(OUTPUT_GHPROXY, "w", encoding="utf-8") as f:
        json.dump(data_gh, f, ensure_ascii=False, indent=2)
    
    with open(OUTPUT_JSDELIVR, "w", encoding="utf-8") as f:
        json.dump(data_js, f, ensure_ascii=False, indent=2)

    print(f"处理完成！\n生成文件 1: {OUTPUT_GHPROXY}\n生成文件 2: {OUTPUT_JSDELIVR}")

if __name__ == "__main__":
    run()
