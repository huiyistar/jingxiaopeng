import requests
import json

# ===== 修改这里 =====
BVID = "BV1oT4y1971w"          # 你的视频 BV 号
COVER_IMAGE = "images/cover.jpg"  # 你准备好的一张通用封面图路径（相对于仓库根目录）
OUTPUT_FILE = "videos.js"       # 输出文件名
# ===================

def fetch_pagelist(bvid):
    """获取分P列表"""
    url = "https://api.bilibili.com/x/player/pagelist"
    params = {"bvid": bvid, "jsonp": "jsonp"}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    resp = requests.get(url, params=params, headers=headers)
    data = resp.json()
    if data["code"] != 0:
        raise Exception(f"API 出错: {data['message']}")
    return data["data"]

def generate_videos_js(pages, cover_img):
    """生成 videos.js 文件内容"""
    lines = []
    lines.append("// 自动生成，共 {} 个分P".format(len(pages)))
    lines.append("const videos = [")
    for p in pages:
        title = p["part"].replace('"', '\\"').replace('\n', ' ')  # 转义双引号和换行
        line = f'  {{'
        line += f' title: "{title}",'
        line += f' img: "{cover_img}",'
        line += f' bvid: "{BVID}",'
        line += f' page: {p["page"]},'
        line += f' cid: "{p["cid"]}"'
        line += f' }},'
        lines.append(line)
    lines.append("];")
    return "\n".join(lines)

if __name__ == "__main__":
    print(f"正在获取 BV: {BVID} 的分P列表...")
    pages = fetch_pagelist(BVID)
    print(f"共获取到 {len(pages)} 个分P")
    js_content = generate_videos_js(pages, COVER_IMAGE)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"✅ 已生成 {OUTPUT_FILE}，包含 {len(pages)} 条视频数据")