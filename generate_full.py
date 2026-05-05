import os
import sys
import subprocess
import shutil
import requests
import json
import time
import argparse
from pathlib import Path

IMAGES_DIR = "images"
OUTPUT_JS = "videos.js"
TEMP_DIR = "temp_videos"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.bilibili.com/",
}

def fetch_pagelist(bvid):
    """获取分P列表"""
    url = "https://api.bilibili.com/x/player/pagelist"
    params = {"bvid": bvid, "jsonp": "jsonp"}
    resp = requests.get(url, params=params, headers=HEADERS)
    data = resp.json()
    if data["code"] != 0:
        raise Exception(f"获取分P列表失败: {data['message']}")
    return data["data"]

def download_part(bvid, page):
    """下载单个分P视频，返回视频文件路径"""
    video_url = f"https://www.bilibili.com/video/{bvid}?p={page}"
    out_dir = Path(TEMP_DIR) / bvid / f"p{page}"
    out_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(out_dir / f"{bvid}_p{page}.%(ext)s")

    cmd = [
        "yt-dlp",
        video_url,
        "-o", output_template,
        "--no-playlist",
        "--merge-output-format", "mp4",
        "--quiet",
        "--no-warnings"
    ]

    print(f"  📥 下载分P {page} ...")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"  ❌ 下载失败: {e.stderr}")
        return None

    video_files = list(out_dir.glob(f"{bvid}_p{page}*.mp4")) + \
                  list(out_dir.glob(f"{bvid}_p{page}*.mkv"))
    if not video_files:
        print(f"  ⚠️ 未找到视频文件")
        return None
    return video_files[0]

def capture_frame(video_path, output_image, offset=-1.0):
    """
    用 ffmpeg 截取一帧
    offset: 相对于视频末尾的偏移秒数，例如 -1 表示最后一秒
    """
    cmd = [
        "ffmpeg",
        "-sseof", str(offset),
        "-i", str(video_path),
        "-frames:v", "1",
        "-q:v", "2",
        "-y",
        str(output_image)
    ]
    print(f"  🎞️ 截取封面（偏移 {offset}s） → {output_image}")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ 截帧失败: {e.stderr}")
        return False

def process_single_page(p_info, bvid, fallback_img, offset):
    """处理一个分P：检查封面 -> 下载 -> 截帧"""
    page = p_info["page"]
    img_file = f"{bvid}_p{page}.jpg"
    img_path = os.path.join(IMAGES_DIR, img_file)

    if os.path.exists(img_path):
        print(f"  ✅ 封面已存在，跳过: {img_path}")
        return img_path

    video_file = download_part(bvid, page)
    if video_file is None:
        print(f"  ⚠️ 下载失败，使用占位封面")
        return fallback_img

    os.makedirs(IMAGES_DIR, exist_ok=True)
    success = capture_frame(video_file, img_path, offset)

    if not success:
        Path(img_path).unlink(missing_ok=True)
        return fallback_img
    return img_path

def generate_video_objects(pagelist, bvid, fallback_img):
    """生成视频数据列表（字典）"""
    videos = []
    for p in pagelist:
        page = p["page"]
        img_file = f"{bvid}_p{page}.jpg"
        img_path = os.path.join(IMAGES_DIR, img_file)
        # 统一使用正斜杠
        img_path = img_path.replace("\\", "/")
        if not os.path.exists(img_path):
            img_path = fallback_img.replace("\\", "/")
        videos.append({
            "title": p["part"],
            "img": img_path,
            "bvid": bvid,
            "page": page,
            "cid": p["cid"]
        })
    return videos

def read_existing_videos(filepath):
    """读出现有 videos.js 中的视频数组"""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    import re
    match = re.search(r"const\s+videos\s*=\s*(\[[\s\S]*?\]);", content)
    if not match:
        print("⚠️ 无法解析 videos.js，将备份原文件并重建。")
        shutil.copy(filepath, filepath + ".backup")
        return None
    try:
        videos = json.loads(match.group(1))
        return videos
    except json.JSONDecodeError:
        print("⚠️ videos.js 格式错误，备份后重建。")
        shutil.copy(filepath, filepath + ".backup")
        return None

def merge_videos(old_videos, new_videos):
    """合并去重（依据 bvid + page）"""
    merged = []
    seen = set()
    for v in old_videos:
        if "bvid" in v and "page" in v:
            merged.append(v)
            seen.add((v["bvid"], v["page"]))
    for v in new_videos:
        key = (v["bvid"], v["page"])
        if key not in seen:
            merged.append(v)
            seen.add(key)
    return merged

def write_videos_js(videos, filepath):
    """写入 videos.js 文件"""
    js_array = json.dumps(videos, ensure_ascii=False, indent=2)
    content = f"// 视频导航数据\nconst videos = {js_array};\n"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已写入 {filepath}，共 {len(videos)} 个视频")

def download_fallback_cover(bvid):
    """下载视频主封面作为占位图"""
    fallback_dir = os.path.join(IMAGES_DIR, "fallback")
    os.makedirs(fallback_dir, exist_ok=True)
    fallback_img = os.path.join(fallback_dir, f"{bvid}_fallback.jpg")
    if os.path.exists(fallback_img):
        return fallback_img

    api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    resp = requests.get(api_url, headers=HEADERS)
    data = resp.json()
    if data["code"] == 0:
        pic_url = data["data"]["pic"]
        img_data = requests.get(pic_url, headers=HEADERS).content
        with open(fallback_img, "wb") as f:
            f.write(img_data)
        print(f"📸 占位封面: {fallback_img}")
        return fallback_img
    else:
        try:
            from PIL import Image
            img = Image.new('RGB', (640, 360), color='gray')
            img.save(fallback_img)
            print(f"📸 灰色占位封面: {fallback_img}")
            return fallback_img
        except ImportError:
            print("❌ 无法获取占位封面，请手动放入", fallback_img)
            return None

def main():
    parser = argparse.ArgumentParser(description="为 B 站视频自动生成封面和 videos.js")
    parser.add_argument("bvid", help="视频 BV 号")
    parser.add_argument("--offset", type=float, default=-1.0,
                        help="截取帧相对于视频末尾的偏移秒数，默认 -1（最后一秒）。例如 0 表示最后一帧（末尾），-2 表示倒数第二秒。")
    parser.add_argument("--keep-video", action="store_true",
                        help="保留下载的临时视频（默认清理）")
    parser.add_argument("--overwrite", action="store_true",
                        help="覆盖现有 videos.js，否则追加")
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None:
        sys.exit("❌ 未找到 ffmpeg，请先安装。")
    if shutil.which("yt-dlp") is None:
        sys.exit("❌ 未找到 yt-dlp，请用 pip install yt-dlp 安装。")

    bvid = args.bvid
    print(f"🚀 获取 {bvid} 的分P列表...")
    try:
        pagelist = fetch_pagelist(bvid)
    except Exception as e:
        sys.exit(str(e))
    total = len(pagelist)
    print(f"共 {total} 个分P\n")

    fallback_img = download_fallback_cover(bvid)
    if fallback_img is None:
        sys.exit("无法获取占位封面，退出。")

    Path(TEMP_DIR).mkdir(exist_ok=True)

    for idx, p in enumerate(pagelist, 1):
        print(f"[{idx}/{total}] 分P {p['page']}: {p['part']}")
        process_single_page(p, bvid, fallback_img, args.offset)
        print("")

    new_videos = generate_video_objects(pagelist, bvid, fallback_img)

    output_path = Path(OUTPUT_JS)
    if output_path.exists() and not args.overwrite:
        old_videos = read_existing_videos(OUTPUT_JS)
        if old_videos is None:
            print("⚠️ 无法解析，将重建 videos.js")
            final_videos = new_videos
        else:
            final_videos = merge_videos(old_videos, new_videos)
            print(f"🔄 追加 {len(new_videos)} 个视频，合并后总计 {len(final_videos)}")
    else:
        final_videos = new_videos
        if output_path.exists():
            print("🔄 --overwrite 启用，覆盖原 videos.js")

    write_videos_js(final_videos, OUTPUT_JS)

    if not args.keep_video:
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        print("🗑️ 已删除临时视频。")
    else:
        print(f"📂 临时视频保留在: {TEMP_DIR}/")

    print("\n✅ 全部完成！")

if __name__ == "__main__":
    main()