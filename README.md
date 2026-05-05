
# 🎬 B站视频导航站

一个简单但强大的**视频收藏夹网页**，以卡片网格展示你的 B 站视频合集，支持搜索、无限滚动加载、点击播放（内嵌 B 站播放器，手机端自动适配分 P）。

全部托管在 **GitHub Pages** 上，零成本、免服务器。

---

## ✨ 功能一览

- 📸 **自动生成视频封面**（自动下载每个分P，自定义截取时间点）
- 🔍 **实时搜索视频标题**
- 📱 **手机端完美适配**（自动使用正确的分P播放器）
- ♾️ **无限滚动加载**（几百个视频也不会卡顿）
- 🚀 **一键追加新视频**（不覆盖原有手动的数据）
- 🎨 **整洁卡片布局**，封面完整显示，整齐对齐
- ⚙️ **命令行高度可配置**（截取偏移、保留视频、覆盖模式）

---

## 📦 本地环境准备（只需一次）

你需要安装三个免费工具：

### 1. Python
- 下载：https://www.python.org/downloads/
- 安装时勾选 **Add Python to PATH**（Windows）

### 2. ffmpeg
- Windows：下载 [ffmpeg-release-essentials.zip](https://www.gyan.dev/ffmpeg/builds/)，解压后将 `bin` 文件夹路径添加到系统环境变量 `PATH`（[图文教程](https://zhuanlan.zhihu.com/p/118362010)）
- macOS：`brew install ffmpeg`
- Linux：`sudo apt install ffmpeg`

### 3. yt-dlp
打开终端（命令提示符/PowerShell/终端），输入：
```bash
pip install yt-dlp
```

验证安装：
```bash
python --version
ffmpeg -version
yt-dlp --version
```

---

## 🚀 快速开始：生成你的第一个视频导航站

### 第一步：下载项目文件

- 下载本仓库的文件 `index.html`、`generate_full.py`（`generate_full.py` 放本地，不上传 GitHub）

### 第二步：运行生成脚本

打开终端，进入脚本所在目录，运行：

```bash
python generate_full.py BV1oT4y1971w
```

等待脚本完成（分P越多下载越久），你将得到：
- `images/` 文件夹（每个分P的封面图）
- `videos.js`（视频数据文件）

### 第三步：预览
双击 `index.html`，即可在浏览器中看到你的视频墙。

---

## 🌐 部署到 GitHub Pages（免费上线）

### 1. 创建 GitHub 仓库
- 登录 [GitHub](https://github.com)，点击右上角 **+** → **New repository**
- 仓库名随意（如 `my-videos`），设为 **Public**，不要勾选“Add a README file”，点击 Create。

### 2. 上传文件
进入仓库，点击 ** uploading an existing file**，上传：
- `index.html`
- `videos.js`
- 整个 `images` 文件夹（直接拖入，有一百个文件限制）

点击 **Commit changes**。

最好还是本地用命令行，  
配置好下载git客户端，  （[下载git客户端](https://git-scm.com/install/windows)）
在项目文件夹下：  
-`git init` 初始化  
-`git add .`添加所有文件
-`git commit -m "提交记录"`  添加提交记录
-`git push origin main`  更新到github远程仓库

### 3. 开启 GitHub Pages
- 仓库页面点 **Settings** → 左侧 **Pages**
- **Branch** 选择 `main`，文件夹选 **/ (root)**，点 **Save**
- 稍等片刻，页面顶部会显示你的网址：`https://你的用户名.github.io/仓库名/`

### 4. 完成！
用浏览器访问该网址，你的视频导航站就上线了。

---

## 🔄 如何更新视频

### 追加新视频（推荐）
```bash
python generate_full.py 另一个BV号
```
- 自动追加到 `videos.js` 末尾（去重）
- 已存在的封面会跳过下载
- 上传新的 `videos.js` 和新增的封面到 GitHub 仓库即可

### 覆盖整个视频集
```bash
python generate_full.py BV号 --overwrite
```

### 手动添加单条视频
编辑 `videos.js`，按以下格式增加条目：
```json
{
  "title": "视频标题",
  "img": "images/你的封面.jpg",
  "bvid": "BVxxxxxx",
  "page": 1,
  "cid": "123456"
}
```

---

## 🎛️ 命令行参数详解

| 参数 | 作用 | 示例 |
|------|------|------|
| `bvid` | **必填**，视频的 BV 号 | `python generate_full.py BV1oT4y1971w` |
| `--offset` | 截取帧相对于**末尾**的偏移秒数，**默认 -1**（最后一秒）。例如 `-2` 表示倒数第二秒，`0` 表示最后一帧（末尾）。 | `python generate_full.py BV1xx --offset -2` |
| `--keep-video` | 保留下载的临时视频文件（默认自动删除） | `python generate_full.py BV1xx --keep-video` |
| `--overwrite` | 覆盖现有 `videos.js`（默认追加） | `python generate_full.py BV1xx --overwrite` |

### 使用场景举例

**1. 想要倒数第 3 秒的封面**
```bash
python generate_full.py BV1oT4y1971w --offset -3
```

**2. 下载并保留所有原始视频（用于后期手动截图）**
```bash
python generate_full.py BV1oT4y1971w --keep-video
```

**3. 重新生成，丢弃之前手动添加的视频**
```bash
python generate_full.py BV1oT4y1971w --overwrite
```

---

## 📁 文件结构说明

```
你的本地项目目录/
├── index.html          ← 网站主页面（需上传）
├── generate_full.py    ← 本地脚本（不上传）
├── videos.js           ← 视频数据（需上传）
└── images/
    ├── BVxxxx_p1.jpg   ← 自动封面
    ├── fallback/       ← 占位封面（下载失败时使用）
    └── ...
```

---

#### 生成你自己的视频时，可以不下载images文件夹(过于庞大)和videos.js 

## ❓ 常见问题

### Q: 手机上看视频始终是第一个分P？
A: `index.html` 已内置移动端播放器修复，会自动使用专用播放器，支持分P。请确保使用最新版。

### Q: 图片加载不出来？
A: 检查 `videos.js` 中的 `img` 路径是否正确，应使用正斜杠（如 `"images/BV1xx_p1.jpg"`），且文件名与 `images/` 文件夹内一致。

### Q: 下载视频失败（403/404）？
A: 可能是网络问题或B站限制。建议：
- 重启网络后重试
- 使用 `--keep-video` 保留已下载视频，避免重复下载
- 如需登录，可添加 Cookie：`--cookie cookies.txt`（需自行从浏览器导出）

### Q: 如何修改每页加载的卡片数量？
A: 打开 `index.html`，找到 `const PAGE_SIZE = 20;`，将 `20` 改为你想要的数字。

### Q: 我可以用自己的封面图吗？
A: 可以！直接将封面图放入 `images/` 文件夹，并修改 `videos.js` 中对应视频的 `"img"` 字段指向该文件即可。

---

## 📜 许可
本项目使用 MIT License，可自由修改分发。

**觉得有用？请点个 Star ⭐ 支持一下！**
```