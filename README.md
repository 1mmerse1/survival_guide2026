# 北京大学工学院新生生存手册

这是《北京大学工学院新生生存手册》的 LaTeX 源码。项目以 `main.tex` 为唯一入口，编译时会把前置内容、七章正文和后置内容组合成一份完整 PDF。

## 项目结构

```text
survival_guide/
├─ main.tex                         # 唯一编译入口和全局设置
├─ .latexmkrc                       # 编译方式和输出位置配置
├─ survival_guide.pdf               # 完整成品
├─ content/                         # 手册的全部内容
│  ├─ frontmatter.tex              # 封面、各版前言、声明
│  ├─ chapter-01-basic-information.tex
│  ├─ chapter-02-course-selection.tex
│  ├─ chapter-03-study-life.tex
│  ├─ chapter-04-student-organizations.tex
│  ├─ chapter-05-positive-mindset.tex
│  ├─ chapter-06-freshman-timeline.tex
│  ├─ chapter-07-daily-life.tex
│  └─ backmatter.tex               # 后记、结语
├─ styles/
│  └─ nexus.sty                     # 章节、目录、页眉页脚和配色样式
├─ assets/                          # 正文使用的全部图片
└─ build/                           # 编译产生的中间文件
```

## 编译完整手册

项目使用 XeLaTeX。在项目根目录运行：

```powershell
latexmk main.tex
```

项目根目录中的 `.latexmkrc` 已经配置好 XeLaTeX、文件名和输出位置：目录、日志等中间文件会进入 `build/`，最终成品会输出为根目录下的 `survival_guide.pdf`。`latexmk` 会自动通过多轮编译完成目录、页码和交叉引用，不需要分别编译各章。

如果没有安装 `latexmk`，可以使用下面的命令，但需要自行整理生成的中间文件：

```powershell
xelatex -jobname=survival_guide main.tex
xelatex -jobname=survival_guide main.tex
```

## 编辑内容

- 修改某章：编辑 `content/` 中对应的章节文件。
- 修改封面、前言或声明：编辑 `content/frontmatter.tex`。
- 修改后记或结语：编辑 `content/backmatter.tex`。
- 调整整本手册的宏包或章节顺序：编辑 `main.tex`。
- 调整章节标题、目录或页眉页脚样式：编辑 `styles/nexus.sty`。
- 添加图片：直接放入 `assets/`，并在正文中使用相对项目根目录的路径引用。

新增一章时，在 `content/` 中新建 `.tex` 文件，再在 `main.tex` 的相应位置增加一行：

```tex
\input{content/文件名}
```

## 封面和封底

成品的封面和封底分别来自：

- `assets/cover-third-edition.png`
- `assets/封底.jpg`

这两张图片会在 PDF 中铺满整页。替换设计时保持文件名不变，再重新运行 `latexmk main.tex` 即可。
