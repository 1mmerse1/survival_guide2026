# 北京大学工学院新生生存手册 2026

这是《北京大学工学院新生生存手册》的 LaTeX 源码仓库。

## 文件说明

- `survival-guide-2026.tex`：手册正文与封面入口，通常只需编辑这个文件。
- `nexus.sty`：全书版式主题，控制章节标题、目录、页眉页脚和配色；除非要修改整体视觉风格，否则无需调整。
- `原图资源/`：封面及正文使用的原始图片。
- `survival-guide-2026.pdf`：最新编译版本，可直接下载阅读。

## 开始编辑

1. 安装 [TeX Live](https://www.tug.org/texlive/)
2. 使用 VS Code、TeXworks 或其他纯文本编辑器打开 `survival-guide-2026.tex`。
3. 确保文件以 UTF-8 编码保存。
4. 在仓库目录打开 PowerShell 或终端，执行：

```powershell
latexmk survival-guide-2026.tex
```

编译完成后，PDF 位于：

```text
survival-guide-2026.pdf
```

首次编译时间可能稍长；后续再次运行同一命令即可增量更新。
