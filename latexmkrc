# XeLaTeX 构建配置：辅助文件集中到 build，最终 PDF 放在仓库根目录。
$pdf_mode = 5;
$aux_dir = 'build';
$out_dir = '.';
$xelatex = 'xelatex -synctex=1 -interaction=nonstopmode -file-line-error %O %S';
$max_repeat = 5;
