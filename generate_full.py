import os
import sys
import subprocess
import shutil
import requests
import json
import time
from pathlib import Path

# ========== 配置区域 ==========
BVID = "BV1oT4y1971w"          # 你的视频 BV 号
IMAGES_DIR = "images"           # 封面输出目录
OUTPUT_JS = "videos.js"         # 最终数据文件
TEMP_DIR = "temp_videos"        # 临时视频存放目录（完成后自动删除）
# ==============================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.bilibili.com/",
}

def fetch_pagelist(bvid):
    """获取全部分P的 page, part, cid"""
    url = "https://api.bilibili.com/x/player/pagelist"
    params = {"bvid": bvid, "jsonp": "jsonp"}
    resp = requests.get(url, params=params, headers=HEADERS)
    data = resp.json()
    if data["code"] != 0:
        raise Exception(f"获取分P列表失败: {data['message']}")
    return data["data"]

def download_part(page):
    """
    用 yt-dlp 下载指定分P的视频，返回视频文件路径。
    下载到 TEMP_DIR/p{page}/ 目录，文件名自动生成。
    """
    video_url = f"https://www.bilibili.com/video/{BVID}?p={page}"
    output_dir = Path(TEMP_DIR) / f"p{page}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 输出模板：直接以页码命名，便于查找
    output_template = str(output_dir / f"p{page}.%(ext)s")

    cmd = [
        "yt-dlp",
        video_url,
        "-o", output_template,          # 输出路径模板
        "--no-playlist",                # 只下载这个分P（不下载整个播放列表）
        "--merge-output-format", "mp4", # 合并为 mp4
        "--quiet",                      # 减少日志输出（可选）
        "--no-warnings"
    ]

    print(f"  📥 正在下载分P {page}...")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"  ❌ yt-dlp 下载失败: {e.stderr}")
        return None

    # 查找下载的视频文件
    video_files = list(output_dir.glob("p{}.mp4".format(page))) + \
                  list(output_dir.glob("p{}.*.mp4".format(page))) + \
                  list(output_dir.glob("*.mp4")) + \
                  list(output_dir.glob("*.mkv"))
    if not video_files:
        print(f"  ⚠️ 未找到视频文件，可能下载失败。")
        return None
    return video_files[0]

def capture_last_frame(video_path, output_image):
    """用 ffmpeg 截取视频最后一秒的第一帧，保存为图片。"""
    cmd = [
        "ffmpeg",
        "-sseof", "-1",
        "-i", str(video_path),
        "-frames:v", "1",
        "-q:v", "2",           # JPG 高质量
        "-y",                  # 覆盖已有文件
        str(output_image)
    ]
    print(f"  🎞️ 截取最后一帧 → {output_image}")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ 截帧失败: {e.stderr}")
        return False

def process_single_page(p_info):
    """处理一个分P：下载、截帧，返回 img 路径"""
    page = p_info["page"]
    img_path = f"{IMAGES_DIR}/p{page}.jpg"
    if os.path.exists(img_path):
        print(f"  📷 分P {page} 封面已存在，跳过处理。")
        return img_path

    video_file = download_part(page)
    if video_file is None:
        return None  # 失败，后续使用 fallback

    os.makedirs(IMAGES_DIR, exist_ok=True)
    success = capture_last_frame(video_file, img_path)

    # 删除临时视频文件
    video_file.unlink(missing_ok=True)
    # 删除临时目录（如果为空）
    parent_dir = video_file.parent
    try:
        shutil.rmtree(parent_dir)
    except OSError:
        pass

    if not success:
        # 截帧失败，删除可能生成的不完整图片
        Path(img_path).unlink(missing_ok=True)
        return None
    return img_path

def generate_videos_js(pages_data):
    """生成 videos.js 文件内容"""
    lines = [
        "// 自动生成，每P封面取自最后一秒",
        "const videos = ["
    ]
    for p in pages_data:
        title = p["part"].replace('"', '\\"').replace('\n', ' ')
        img = p["img"]
        lines.append(
            '  {{ title: "{}", img: "{}", bvid: "{}", page: {}, cid: "{}" }},'.format(
                title, img, BVID, p["page"], p["cid"]
            )
        )
    lines.append("];")
    return "\n".join(lines)

def download_fallback_cover():
    """如果某个分P失败，使用视频主封面作为 fallback.jpg"""
    fallback_img = f"{IMAGES_DIR}/fallback.jpg"
    if os.path.exists(fallback_img):
        return
    print("📸 正在下载通用占位封面...")
    api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={BVID}"
    resp = requests.get(api_url, headers=HEADERS)
    data = resp.json()
    if data["code"] == 0:
        pic_url = data["data"]["pic"]
        img_data = requests.get(pic_url, headers=HEADERS).content
        os.makedirs(IMAGES_DIR, exist_ok=True)
        with open(fallback_img, "wb") as f:
            f.write(img_data)
        print(f"✅ 占位封面已保存: {fallback_img}")
    else:
        # 创建纯灰图片作为应急
        try:
            from PIL import Image
            img = Image.new('RGB', (640, 360), color='gray')
            os.makedirs(IMAGES_DIR, exist_ok=True)
            img.save(fallback_img)
            print(f"生成灰色占位封面: {fallback_img}")
        except ImportError:
            # 如果没有 Pillow，复制一张任意图片或放弃
            pass

def main():
    # 检查工具
    if shutil.which("ffmpeg") is None:
        sys.exit("❌ 未找到 ffmpeg，请先安装。")
    if shutil.which("yt-dlp") is None:
        sys.exit("❌ 未找到 yt-dlp，请用 pip install yt-dlp 安装。")

    print(f"🚀 获取视频 {BVID} 的分P列表...")
    pagelist = fetch_pagelist(BVID)
    total = len(pagelist)
    print(f"共 {total} 个分P\n")

    # 下载占位封面备用
    download_fallback_cover()
    fallback_img = f"{IMAGES_DIR}/fallback.jpg"

    Path(TEMP_DIR).mkdir(exist_ok=True)

    processed = []
    for idx, p in enumerate(pagelist, 1):
        print(f"[{idx}/{total}] 处理分P {p['page']}: {p['part']}")
        img = process_single_page(p)
        if img is None:
            print(f"  ⚠️ 分P {p['page']} 处理失败，使用占位封面。")
            img = fallback_img
        processed.append({
            "part": p["part"],
            "img": img,
            "page": p["page"],
            "cid": p["cid"]
        })
        print("")
        # 可选延迟，避免请求过快
        time.sleep(0.5)

    # 清理临时目录
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

    # 生成 videos.js
    js_content = generate_videos_js(processed)
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"✅ 全部完成！")
    print(f"   - 生成 {total} 条视频数据 → {OUTPUT_JS}")
    print(f"   - 封面图片保存在 {IMAGES_DIR}/ 文件夹中")
    print(f"   - 失败分P已使用 fallback.jpg 代替")
    print(f"请将 {IMAGES_DIR} 文件夹和 {OUTPUT_JS} 放入仓库根目录，推送即可。")

if __name__ == "__main__":
    main()