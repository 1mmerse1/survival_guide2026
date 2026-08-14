#!/usr/bin/env python3
"""Build the static handbook website from the LaTeX source files.

This converter intentionally supports the LaTeX constructs used by this
project. It keeps the handbook content in one place while allowing the PDF and
website to use different presentation layers.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from dataclasses import dataclass
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
ASSETS_DIR = ROOT / "assets"
WEBSITE_DIR = ROOT / "website"
DIST_DIR = WEBSITE_DIR / "dist"


@dataclass(frozen=True)
class PageSpec:
    source: str
    slug: str
    nav_title: str
    description: str
    category: str
    start: str | None = None
    end: str | None = None
    kind: str = "article"


@dataclass(frozen=True)
class CategorySpec:
    slug: str
    title: str
    description: str
    eyebrow: str
    articles: tuple[str, ...]
    direct: bool = False


PAGES = [
    PageSpec("chapter-01-basic-information.tex", "basic-information", "基本情况", "小而精的北大工科、招生人数与学生构成", "basic-information", None, r"\section{细谈本科专业}"),

    PageSpec("chapter-01-basic-information.tex", "major-theoretical-mechanics", "理论与应用力学", "专业学习、未来方向与周培源班经验", "majors", r"\subsection{理论与应用力学}", r"\subsection{工程与科学计算}"),
    PageSpec("chapter-01-basic-information.tex", "major-scientific-computing", "工程与科学计算", "数学、力学与计算机交叉的培养体验", "majors", r"\subsection{工程与科学计算}", r"\subsection{能源与环境系统工程}"),
    PageSpec("chapter-01-basic-information.tex", "major-energy-environment", "能源与环境系统工程", "能源专业学习内容、专业未来与个人体会", "majors", r"\subsection{能源与环境系统工程}", r"\subsection{航空航天工程}"),
    PageSpec("chapter-01-basic-information.tex", "major-aerospace", "航空航天工程", "航空航天专业课程、方向与学习体验", "majors", r"\subsection{航空航天工程}", r"\subsection{生物医学工程}"),
    PageSpec("chapter-01-basic-information.tex", "major-biomedical-engineering", "生物医学工程", "生医工研究方向、课程与升学经验", "majors", r"\subsection{生物医学工程}", r"\subsection{材料科学与工程}"),
    PageSpec("chapter-01-basic-information.tex", "major-materials-science", "材料科学与工程", "材料专业方向、课程与发展选择", "majors", r"\subsection{材料科学与工程}", r"\subsection{机器人工程}"),
    PageSpec("chapter-01-basic-information.tex", "major-robotics", "机器人工程", "机器人专业课程、研究方向与学习建议", "majors", r"\subsection{机器人工程}", r"\subsection{环境科学与工程}"),
    PageSpec("chapter-01-basic-information.tex", "major-environmental-science-engineering", "环境科学与工程", "环境化学及环境科学与工程专业经验分享", "majors", r"\subsection{环境科学与工程}", r"\textbf{环境科学}"),
    PageSpec("chapter-01-basic-information.tex", "major-environmental-science", "环境科学", "环境科学专业课程与学习体验", "majors", r"\textbf{环境科学}", r"\textbf{环境工程}"),
    PageSpec("chapter-01-basic-information.tex", "major-environmental-engineering", "环境工程", "环境工程专业课程与发展方向", "majors", r"\textbf{环境工程}", r"\textbf{环境管理}"),
    PageSpec("chapter-01-basic-information.tex", "major-environmental-management", "环境管理", "环境管理专业经验分享", "majors", r"\textbf{环境管理}", r"\textbf{环境健康}"),
    PageSpec("chapter-01-basic-information.tex", "major-environmental-health", "环境健康", "环境健康研究方向与课程介绍", "majors", r"\textbf{环境健康}", r"\textbf{环境大数据}"),
    PageSpec("chapter-01-basic-information.tex", "major-environmental-data", "环境大数据", "环境大数据课程、能力与发展方向", "majors", r"\textbf{环境大数据}"),

    PageSpec("chapter-02-course-selection.tex", "course-requirements", "课程分类与毕业要求", "了解课程类别、学分结构与毕业要求", "course-selection", r"\section{课程分类}", r"\section{选课网基本操作}"),
    PageSpec("chapter-02-course-selection.tex", "course-system", "选课网基本操作", "从培养方案到投点、退课的完整选课流程", "course-selection", r"\section{选课网基本操作}", r"\section{选课信息来源}"),
    PageSpec("chapter-02-course-selection.tex", "course-tools", "选课信息来源", "课程测评、信息查询与选课辅助资源", "course-selection", r"\section{选课信息来源}", r"\section{特殊选课模式}"),
    PageSpec("chapter-02-course-selection.tex", "special-course-selection", "特殊选课模式", "跨院系、课程替代、冲突选课与中期退课", "course-selection", r"\section{特殊选课模式}"),

    PageSpec("chapter-03-study-life.tex", "training-program", "工学院培养方案", "理解培养方案及其使用方式", "study-planning", r"\section{工学院培养方案}", r"\section{基础课程}"),
    PageSpec("chapter-03-study-life.tex", "foundation-courses", "基础课程", "数学、物理、化学和生物课程建议", "study-planning", r"\section{基础课程}", r"\section{公共课程}"),
    PageSpec("chapter-03-study-life.tex", "public-courses", "公共课程", "计算机、思政、英语、通选与外校课程", "study-planning", r"\section{公共课程}", r"\section{转入/转出工学院}"),
    PageSpec("chapter-03-study-life.tex", "major-transfer", "转入与转出工学院", "转专业政策、准备方法与真实经验", "study-planning", r"\section{转入/转出工学院}", r"\section[双专业/辅修建议]"),
    PageSpec("chapter-03-study-life.tex", "double-major-minor", "双专业与辅修", "申请、选课、学分与经验分享", "study-planning", r"\section[双专业/辅修建议]", r"\section{学业导师}"),
    PageSpec("chapter-03-study-life.tex", "academic-advisor", "学业导师", "学业导师制度与沟通建议", "study-planning", r"\section{学业导师}", r"\section{计算机与AI工具使用指南}"),
    PageSpec("chapter-03-study-life.tex", "digital-tools", "计算机与 AI 工具", "计算机基础资源、AI 工具原理、使用方法与注意事项", "study-planning", r"\section{计算机与AI工具使用指南}", r"\section{善用搜索}"),
    PageSpec("chapter-03-study-life.tex", "search-skills", "善用搜索", "树洞、课程测评网站及其他信息检索方法", "study-planning", r"\section{善用搜索}"),

    PageSpec("chapter-04-student-organizations.tex", "student-affairs", "学工简介", "学院学生工作的内容与信息渠道", "campus-engagement", r"\section{学工简介}", r"\section{学工组织}"),
    PageSpec("chapter-04-student-organizations.tex", "student-union-league", "学工组织", "团委、学生会及其他学生组织的工作内容", "campus-engagement", r"\section{学工组织}", r"\section{社团简介}"),
    PageSpec("chapter-04-student-organizations.tex", "student-clubs", "社团简介", "工学院社团及参与建议", "campus-engagement", r"\section{社团简介}", r"\section{入党相关}"),
    PageSpec("chapter-04-student-organizations.tex", "party-membership", "入党相关", "入党流程与相关信息", "campus-engagement", r"\section{入党相关}", r"\section{其他学生组织与课外活动}"),
    PageSpec("chapter-04-student-organizations.tex", "extracurricular-activities", "其他学生组织与课外活动", "志愿服务、学校活动与参与建议", "campus-engagement", r"\section{其他学生组织与课外活动}"),

    PageSpec("chapter-05-positive-mindset.tex", "freshman-challenges", "新生面临的核心问题", "适应大学生活时常见的困惑", "wellbeing-life", r"\section{新生面临的核心问题}", r"\section{如何利用好资源寻求心理帮助}"),
    PageSpec("chapter-05-positive-mindset.tex", "mental-health-resources", "如何利用资源寻求心理帮助", "校内心理支持资源与求助建议", "wellbeing-life", r"\section{如何利用好资源寻求心理帮助}", r"\section{常见问题荟萃}"),
    PageSpec("chapter-05-positive-mindset.tex", "common-questions", "常见问题荟萃", "学术、生活与人际问题的经验建议", "wellbeing-life", r"\section{常见问题荟萃}"),

    PageSpec("chapter-06-freshman-timeline.tex", "freshman-timeline", "大一时间线", "按时间浏览大一学年的重要节点和校园事件", "freshman-timeline", None, None, "timeline"),

    PageSpec("chapter-07-daily-life.tex", "engineering-campus", "工院人根据地", "工学大院空间与日常活动地点", "wellbeing-life", r"\section{工院人根据地}", r"\section{信息渠道}"),
    PageSpec("chapter-07-daily-life.tex", "information-resources", "信息渠道与常用工具", "网站、公众号、软件和校内电话", "wellbeing-life", r"\section{信息渠道}"),

    PageSpec("frontmatter.tex", "about-handbook", "关于这本手册", "编写缘起、各版前言与使用声明", "about", r"\fullbleedpage{assets/cover-third-edition.png}", None, "frontmatter"),
    PageSpec("backmatter.tex", "afterword", "后记与结语", "致谢、反馈方式与写给读者的话", "about", r"\chapter*{后记}", None, "backmatter"),
]


CATEGORIES = [
    CategorySpec("basic-information", "基本情况", "先从整体上认识北大工科、工学院的规模和学生构成。", "认识工院", ("basic-information",), True),
    CategorySpec("majors", "专业介绍", "按专业浏览学长学姐访谈，了解课程、方向、体验与未来选择。", "专业与方向", tuple(page.slug for page in PAGES if page.category == "majors")),
    CategorySpec("course-selection", "选课指导", "从毕业要求到选课操作，按实际问题查找信息。", "课程与选课", tuple(page.slug for page in PAGES if page.category == "course-selection")),
    CategorySpec("study-planning", "学习规划", "培养方案、基础课程、转专业、数字工具和信息检索等专题。", "学业发展", tuple(page.slug for page in PAGES if page.category == "study-planning")),
    CategorySpec("freshman-timeline", "大一时间线", "按学期和时间节点浏览新生第一年的重要事件。", "全年节奏", ("freshman-timeline",), True),
    CategorySpec("campus-engagement", "校园参与", "了解学生工作、学生组织、社团和课外活动。", "组织与活动", tuple(page.slug for page in PAGES if page.category == "campus-engagement")),
    CategorySpec("wellbeing-life", "身心与日常生活", "从适应与心理支持，到校园空间、信息渠道和常用工具。", "校园生活", tuple(page.slug for page in PAGES if page.category == "wellbeing-life")),
    CategorySpec("about", "关于手册", "阅读前言、声明、后记与结语。", "项目说明", tuple(page.slug for page in PAGES if page.category == "about")),
]


def strip_comments(source: str) -> str:
    cleaned: list[str] = []
    for line in source.splitlines():
        index = 0
        while True:
            pos = line.find("%", index)
            if pos < 0:
                break
            slash_count = 0
            cursor = pos - 1
            while cursor >= 0 and line[cursor] == "\\":
                slash_count += 1
                cursor -= 1
            if slash_count % 2 == 0:
                line = line[:pos]
                break
            index = pos + 1
        cleaned.append(line.rstrip())
    return "\n".join(cleaned)


def extract_braced(text: str, start: int) -> tuple[str, int]:
    """Return braced content and the index immediately after the group."""
    if start >= len(text) or text[start] != "{":
        return "", start
    depth = 1
    cursor = start + 1
    content_start = cursor
    while cursor < len(text):
        if text[cursor] == "\\":
            cursor += 2
            continue
        if text[cursor] == "{":
            depth += 1
        elif text[cursor] == "}":
            depth -= 1
            if depth == 0:
                return text[content_start:cursor], cursor + 1
        cursor += 1
    return text[content_start:], len(text)


def extract_optional(text: str, start: int) -> tuple[str, int]:
    if start >= len(text) or text[start] != "[":
        return "", start
    depth = 1
    cursor = start + 1
    while cursor < len(text):
        if text[cursor] == "[":
            depth += 1
        elif text[cursor] == "]":
            depth -= 1
            if depth == 0:
                return text[start + 1:cursor], cursor + 1
        cursor += 1
    return text[start + 1:], len(text)


def plain_text(fragment: str) -> str:
    fragment = re.sub(r"<script[\s\S]*?</script>", "", fragment, flags=re.I)
    fragment = re.sub(r"<style[\s\S]*?</style>", "", fragment, flags=re.I)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(fragment)).strip()


class LatexPageConverter:
    STRUCTURAL_COMMANDS = {
        "frontmatter", "backmatter", "mainmatter", "tableofcontents", "newpage",
        "null", "clearpage", "centering", "noindent", "pagestyle", "renewcommand",
    }
    SPACING_COMMANDS = {"vspace", "hspace", "quad", "qquad", "newline", "linebreak"}

    def __init__(self, spec: PageSpec):
        self.spec = spec
        self.footnotes: list[str] = []
        self.headings: list[dict[str, object]] = []
        self.unknown_commands: set[str] = set()
        self.image_references: list[str] = []
        self.figure_count = 0
        self.list_count = 0
        self.table_count = 0
        self.timeline_event_count = 0

    def convert(self, source: str) -> str:
        source = strip_comments(source)
        if self.spec.kind == "frontmatter":
            # The first 90 lines construct a PDF-only cover. The web edition
            # begins at the actual written content.
            marker = r"\chapter*{第三版前言}"
            position = source.find(marker)
            if position < 0:
                raise ValueError("无法在 frontmatter.tex 中找到“第三版前言”")
            source = source[position:]
        source = re.sub(r"\\tableofcontents\b", "", source)
        source = re.sub(r"\\(?:frontmatter|backmatter|mainmatter|newpage|null|clearpage)\b", "", source)
        source = re.sub(r"\\fullbleedpage\{[^{}]+\}", "", source)
        return self.convert_blocks(source)

    def convert_blocks(self, source: str) -> str:
        lines = source.splitlines()
        output: list[str] = []
        paragraph: list[str] = []
        index = 0

        def flush_paragraph() -> None:
            if not paragraph:
                return
            raw = " ".join(part.strip() for part in paragraph if part.strip())
            paragraph.clear()
            raw = re.sub(r"\\vspace\s*\{[^{}]*\}", "", raw).strip()
            if raw:
                output.append(f"<p>{self.inline(raw)}</p>")

        while index < len(lines):
            line = lines[index].strip()
            if not line:
                flush_paragraph()
                index += 1
                continue

            heading = self.parse_heading(line)
            if heading:
                flush_paragraph()
                command, title, consumed = heading
                level = {"chapter": 1, "section": 2, "subsection": 3, "subsubsection": 4}[command]
                heading_id = f"section-{len(self.headings) + 1}"
                rendered_title = self.inline(title)
                self.headings.append({"level": level, "title": plain_text(rendered_title), "id": heading_id})
                output.append(f'<h{level} id="{heading_id}">{rendered_title}<a class="heading-anchor" href="#{heading_id}" aria-label="链接到本节">#</a></h{level}>')
                remainder = line[consumed:].strip()
                if remainder:
                    paragraph.append(remainder)
                index += 1
                continue

            if line.startswith(r"\begin{figure}"):
                flush_paragraph()
                block, index = self.collect_environment(lines, index, "figure")
                output.append(self.render_figure(block))
                continue

            if line.startswith(r"\begin{itemize}") or line.startswith(r"\begin{enumerate}"):
                flush_paragraph()
                environment = "itemize" if "itemize" in line else "enumerate"
                block, index = self.collect_environment(lines, index, environment)
                output.append(self.render_list(block, ordered=environment == "enumerate"))
                continue

            if line.startswith(r"\begin{table}"):
                flush_paragraph()
                block, index = self.collect_environment(lines, index, "table")
                output.append(self.render_table(block))
                continue

            if line == r"\[":
                flush_paragraph()
                block: list[str] = []
                index += 1
                while index < len(lines) and lines[index].strip() != r"\]":
                    block.append(lines[index])
                    index += 1
                index += 1
                joined = "\n".join(block)
                if r"\begin{matrix}" in joined:
                    output.append(self.render_matrix(joined))
                else:
                    output.append(f'<div class="math-display">\\[{html.escape(joined)}\\]</div>')
                continue

            if line.startswith(r"\begin{flushright}"):
                flush_paragraph()
                block, index = self.collect_environment(lines, index, "flushright")
                inner = re.sub(r"^\\begin\{flushright\}", "", block.strip())
                inner = re.sub(r"\\end\{flushright\}$", "", inner.strip())
                output.append(f'<div class="signature">{self.inline(inner)}</div>')
                continue

            if line.startswith(r"\begin{center}"):
                flush_paragraph()
                block, index = self.collect_environment(lines, index, "center")
                if r"\begin{tikzpicture}" in block:
                    output.append(self.render_timeline(block))
                else:
                    inner = re.sub(r"^\\begin\{center\}", "", block.strip())
                    inner = re.sub(r"\\end\{center\}$", "", inner.strip())
                    output.append(f'<div class="centered-content">{self.inline(inner)}</div>')
                continue

            if line.startswith(r"\begin{quote}"):
                flush_paragraph()
                block, index = self.collect_environment(lines, index, "quote")
                inner = re.sub(r"^\\begin\{quote\}", "", block.strip())
                inner = re.sub(r"\\end\{quote\}$", "", inner.strip())
                output.append(f'<blockquote>{self.inline(inner)}</blockquote>')
                continue

            if re.fullmatch(r"\\(?:vspace|hspace)\s*\{[^{}]*\}", line):
                flush_paragraph()
                index += 1
                continue

            if line.startswith(r"\renewcommand") or line in {r"\newpage", r"\null"}:
                flush_paragraph()
                index += 1
                continue

            paragraph.append(line)
            index += 1

        flush_paragraph()
        if self.footnotes:
            notes = "".join(
                f'<li id="footnote-{number}">{note} <a class="footnote-back" href="#footnote-ref-{number}" aria-label="返回正文">↩</a></li>'
                for number, note in enumerate(self.footnotes, 1)
            )
            output.append(f'<section class="footnotes" aria-labelledby="footnotes-title"><h2 id="footnotes-title">脚注</h2><ol>{notes}</ol></section>')
        return "\n".join(output)

    def parse_heading(self, line: str) -> tuple[str, str, int] | None:
        match = re.match(r"\\(chapter|section|subsection|subsubsection)(\*)?", line)
        if not match:
            return None
        cursor = match.end()
        if cursor < len(line) and line[cursor] == "[":
            _, cursor = extract_optional(line, cursor)
        while cursor < len(line) and line[cursor].isspace():
            cursor += 1
        if cursor >= len(line) or line[cursor] != "{":
            return None
        title, end = extract_braced(line, cursor)
        return match.group(1), title, end

    @staticmethod
    def collect_environment(lines: list[str], start: int, environment: str) -> tuple[str, int]:
        depth = 0
        block: list[str] = []
        index = start
        begin = rf"\begin{{{environment}}}"
        end = rf"\end{{{environment}}}"
        while index < len(lines):
            current = lines[index]
            depth += current.count(begin)
            depth -= current.count(end)
            block.append(current)
            index += 1
            if depth <= 0:
                break
        return "\n".join(block), index

    def render_figure(self, block: str) -> str:
        image_match = re.search(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", block)
        if not image_match:
            self.unknown_commands.add("figure-without-image")
            return ""
        path = image_match.group(1).replace("\\", "/")
        caption_match = re.search(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}", block, flags=re.S)
        caption = self.inline(caption_match.group(1).strip()) if caption_match else ""
        self.image_references.append(path)
        self.figure_count += 1
        alt = plain_text(caption) or Path(path).stem
        caption_html = f"<figcaption>{caption}</figcaption>" if caption else ""
        return (
            f'<figure class="content-figure">'
            f'<button class="image-button" type="button" data-image="{html.escape(path, quote=True)}" aria-label="放大图片：{html.escape(alt, quote=True)}">'
            f'<img src="{html.escape(path, quote=True)}" alt="{html.escape(alt, quote=True)}" loading="lazy">'
            f'</button>{caption_html}</figure>'
        )

    def render_list(self, block: str, ordered: bool) -> str:
        block = re.sub(r"^\\begin\{(?:itemize|enumerate)\}(?:\[[^]]*\])?", "", block.strip())
        block = re.sub(r"\\end\{(?:itemize|enumerate)\}$", "", block.strip())
        parts = re.split(r"\\item(?:\s*\[[^]]*\])?", block)
        items = [part.strip() for part in parts[1:] if part.strip()]
        tag = "ol" if ordered else "ul"
        self.list_count += 1
        return f'<{tag} class="content-list">' + "".join(f"<li>{self.inline(item)}</li>" for item in items) + f"</{tag}>"

    def render_table(self, block: str) -> str:
        marker = r"\begin{tabular}"
        position = block.find(marker)
        if position < 0:
            self.unknown_commands.add("table-without-tabular")
            return ""
        cursor = position + len(marker)
        while cursor < len(block) and block[cursor].isspace():
            cursor += 1
        if cursor >= len(block) or block[cursor] != "{":
            self.unknown_commands.add("table-without-columns")
            return ""
        _, body_start = extract_braced(block, cursor)
        body_end = block.find(r"\end{tabular}", body_start)
        if body_end < 0:
            self.unknown_commands.add("table-without-tabular-end")
            return ""
        return self.render_rows(block[body_start:body_end])

    def render_matrix(self, block: str) -> str:
        matrix = re.search(r"\\begin\{matrix\}(.*?)\\end\{matrix\}", block, flags=re.S)
        if not matrix:
            return f'<div class="math-display">\\[{html.escape(block)}\\]</div>'
        return self.render_rows(matrix.group(1))

    def render_timeline(self, block: str) -> str:
        """Turn the PDF-only TikZ timeline into semantic website cards."""
        nodes: list[str] = []
        cursor = 0
        while True:
            position = block.find(r"\node", cursor)
            if position < 0:
                break
            brace = block.find("{", position)
            if brace < 0:
                break
            content, cursor = extract_braced(block, brace)
            nodes.append(content.strip())
        if len(nodes) % 2:
            self.unknown_commands.add("timeline-node-pair")

        events: list[str] = []
        for index in range(0, len(nodes) - 1, 2):
            date = self.inline(nodes[index])
            detail = re.sub(r"\\\\\[[^]]*\]", " ", nodes[index + 1]).strip()
            title_marker = detail.find(r"\textbf")
            title = "校园事件"
            description = detail
            if title_marker >= 0:
                brace = detail.find("{", title_marker)
                if brace >= 0:
                    title, end = extract_braced(detail, brace)
                    description = detail[end:]
            description = re.sub(r"\\(?:footnotesize|small|bfseries)\b", "", description)
            description = re.sub(r"\\color\{[^{}]*\}", "", description).strip(" {};\t")

            self.timeline_event_count += 1
            heading_id = f"timeline-event-{self.timeline_event_count}"
            rendered_title = self.inline(title)
            self.headings.append({
                "level": 3,
                "title": plain_text(rendered_title),
                "id": heading_id,
            })
            events.append(
                f'<li class="timeline-event"><time>{date}</time><div>'
                f'<h3 id="{heading_id}">{rendered_title}<a class="heading-anchor" href="#{heading_id}" aria-label="链接到本项">#</a></h3>'
                f'<p>{self.inline(description)}</p></div></li>'
            )
        return '<ol class="web-timeline">' + "".join(events) + "</ol>"

    def render_rows(self, body: str) -> str:
        body = body.replace(r"\hline", "")
        rows = [row.strip() for row in re.split(r"\\\\", body) if row.strip()]
        rendered_rows: list[str] = []
        for row_index, row in enumerate(rows):
            cells = [cell.strip() for cell in row.split("&")]
            cell_tag = "th" if row_index == 0 else "td"
            rendered_rows.append("<tr>" + "".join(f"<{cell_tag}>{self.inline(cell)}</{cell_tag}>" for cell in cells) + "</tr>")
        self.table_count += 1
        return '<div class="table-scroll"><table>' + "".join(rendered_rows) + "</table></div>"

    def inline(self, text: str) -> str:
        output: list[str] = []
        cursor = 0
        while cursor < len(text):
            char = text[cursor]
            if char == "$":
                end = cursor + 1
                while end < len(text):
                    if text[end] == "$" and text[end - 1] != "\\":
                        break
                    end += 1
                if end < len(text):
                    formula = text[cursor + 1:end]
                    output.append(f'<span class="math">\\({html.escape(formula)}\\)</span>')
                    cursor = end + 1
                    continue
            if char == "\\":
                if text.startswith(r"\\", cursor):
                    output.append("<br>")
                    cursor += 2
                    continue
                if cursor + 1 < len(text) and text[cursor + 1].isspace():
                    output.append(" ")
                    cursor += 2
                    continue
                command_match = re.match(r"\\([A-Za-z@]+|[%&#_$])", text[cursor:])
                if command_match:
                    command = command_match.group(1)
                    cursor += command_match.end()
                    while cursor < len(text) and text[cursor].isspace():
                        cursor += 1
                    if command in {"%", "&", "#", "_", "$"}:
                        output.append(html.escape(command))
                        continue
                    if command in {"textbf", "bfseries"}:
                        if cursor < len(text) and text[cursor] == "{":
                            content, cursor = extract_braced(text, cursor)
                            output.append(f"<strong>{self.inline(content)}</strong>")
                        continue
                    if command in {"emph", "textit"}:
                        if cursor < len(text) and text[cursor] == "{":
                            content, cursor = extract_braced(text, cursor)
                            output.append(f"<em>{self.inline(content)}</em>")
                        continue
                    if command == "underline":
                        if cursor < len(text) and text[cursor] == "{":
                            content, cursor = extract_braced(text, cursor)
                            output.append(f"<u>{self.inline(content)}</u>")
                        continue
                    if command == "footnote":
                        if cursor < len(text) and text[cursor] == "{":
                            content, cursor = extract_braced(text, cursor)
                            number = len(self.footnotes) + 1
                            rendered = self.inline(content)
                            self.footnotes.append(rendered)
                            output.append(f'<sup class="footnote-ref" id="footnote-ref-{number}"><a href="#footnote-{number}" aria-label="脚注 {number}">{number}</a></sup>')
                        continue
                    if command == "href":
                        if cursor < len(text) and text[cursor] == "{":
                            url, cursor = extract_braced(text, cursor)
                            label = url
                            if cursor < len(text) and text[cursor] == "{":
                                label, cursor = extract_braced(text, cursor)
                            output.append(f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{self.inline(label)}</a>')
                        continue
                    if command == "url":
                        if cursor < len(text) and text[cursor] == "{":
                            url, cursor = extract_braced(text, cursor)
                            output.append(f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(url)}</a>')
                        continue
                    if command in {"text", "mathrm", "textrm"}:
                        if cursor < len(text) and text[cursor] == "{":
                            content, cursor = extract_braced(text, cursor)
                            output.append(self.inline(content))
                        continue
                    if command == "textcolor":
                        if cursor < len(text) and text[cursor] == "{":
                            _, cursor = extract_braced(text, cursor)
                        if cursor < len(text) and text[cursor] == "{":
                            content, cursor = extract_braced(text, cursor)
                            output.append(self.inline(content))
                        continue
                    if command in {"vspace", "hspace"}:
                        if cursor < len(text) and text[cursor] == "{":
                            _, cursor = extract_braced(text, cursor)
                        output.append(" ")
                        continue
                    if command in {"quad", "qquad"}:
                        output.append("　")
                        continue
                    if command == "enspace":
                        output.append(" ")
                        continue
                    if command in {"newline", "linebreak"}:
                        output.append("<br>")
                        continue
                    if command == "LaTeX":
                        output.append("LaTeX")
                        continue
                    if command in {"label", "renewcommand"}:
                        if cursor < len(text) and text[cursor] == "{":
                            _, cursor = extract_braced(text, cursor)
                        continue
                    if command == "color":
                        if cursor < len(text) and text[cursor] == "{":
                            _, cursor = extract_braced(text, cursor)
                        continue
                    if command in {"noindent", "centering", "selectfont", "footnotesize", "small"}:
                        continue
                    self.unknown_commands.add(command)
                    if cursor < len(text) and text[cursor] == "{":
                        content, cursor = extract_braced(text, cursor)
                        output.append(self.inline(content))
                    else:
                        output.append(html.escape("\\" + command))
                    continue
            if char in "{}":
                cursor += 1
                continue
            next_special = len(text)
            for special in ("$", "\\", "{", "}"):
                found = text.find(special, cursor + 1)
                if found >= 0:
                    next_special = min(next_special, found)
            output.append(self.linkify(text[cursor:next_special]))
            cursor = next_special
        return "".join(output)

    @staticmethod
    def linkify(text: str) -> str:
        pattern = re.compile(r"https?://[^\s<>，。；）]+|www\.[A-Za-z0-9./?&=_-]+")
        output: list[str] = []
        cursor = 0
        for match in pattern.finditer(text):
            output.append(html.escape(text[cursor:match.start()]))
            label = match.group(0)
            href = label if label.startswith("http") else "https://" + label
            output.append(f'<a href="{html.escape(href, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(label)}</a>')
            cursor = match.end()
        output.append(html.escape(text[cursor:]))
        return "".join(output)


def load_template(name: str) -> str:
    return (WEBSITE_DIR / "templates" / name).read_text(encoding="utf-8")


PAGE_BY_SLUG = {page.slug: page for page in PAGES}
CATEGORY_BY_SLUG = {category.slug: category for category in CATEGORIES}


def category_url(category: CategorySpec) -> str:
    return f"{category.articles[0]}.html" if category.direct else f"{category.slug}.html"


def render_navigation(active_category: str = "") -> str:
    links = ['<a class="nav-home" href="index.html">首页</a>']
    for category in CATEGORIES:
        active = ' aria-current="page"' if category.slug == active_category else ""
        links.append(f'<a href="{category_url(category)}"{active}>{html.escape(category.title)}</a>')
    return "\n".join(links)


def render_toc(headings: Iterable[dict[str, object]]) -> str:
    items = []
    for heading in headings:
        level = int(heading["level"])
        items.append(
            f'<li class="toc-level-{level}"><a href="#{heading["id"]}">{html.escape(str(heading["title"]))}</a></li>'
        )
    return '<ol class="toc-list">' + "".join(items) + "</ol>"


def replace_tokens(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def slice_source(source: str, start: str | None, end: str | None) -> str:
    lines = source.splitlines()
    start_index = 0
    if start:
        matches = [index for index, line in enumerate(lines) if line.strip().startswith(start)]
        if not matches:
            raise ValueError(f"找不到内容起点：{start}")
        start_index = matches[0]
    end_index = len(lines)
    if end:
        matches = [
            index for index, line in enumerate(lines[start_index + 1:], start_index + 1)
            if line.strip().startswith(end)
        ]
        if not matches:
            raise ValueError(f"找不到内容终点：{end}")
        end_index = matches[0]
    return "\n".join(lines[start_index:end_index]).strip() + "\n"


def prepare_source_for_spec(source: str, spec: PageSpec) -> str:
    """Add a web-only structural heading where the PDF uses bold text."""
    if not spec.start or not spec.start.startswith(r"\textbf{"):
        return source
    lines = source.splitlines()
    if lines and lines[0].strip().startswith(spec.start):
        lines[0] = rf"\subsection{{{spec.nav_title}}}"
    return "\n".join(lines).strip() + "\n"


def normalize_heading_levels(source: str) -> str:
    heading_pattern = re.compile(r"(?m)^\\(chapter|section|subsection|subsubsection)(?=\*|\[|\{)")
    first = heading_pattern.search(source)
    if not first:
        return source
    ranks = ["chapter", "section", "subsection", "subsubsection"]
    shift = ranks.index(first.group(1))
    if shift == 0:
        return source

    def promote(match: re.Match[str]) -> str:
        current = ranks.index(match.group(1))
        return "\\" + ranks[max(0, current - shift)]

    return heading_pattern.sub(promote, source)


def render_cards(article_slugs: Iterable[str], compact: bool = False) -> str:
    class_name = "topic-card compact" if compact else "topic-card"
    return "".join(
        f'<a class="{class_name}" href="{page.slug}.html">'
        f'<span class="topic-kicker">专题</span>'
        f'<h2>{html.escape(page.nav_title)}</h2>'
        f'<p>{html.escape(page.description)}</p>'
        f'<span class="topic-arrow">查看内容 <span aria-hidden="true">→</span></span></a>'
        for slug in article_slugs
        for page in [PAGE_BY_SLUG[slug]]
    )


def search_entries_for_article(spec: PageSpec, article: str) -> list[dict[str, str]]:
    category = CATEGORY_BY_SLUG[spec.category]
    entries = [{
        "title": spec.nav_title,
        "breadcrumb": f"{category.title} › {spec.nav_title}",
        "description": spec.description,
        "url": f"{spec.slug}.html",
        "text": plain_text(article),
    }]
    heading_pattern = re.compile(r'<h([1-4]) id="([^"]+)">(.*?)</h\1>', flags=re.S)
    matches = list(heading_pattern.finditer(article))
    for index, match in enumerate(matches):
        level = int(match.group(1))
        if level == 1:
            continue
        end = len(article)
        for following in matches[index + 1:]:
            if int(following.group(1)) <= level:
                end = following.start()
                break
        section_text = plain_text(article[match.end():end])
        if len(section_text) < 8:
            continue
        title = plain_text(match.group(3).replace('<a class="heading-anchor" href="#' + match.group(2) + '" aria-label="链接到本节">#</a>', ''))
        entries.append({
            "title": title,
            "breadcrumb": f"{category.title} › {spec.nav_title} › {title}",
            "description": spec.description,
            "url": f"{spec.slug}.html#{match.group(2)}",
            "text": section_text,
        })
    return entries


def audit_local_links() -> list[str]:
    broken: list[str] = []
    html_files = list(DIST_DIR.glob("*.html"))
    id_cache: dict[Path, set[str]] = {}
    for source_path in html_files:
        source = source_path.read_text(encoding="utf-8")
        for match in re.finditer(r'(?:href|src)="([^"]+)"', source):
            value = html.unescape(match.group(1))
            if value.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
                continue
            path_part, _, fragment = value.partition("#")
            target = source_path if not path_part else DIST_DIR / path_part
            if not target.exists():
                broken.append(f"{source_path.name}: {value}")
                continue
            if fragment and target.suffix.lower() == ".html":
                if target not in id_cache:
                    target_source = target.read_text(encoding="utf-8")
                    id_cache[target] = set(re.findall(r'\bid="([^"]+)"', target_source))
                if fragment not in id_cache[target]:
                    broken.append(f"{source_path.name}: {value}（锚点不存在）")
    return sorted(set(broken))


def build() -> dict[str, object]:
    expected_root = ROOT / "website" / "dist"
    if DIST_DIR.resolve() != expected_root.resolve():
        raise RuntimeError(f"不安全的输出目录：{DIST_DIR}")
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    shutil.copytree(ASSETS_DIR, DIST_DIR / "assets")
    shutil.copy2(WEBSITE_DIR / "styles" / "main.css", DIST_DIR / "main.css")
    shutil.copy2(WEBSITE_DIR / "scripts" / "main.js", DIST_DIR / "main.js")
    pdf_source = ROOT / "survival_guide.pdf"
    if pdf_source.exists():
        shutil.copy2(pdf_source, DIST_DIR / "survival_guide.pdf")

    page_template = load_template("page.html")
    category_template = load_template("category.html")
    index_template = load_template("index.html")
    search_entries: list[dict[str, str]] = []
    audit_pages: list[dict[str, object]] = []
    referenced_images: set[str] = set()
    conversion_mismatches: list[str] = []

    for spec in PAGES:
        source_path = CONTENT_DIR / spec.source
        source = source_path.read_text(encoding="utf-8")
        source_slice = slice_source(source, spec.start, spec.end)
        expected_counts = {
            "footnotes": source_slice.count(r"\footnote{"),
            "figures": source_slice.count(r"\begin{figure}"),
            "lists": source_slice.count(r"\begin{itemize}") + source_slice.count(r"\begin{enumerate}"),
            "tables": source_slice.count(r"\begin{table}") + source_slice.count(r"\begin{matrix}"),
        }
        source = normalize_heading_levels(prepare_source_for_spec(source_slice, spec))
        converter = LatexPageConverter(spec)
        article = converter.convert(source)
        referenced_images.update(converter.image_references)

        actual_counts = {
            "footnotes": len(converter.footnotes),
            "figures": converter.figure_count,
            "lists": converter.list_count,
            "tables": converter.table_count,
        }
        for kind, expected in expected_counts.items():
            actual = actual_counts[kind]
            if actual != expected:
                conversion_mismatches.append(
                    f"{spec.source} → {spec.slug}: {kind} 原文 {expected}，网页 {actual}"
                )

        category = CATEGORY_BY_SLUG[spec.category]
        sibling_slugs = [slug for slug in category.articles if slug != spec.slug]
        related = render_cards(sibling_slugs[:4], compact=True) if sibling_slugs else ""
        related_section = (
            f'<section class="related-section"><div class="section-heading small"><p class="eyebrow">RELATED</p><h2>继续浏览</h2></div><div class="related-grid">{related}</div></section>'
            if related else ""
        )
        rendered = replace_tokens(page_template, {
            "BODY_CLASS": "no-page-toc" if spec.slug == "freshman-timeline" else "",
            "TITLE": html.escape(spec.nav_title),
            "DESCRIPTION": html.escape(spec.description),
            "NAVIGATION": render_navigation(spec.category),
            "CATEGORY_TITLE": html.escape(category.title),
            "CATEGORY_URL": category_url(category),
            "PAGE_DESCRIPTION": html.escape(spec.description),
            "TOC": render_toc(converter.headings),
            "ARTICLE": article,
            "RELATED": related_section,
        })
        (DIST_DIR / f"{spec.slug}.html").write_text(rendered, encoding="utf-8")

        search_entries.extend(search_entries_for_article(spec, article))
        audit_pages.append({
            "source": spec.source,
            "output": f"{spec.slug}.html",
            "headings": len(converter.headings),
            "footnotes": len(converter.footnotes),
            "figures": converter.figure_count,
            "lists": converter.list_count,
            "tables": converter.table_count,
            "visible_characters": len(re.sub(r"\s+", "", plain_text(article))),
            "unknown_commands": sorted(converter.unknown_commands),
        })

    for category in CATEGORIES:
        if category.direct:
            continue
        original_intro = ""
        if category.slug == "majors":
            source = (CONTENT_DIR / "chapter-01-basic-information.tex").read_text(encoding="utf-8")
            intro_source = slice_source(source, r"\section{细谈本科专业}", r"\subsection{理论与应用力学}")
            intro_lines = intro_source.splitlines()[1:]
            intro_converter = LatexPageConverter(PageSpec("chapter-01-basic-information.tex", "majors", "专业介绍", category.description, "majors"))
            original_intro = intro_converter.convert("\n".join(intro_lines))
            referenced_images.update(intro_converter.image_references)
        category_html = replace_tokens(category_template, {
            "TITLE": html.escape(category.title),
            "DESCRIPTION": html.escape(category.description),
            "EYEBROW": html.escape(category.eyebrow),
            "NAVIGATION": render_navigation(category.slug),
            "CATEGORY_INTRO": original_intro,
            "TOPIC_CARDS": render_cards(category.articles),
        })
        (DIST_DIR / f"{category.slug}.html").write_text(category_html, encoding="utf-8")

    category_cards = "".join(
        f'<a class="portal-card portal-{index}" href="{category_url(category)}">'
        f'<span class="portal-number">{index:02d}</span><p>{html.escape(category.eyebrow)}</p>'
        f'<h2>{html.escape(category.title)}</h2><span>{html.escape(category.description)}</span>'
        f'<strong>进入栏目 →</strong></a>'
        for index, category in enumerate(CATEGORIES, 1)
    )
    index_html = replace_tokens(index_template, {
        "NAVIGATION": render_navigation(),
        "CATEGORY_CARDS": category_cards,
    })
    (DIST_DIR / "index.html").write_text(index_html, encoding="utf-8")
    (DIST_DIR / "search-index.js").write_text(
        "window.SEARCH_INDEX = " + json.dumps(search_entries, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )

    missing_images = sorted(
        path for path in referenced_images if not (ROOT / path).exists()
    )
    unknown_commands = sorted({
        command
        for page in audit_pages
        for command in page["unknown_commands"]
    })
    all_asset_files = sorted(path.name for path in ASSETS_DIR.iterdir() if path.is_file())
    copied_asset_files = sorted(path.name for path in (DIST_DIR / "assets").iterdir() if path.is_file())
    broken_links = audit_local_links()
    report = {
        "status": "ok" if not (missing_images or unknown_commands or conversion_mismatches or broken_links) else "failed",
        "pages": audit_pages,
        "summary": {
            "source_articles": len(PAGES),
            "category_pages": len([category for category in CATEGORIES if not category.direct]),
            "generated_html_pages": len(list(DIST_DIR.glob("*.html"))),
            "source_assets": len(all_asset_files),
            "copied_assets": len(copied_asset_files),
            "image_references": len(referenced_images),
            "missing_images": missing_images,
            "unknown_commands": unknown_commands,
            "conversion_mismatches": conversion_mismatches,
            "broken_links": broken_links,
            "search_entries": len(search_entries),
        },
    }
    (DIST_DIR / "build-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if missing_images:
        raise FileNotFoundError("网站引用的图片不存在：" + ", ".join(missing_images))
    if unknown_commands:
        raise RuntimeError("发现尚未支持的 LaTeX 命令：" + ", ".join(unknown_commands))
    if conversion_mismatches:
        raise RuntimeError("网站内容转换数量不一致：" + "; ".join(conversion_mismatches))
    if broken_links:
        raise RuntimeError("网站存在损坏的本地链接：" + "; ".join(broken_links))
    return report


def serve(port: int) -> None:
    class WebsiteHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(DIST_DIR), **kwargs)

    address = f"http://127.0.0.1:{port}/"
    print(f"本地网站已启动：{address}")
    print("按 Ctrl+C 停止。")
    ThreadingHTTPServer(("127.0.0.1", port), WebsiteHandler).serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="从 LaTeX 原文生成静态网站")
    parser.add_argument("--serve", action="store_true", help="生成后启动本地预览服务器")
    parser.add_argument("--port", type=int, default=8000, help="本地预览端口，默认 8000")
    args = parser.parse_args()

    report = build()
    summary = report["summary"]
    print("网站生成完成。")
    print(f"  页面：{summary['generated_html_pages']} 个 HTML 文件")
    print(f"  图片：{summary['copied_assets']} 个资源文件")
    print(f"  输出：{DIST_DIR / 'index.html'}")
    if args.serve:
        serve(args.port)


if __name__ == "__main__":
    main()
