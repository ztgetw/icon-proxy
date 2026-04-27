import os
import json
import requests
import copy
from urllib.parse import urlparse

# ================= 配置 =================
SOURCE_URL = "https://emby-icon.vercel.app/TFEL-Emby.json"

OUTPUT_FILE = "TFEL-Emby-MultiCDN.json"

ICONS_DIR = "icons"
TARGET_BRANCH = "icon"
# =======================================


def generate_cdn_urls(repo_full_name, branch, filename):
    """
    生成多个 CDN 加速链接（按优先级排序）
    """
    base_raw = f"https://raw.githubusercontent.com/{repo_full_name}/{branch}/icons/{filename}"

    return [
        # 🥇 jsDelivr（最稳）
        f"https://cdn.jsdelivr.net/gh/{repo_full_name}@{branch}/icons/{filename}",

        # 🥈 Statically（国内快）
        f"https://cdn.statically.io/gh/{repo_full_name}/{branch}/icons/{filename}",

        # 🥉 FastGit
        f"https://raw.fastgit.org/{repo_full_name}/{branch}/icons/{filename}",

        # 备用 ghproxy
        f"https://ghproxy.net/{base_raw}",

        # 最后兜底（官方）
        base_raw
    ]


def process_items(items, repo_full_name, branch, download=False, multi_url=True):
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

        # 🚀 多 CDN
        cdn_urls = generate_cdn_urls(repo_full_name, branch, filename)

        # 是否使用多 URL fallback
        new_value = cdn_urls if multi_url else cdn_urls[0]

        if 'url' in item:
            item['url'] = new_value
        if 'Url' in item:
            item['Url'] = new_value

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

    # 2. 深拷贝
    data = copy.deepcopy(original_data)

    items = data if isinstance(data, list) else data.get("icons", [])

    print(f"找到 {len(items)} 个图标，开始处理...")

    # 3. 处理数据（开启多 CDN）
    process_items(
        items,
        repo_full_name,
        TARGET_BRANCH,
        download=True,
        multi_url=True
    )

    # 4. 保存 JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 处理完成！输出文件: {OUTPUT_FILE}")


if __name__ == "__main__":
    run()
