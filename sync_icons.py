import os
import json
import requests
import copy
from urllib.parse import urlparse

# ================= 配置 =================
SOURCE_URL = "https://emby-icon.vercel.app/TFEL-Emby.json"

ICONS_DIR = "icons"
TARGET_BRANCH = "icon"

OUTPUT_FILES = {
    "jsdelivr": "TFEL-Emby-jsdelivr.json",
    "statically": "TFEL-Emby-statically.json",
    "fastgit": "TFEL-Emby-fastgit.json",
    "ghproxy": "TFEL-Emby-ghproxy.json",
    "raw": "TFEL-Emby-raw.json"
}
# =======================================


def generate_cdn_url(repo, branch, filename, cdn_type):
    base_raw = f"https://raw.githubusercontent.com/{repo}/{branch}/icons/{filename}"

    if cdn_type == "jsdelivr":
        return f"https://cdn.jsdelivr.net/gh/{repo}@{branch}/icons/{filename}"

    elif cdn_type == "statically":
        return f"https://cdn.statically.io/gh/{repo}/{branch}/icons/{filename}"

    elif cdn_type == "fastgit":
        return f"https://raw.fastgit.org/{repo}/{branch}/icons/{filename}"

    elif cdn_type == "ghproxy":
        return f"https://ghproxy.net/{base_raw}"

    elif cdn_type == "raw":
        return base_raw

    return base_raw


def process_items(items, repo, branch, cdn_type, download=False):
    count = 0

    for item in items:
        original_url = item.get('url') or item.get('Url')
        if not original_url:
            continue

        parsed = urlparse(original_url)
        filename = os.path.basename(parsed.path)
        if not filename:
            continue

        # 下载图片（只执行一次）
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

        # 替换 URL
        new_url = generate_cdn_url(repo, branch, filename, cdn_type)

        if 'url' in item:
            item['url'] = new_url
        if 'Url' in item:
            item['Url'] = new_url

        count += 1

    return count


def run():
    repo_full_name = os.environ.get("GITHUB_REPOSITORY")
    if not repo_full_name:
        print("错误：无法获取 GITHUB_REPOSITORY 环境变量")
        return

    print(f"当前仓库: {repo_full_name}")

    if not os.path.exists(ICONS_DIR):
        os.makedirs(ICONS_DIR)

    # 1. 下载原始 JSON
    print("正在下载原始 JSON...")
    try:
        resp = requests.get(SOURCE_URL, timeout=30)
        resp.raise_for_status()
        original_data = resp.json()
    except Exception as e:
        print(f"下载 JSON 失败: {e}")
        return

    # 2. 获取 items
    base_items = original_data if isinstance(original_data, list) else original_data.get("icons", [])

    print(f"找到 {len(base_items)} 个图标")

    # 3. 为每个 CDN 生成一个 JSON
    for cdn_type, filename in OUTPUT_FILES.items():
        print(f"正在生成: {cdn_type}")

        data_copy = copy.deepcopy(original_data)
        items = data_copy if isinstance(data_copy, list) else data_copy.get("icons", [])

        process_items(
            items,
            repo_full_name,
            TARGET_BRANCH,
            cdn_type,
            download=(cdn_type == "jsdelivr")  # 只下载一次
        )

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data_copy, f, ensure_ascii=False, indent=2)

        print(f"✅ 已生成: {filename}")

    print("🎉 全部处理完成！")


if __name__ == "__main__":
    run()
