# 北京大学工学院新生生存手册

本项目同时维护《北京大学工学院新生生存手册》的 PDF 和静态网站。正文只维护一份：`content/` 中的 LaTeX 文件既用于编译 PDF，也由 Python 构建脚本转换成网页，避免两边手工复制后内容逐渐不一致。

## 项目产物

- `survival_guide.pdf`：完整 PDF 成品，位于项目根目录。
- `website/dist/`：自动生成的静态网站，可直接本地预览，未来也可以交给 GitHub Pages 发布。

网站保留正文、图片、脚注、表格和主要层级，但舍弃封面、封底、纸张分页、页眉页脚等只适用于书本的排版。网页会把长章节拆成更便于浏览和搜索的专题；这种拆分只影响网站，不改变 LaTeX 原文的章节结构。

## 技术栈

### PDF

- LaTeX：正文与排版源文件
- XeLaTeX：支持中文字体的编译引擎
- latexmk：自动执行多轮编译并整理中间文件

### 网站

- Python 3 标准库：读取 LaTeX、转换 HTML、复制图片并执行构建检查
- HTML5：页面结构
- CSS3：响应式布局与视觉样式
- 原生 JavaScript：全文搜索、手机菜单、图片放大和返回顶部
- MathJax（CDN）：在浏览器中显示数学公式

网站没有后端、数据库、Node.js、npm 或前端框架。GitHub Pages 与 GitHub Actions 是计划中的发布方式，目前本地构建不依赖它们。

## 目录结构

```text
survival_guide/
├─ main.tex                         # PDF 唯一编译入口与全局设置
├─ .latexmkrc                       # XeLaTeX、输出名称和中间目录配置
├─ survival_guide.pdf               # PDF 成品
├─ content/                         # PDF 与网站共用的正文源文件
│  ├─ frontmatter.tex              # 前言、声明等前置内容
│  ├─ chapter-01-basic-information.tex
│  ├─ chapter-02-course-selection.tex
│  ├─ chapter-03-study-life.tex
│  ├─ chapter-04-student-organizations.tex
│  ├─ chapter-05-positive-mindset.tex
│  ├─ chapter-06-freshman-timeline.tex
│  ├─ chapter-07-daily-life.tex
│  └─ backmatter.tex               # 后记与结语
├─ assets/                          # LaTeX 与网站共用的全部图片
├─ styles/
│  └─ nexus.sty                     # PDF 章节、目录、页眉页脚和配色
├─ build/                           # PDF 编译中间文件
├─ scripts/
│  └─ build_website.py             # LaTeX → 静态网站构建器与审计
└─ website/
   ├─ templates/                    # 首页、栏目页、内容页 HTML 模板
   ├─ styles/main.css               # 网站全部基础样式
   ├─ scripts/main.js               # 网站交互与搜索逻辑
   └─ dist/                         # 自动生成的网站，不手改、不提交
```

## 编译 PDF

在项目根目录运行：

```powershell
latexmk main.tex
```

`.latexmkrc` 已配置 XeLaTeX。目录、日志等中间文件会进入 `build/`，成品输出为根目录的 `survival_guide.pdf`。`latexmk` 会自动完成目录、页码和交叉引用所需的多轮编译。

若没有安装 `latexmk`，可临时使用：

```powershell
xelatex -jobname=survival_guide main.tex
xelatex -jobname=survival_guide main.tex
```

## 生成与预览网站

生成静态网站：

```powershell
python scripts/build_website.py
```

生成结果在 `website/dist/`。构建器会同步复制正文图片、样式、脚本及当前 PDF，并检查缺图、未知 LaTeX 命令、转换数量差异和损坏的本地链接。成功后会生成 `website/dist/build-report.json`。

启动本地预览：

```powershell
python scripts/build_website.py --serve
```

浏览器打开 `http://127.0.0.1:8000/`，按 `Ctrl+C` 停止。修改源文件后需要重新运行构建命令，再刷新浏览器。

## 修改边界

### 修改正文或图片

正文以 `content/*.tex` 为准，图片放在 `assets/`。修改后分别重新运行 `latexmk main.tex` 和 `python scripts/build_website.py`，PDF 与网站都会采用新内容。

新增 LaTeX 章节时，还需在 `main.tex` 增加相应的 `\input{content/文件名}`。如果希望新章节在网站中成为独立专题，也要在 `scripts/build_website.py` 的页面配置中登记切分位置。

### 只修改网站结构或 UI

- 页面骨架：修改 `website/templates/`
- 颜色、字号、间距、响应式布局：修改 `website/styles/main.css`
- 搜索、菜单、图片交互：修改 `website/scripts/main.js`
- 栏目名称、专题切分、网页专用组织方式：修改 `scripts/build_website.py`

纯网站需求不应改动 `content/*.tex`。例如合并网页栏目、调整导航、隐藏某页目录，都应在构建器、模板或样式层处理。

### 不要直接修改生成物

不要手动编辑 `website/dist/`。该目录每次构建都会被清空并重新生成，而且已被 `.gitignore` 忽略。任何长期修改都应写回模板、CSS、JavaScript 或构建器。

## 协作建议

1. 开始工作前先确认自己所在分支和工作区状态，避免覆盖他人的未提交修改。
2. 正文作者编辑 `content/`；负责 UI 的同学优先编辑 `website/templates/`、`website/styles/` 和 `website/scripts/`。
3. 修改正文后同时检查 PDF 与网站；只改网站时至少重新构建并检查桌面端、手机端、导航和搜索。
4. 提交前查看 `website/dist/build-report.json`，确认状态为 `ok`，且缺图、未知命令、转换差异和损坏链接均为空。
5. `survival_guide.pdf` 是二进制成品，合并冲突难以人工处理。除非本次确实要更新 PDF，否则不要把它混入网站 UI 的提交。
6. 一次提交尽量只处理一个主题，并在提交说明中写清是“正文更新”“网站结构”还是“网站 UI”。

## 封面和封底

PDF 的封面和封底分别来自：

- `assets/cover-third-edition.png`
- `assets/封底.jpg`

替换设计时保持文件名不变，再运行 `latexmk main.tex`。网站不会展示这两张书本专用页面。

## GitHub Pages 自动发布

仓库中的 `.github/workflows/deploy-pages.yml` 会在 `master` 分支有新提交时自动运行，也可以在 GitHub 的 Actions 页面手动运行。它会读取最新正文，执行网站构建，将 `website/dist/` 上传为 Pages artifact，再发布到 GitHub Pages。

首次启用时，在仓库打开 `Settings → Pages`，把 `Build and deployment` 的来源设置为 `GitHub Actions`。之后只要把需要发布的提交推送到 `master`，等待 Actions 中的 `Build and deploy website` 变成绿色，网站就会更新。`website/dist/` 是构建产物，不需要手动编辑或提交。
