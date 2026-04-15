#!/usr/bin/env python3
"""Convert PROJECT_OVERVIEW.md to PDF using fpdf2 with Chinese font support."""

import re
from pathlib import Path
from fpdf import FPDF

MD_FILE = Path("docs/PROJECT_OVERVIEW.md")
PDF_FILE = Path("docs/PROJECT_OVERVIEW.pdf")

# Chinese font on macOS
CN_FONT = "/System/Library/Fonts/STHeiti Medium.ttc"
FALLBACK_FONT = "/System/Library/Fonts/STHeiti Light.ttc"


def clean_inline_markdown(text):
    """Remove markdown inline formatting for PDF rendering."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    text = text.replace('> ', '')
    text = text.replace('---', '')
    return text


class WikiPDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return  # No header on title page
        self.set_font("STHeiti", "B", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, "Personal Knowledge System - Project Overview", align="R")
        self.line(10, 13, self.w - 10, 13)
        self.ln(5)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font("STHeiti", "", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, text):
        self.ln(3)
        self.set_font("STHeiti", "B", 16)
        self.set_text_color(30, 60, 120)
        # Clean any ** markers
        text = text.replace('**', '')
        self.multi_cell(self.w - 20, 9, text)
        self.ln(4)
        self.set_text_color(0, 0, 0)

    def sub_heading(self, text):
        self.ln(2)
        self.set_font("STHeiti", "B", 13)
        self.set_text_color(50, 80, 140)
        text = text.replace('**', '')
        self.multi_cell(self.w - 20, 8, text)
        self.ln(2)
        self.set_text_color(0, 0, 0)

    def sub_sub_heading(self, text):
        self.ln(1)
        self.set_font("STHeiti", "B", 11)
        text = text.replace('**', '')
        self.multi_cell(self.w - 20, 7, text)
        self.ln(1)

    def body_text(self, text):
        self.set_font("STHeiti", "", 10)
        text = clean_inline_markdown(text)
        self.multi_cell(self.w - 20, 6, text)
        self.ln(2)

    def code_block(self, text):
        self.set_fill_color(245, 245, 248)
        self.set_font("STHeiti", "", 7)
        lines = text.strip().split("\n")
        for line in lines:
            # Truncate very long lines to fit page
            max_w = self.w - 22
            if self.get_string_width(line) > max_w:
                # Split into chunks
                chunk = ""
                for ch in line:
                    test = chunk + ch
                    if self.get_string_width(test) > max_w:
                        self.set_x(11)
                        self.cell(max_w, 4.5, chunk, fill=True)
                        self.ln(4.5)
                        chunk = ch
                    else:
                        chunk = test
                if chunk:
                    self.set_x(11)
                    self.cell(max_w, 4.5, chunk, fill=True)
                    self.ln(4.5)
            else:
                self.set_x(11)
                self.cell(self.get_string_width(line) + 4, 4.5, line, fill=True)
                self.ln(4.5)
        self.ln(3)

    def bullet_item(self, text):
        self.set_font("STHeiti", "", 10)
        self.set_x(15)
        bullet = "\u2022"
        self.multi_cell(self.w - 30, 6, f"{bullet} {text}")
        self.ln(0.5)


def parse_markdown(md_text):
    """Simple markdown parser returning structured elements."""
    elements = []
    lines = md_text.split("\n")
    in_code_block = False
    code_buffer = []
    in_table = False
    table_headers = []
    table_rows = []

    for line in lines:
        # Code block toggle
        if line.strip().startswith("```"):
            if in_code_block:
                elements.append(("code", "\n".join(code_buffer)))
                code_buffer = []
                in_code_block = False
            else:
                if in_table:
                    elements.append(("table", (table_headers, table_rows)))
                    table_headers = []
                    table_rows = []
                    in_table = False
                in_code_block = True
            continue

        if in_code_block:
            code_buffer.append(line)
            continue

        # Table handling
        if "|" in line:
            if re.match(r'^[\s\|\-:]+$', line):
                continue  # Skip separator
            if not in_table:
                table_headers = [c.strip() for c in line.split("|") if c.strip()]
                in_table = True
            else:
                row = [c.strip() for c in line.split("|") if c.strip()]
                if row:
                    table_rows.append(row)
            continue
        elif in_table:
            elements.append(("table", (table_headers, table_rows)))
            table_headers = []
            table_rows = []
            in_table = False

        # Horizontal rule
        if line.strip() in ("---", "***", "* * *"):
            elements.append(("hr",))
            continue

        # Headings
        m = re.match(r'^(#{1,6})\s+(.+)$', line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            elements.append(("heading", level, text))
            continue

        # Blockquote
        if line.startswith("> "):
            elements.append(("blockquote", line[2:].strip()))
            continue

        # Empty line
        if not line.strip():
            continue

        # List item
        if re.match(r'^\s*[-*]\s+', line):
            text = re.sub(r'^\s*[-*]\s+', '', line)
            elements.append(("list", clean_inline_markdown(text)))
            continue

        # Regular text
        elements.append(("text", line))

    # Flush remaining
    if in_code_block:
        elements.append(("code", "\n".join(code_buffer)))
    if in_table:
        elements.append(("table", (table_headers, table_rows)))

    return elements


def simple_table(pdf, headers, rows):
    """Render a simple table."""
    n_cols = len(headers)
    if n_cols == 0:
        return

    col_width = (pdf.w - 22) / n_cols
    row_h = 6

    # Header row
    pdf.set_font("STHeiti", "B", 7)
    pdf.set_fill_color(30, 60, 120)
    pdf.set_text_color(255, 255, 255)
    for h in headers:
        pdf.cell(col_width, row_h, h.strip()[:15], border=1, fill=True, align="C")
    pdf.ln()

    # Data rows
    pdf.set_font("STHeiti", "", 7)
    pdf.set_text_color(0, 0, 0)
    fill = False
    for row in rows:
        if fill:
            pdf.set_fill_color(240, 240, 250)
        else:
            pdf.set_fill_color(255, 255, 255)
        for i in range(n_cols):
            cell = row[i].strip()[:20] if i < len(row) else ""
            cell = clean_inline_markdown(cell)
            pdf.cell(col_width, row_h, cell, border=1, fill=True, align="L")
        pdf.ln()
        fill = not fill
    pdf.ln(3)


def generate_pdf(elements, output_path):
    pdf = WikiPDF(format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Add fonts
    pdf.add_font("STHeiti", "", FALLBACK_FONT)
    pdf.add_font("STHeiti", "B", CN_FONT)
    pdf.add_font("STHeiti", "I", FALLBACK_FONT)

    for elem in elements:
        etype = elem[0]

        if etype == "heading":
            level = elem[1]
            text = elem[2]
            if level == 1 and "Personal Knowledge System" in text:
                # Title page
                pdf.set_font("STHeiti", "B", 22)
                pdf.set_text_color(30, 60, 120)
                pdf.multi_cell(pdf.w - 20, 12, text)
                pdf.ln(5)
                pdf.set_font("STHeiti", "", 12)
                pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(pdf.w - 20, 8, "From Karpathy's LLM Wiki to a Practical Knowledge System")
                pdf.ln(10)
                pdf.set_text_color(0, 0, 0)
            elif level == 2:
                pdf.section_title(text)
            elif level == 3:
                pdf.sub_heading(text)
            else:
                pdf.sub_sub_heading(text)

        elif etype == "text":
            pdf.body_text(elem[1])

        elif etype == "code":
            pdf.code_block(elem[1])

        elif etype == "table":
            headers, rows = elem[1]
            if headers:
                simple_table(pdf, headers, rows)

        elif etype == "list":
            pdf.bullet_item(elem[1])

        elif etype == "blockquote":
            pdf.set_font("STHeiti", "I", 10)
            pdf.set_text_color(80, 80, 80)
            pdf.set_x(15)
            pdf.multi_cell(pdf.w - 30, 6, elem[1])
            pdf.ln(2)
            pdf.set_text_color(0, 0, 0)

        elif etype == "hr":
            y = pdf.get_y()
            pdf.set_draw_color(180, 180, 180)
            pdf.line(10, y, pdf.w - 10, y)
            pdf.ln(5)

    pdf.output(str(output_path))
    print(f"PDF generated: {output_path}")


def main():
    if not MD_FILE.exists():
        print(f"Error: {MD_FILE} not found")
        return

    md_text = MD_FILE.read_text(encoding="utf-8")
    elements = parse_markdown(md_text)
    print(f"Parsed {len(elements)} elements from markdown")
    generate_pdf(elements, PDF_FILE)
    print(f"Output: {PDF_FILE.absolute()}")


if __name__ == "__main__":
    main()
