from __future__ import annotations

import html
import re
import sys
import zipfile
from pathlib import Path


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def run(text: str, *, style: str | None = None, bold: bool = False, italic: bool = False) -> str:
    props = []
    if bold:
        props.append("<w:b/>")
    if italic:
        props.append("<w:i/>")
    if style == "code":
        props.append('<w:rStyle w:val="CodeChar"/>')
    rpr = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
    preserve = ' xml:space="preserve"' if text.startswith(" ") or text.endswith(" ") else ""
    return f"<w:r>{rpr}<w:t{preserve}>{esc(text)}</w:t></w:r>"


def paragraph(text: str = "", *, style: str | None = None) -> str:
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{ppr}{run(text)}</w:p>"


def bullet(text: str, level: int = 0) -> str:
    return (
        "<w:p><w:pPr>"
        '<w:pStyle w:val="ListParagraph"/>'
        f'<w:numPr><w:ilvl w:val="{level}"/><w:numId w:val="1"/></w:numPr>'
        f"</w:pPr>{run(text)}</w:p>"
    )


def numbered(text: str, level: int = 0) -> str:
    return (
        "<w:p><w:pPr>"
        '<w:pStyle w:val="ListParagraph"/>'
        f'<w:numPr><w:ilvl w:val="{level}"/><w:numId w:val="2"/></w:numPr>'
        f"</w:pPr>{run(text)}</w:p>"
    )


def code_paragraph(text: str) -> str:
    return f'<w:p><w:pPr><w:pStyle w:val="CodeBlock"/></w:pPr>{run(text, style="code")}</w:p>'


def table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    col_count = max(len(row) for row in rows)
    grid = "".join('<w:gridCol w:w="2400"/>' for _ in range(col_count))
    out = [
        "<w:tbl>",
        '<w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="0" w:type="auto"/></w:tblPr>',
        f"<w:tblGrid>{grid}</w:tblGrid>",
    ]
    for row_index, row in enumerate(rows):
        out.append("<w:tr>")
        for cell in row + [""] * (col_count - len(row)):
            shade = '<w:shd w:fill="D9EAF7"/>' if row_index == 0 else ""
            out.append(
                "<w:tc>"
                f'<w:tcPr><w:tcW w:w="2400" w:type="dxa"/>{shade}</w:tcPr>'
                f"{paragraph(cell)}"
                "</w:tc>"
            )
        out.append("</w:tr>")
    out.append("</w:tbl>")
    return "".join(out)


def parse_table(lines: list[str], start: int) -> tuple[str, int] | None:
    if start + 1 >= len(lines):
        return None
    if not (lines[start].strip().startswith("|") and lines[start + 1].strip().startswith("|")):
        return None
    separator = lines[start + 1].strip().strip("|")
    if not all(re.fullmatch(r"\s*:?-{3,}:?\s*", part) for part in separator.split("|")):
        return None

    rows = []
    i = start
    while i < len(lines) and lines[i].strip().startswith("|"):
        if i != start + 1:
            rows.append([part.strip().strip("`") for part in lines[i].strip().strip("|").split("|")])
        i += 1
    return table(rows), i


def markdown_to_body(md: str) -> str:
    lines = md.splitlines()
    parts: list[str] = []
    i = 0
    in_code = False
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code = not in_code
            i += 1
            continue

        if in_code:
            parts.append(code_paragraph(line))
            i += 1
            continue

        parsed = parse_table(lines, i)
        if parsed:
            tbl, next_i = parsed
            parts.append(tbl)
            i = next_i
            continue

        if not stripped:
            parts.append(paragraph(""))
        elif stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped[level:].strip()
            style = f"Heading{min(level, 4)}"
            parts.append(paragraph(text, style=style))
        elif stripped.startswith("- "):
            parts.append(bullet(stripped[2:].strip()))
        elif re.match(r"^\d+\.\s+", stripped):
            parts.append(numbered(re.sub(r"^\d+\.\s+", "", stripped)))
        elif stripped.startswith(">"):
            parts.append(paragraph(stripped.lstrip("> ").strip(), style="Quote"))
        else:
            parts.append(paragraph(stripped))
        i += 1
    return "".join(parts)


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
</Types>
"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
"""

STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading4"><w:name w:val="heading 4"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:rPr><w:b/><w:sz w:val="22"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:pPr><w:ind w:left="720"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="CodeBlock"><w:name w:val="Code Block"/><w:basedOn w:val="Normal"/><w:pPr><w:shd w:fill="F2F2F2"/></w:pPr><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="19"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/><w:basedOn w:val="Normal"/><w:pPr><w:ind w:left="720"/></w:pPr><w:rPr><w:i/></w:rPr></w:style>
<w:style w:type="character" w:styleId="CodeChar"><w:name w:val="Code Char"/><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/></w:rPr></w:style>
<w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/><w:tblPr><w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/></w:tblBorders></w:tblPr></w:style>
</w:styles>
"""

NUMBERING = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:abstractNum w:abstractNumId="1"><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>
<w:abstractNum w:abstractNumId="2"><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>
<w:num w:numId="1"><w:abstractNumId w:val="1"/></w:num>
<w:num w:numId="2"><w:abstractNumId w:val="2"/></w:num>
</w:numbering>
"""


def document_xml(body: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
{body}
<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>
</w:body>
</w:document>
"""


def write_docx(md_path: Path, docx_path: Path) -> None:
    body = markdown_to_body(md_path.read_text(encoding="utf-8"))
    docx_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(docx_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES)
        zf.writestr("_rels/.rels", RELS)
        zf.writestr("word/_rels/document.xml.rels", DOC_RELS)
        zf.writestr("word/document.xml", document_xml(body))
        zf.writestr("word/styles.xml", STYLES)
        zf.writestr("word/numbering.xml", NUMBERING)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Uso: python scripts/md_to_docx.py entrada.md salida.docx")
    write_docx(Path(sys.argv[1]), Path(sys.argv[2]))
