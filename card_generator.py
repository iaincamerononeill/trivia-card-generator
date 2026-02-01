from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics


@dataclass(frozen=True)
class CardRow:
    level: str
    subject: str  # initial like "C"
    question: str
    answer: str


@dataclass(frozen=True)
class LayoutConfig:
    # Page/grid
    page_size: Tuple[float, float] = A4
    cols: int = 2
    rows: int = 4
    margin: float = 10 * mm
    gutter_x: float = 4 * mm
    gutter_y: float = 4 * mm

    # Card styling
    corner_radius: float = 3 * mm
    border_width: float = 1
    padding: float = 4 * mm

    # Header/badge
    header_height: float = 9 * mm
    badge_w: float = 14 * mm
    badge_h: float = 9 * mm

    # Typography
    font_name: str = "Helvetica"
    font_size_body: float = 11
    font_size_header: float = 10

    # Hard limits (tune these if you like)
    max_chars_question: int = 170
    max_chars_answer: int = 120
    max_chars_level: int = 20
    max_chars_subject: int = 3  # e.g. "C", "Sci", etc.


def _clean(s: str) -> str:
    return (s or "").strip().replace("\ufeff", "")


def load_cards(csv_path: Path) -> List[CardRow]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)

        # Detect header
        has_header = False
        try:
            sniff = csv.Sniffer()
            has_header = sniff.has_header(sample)
            dialect = sniff.sniff(sample)
        except csv.Error:
            dialect = csv.excel

        reader = csv.reader(f, dialect)
        rows = list(reader)

    # Drop completely empty lines
    rows = [r for r in rows if any(_clean(c) for c in r)]

    if not rows:
        raise ValueError("CSV appears to be empty.")

    if has_header:
        header = [c.lower().strip() for c in rows[0]]
        data = rows[1:]

        # Map columns by name, with a few aliases
        def find_col(*names: str) -> int:
            for n in names:
                if n in header:
                    return header.index(n)
            raise ValueError(f"Missing required column. Need one of: {names}. Found: {header}")

        i_level = find_col("level", "stage", "tier")
        i_subject = find_col("subject", "category", "cat")
        i_q = find_col("question", "q")
        i_a = find_col("answer", "a")

        cards: List[CardRow] = []
        for idx, r in enumerate(data, start=2):  # 1-based lines, header is line 1
            # Pad short rows
            while len(r) <= max(i_level, i_subject, i_q, i_a):
                r.append("")
            cards.append(
                CardRow(
                    level=_clean(r[i_level]),
                    subject=_clean(r[i_subject]),
                    question=_clean(r[i_q]),
                    answer=_clean(r[i_a]),
                )
            )
        return cards

    # No header: assume fixed order
    cards = []
    for idx, r in enumerate(rows, start=1):
        if len(r) < 4:
            raise ValueError(f"Row {idx} has {len(r)} columns, expected 4: level, subject, question, answer.")
        cards.append(CardRow(_clean(r[0]), _clean(r[1]), _clean(r[2]), _clean(r[3])))
    return cards


def _string_width(text: str, font: str, size: float) -> float:
    return pdfmetrics.stringWidth(text, font, size)


def wrap_text(text: str, font: str, size: float, max_width: float) -> List[str]:
    """
    Greedy word wrap using actual rendered width.
    """
    words = text.split()
    if not words:
        return [""]

    lines: List[str] = []
    current = words[0]
    for w in words[1:]:
        candidate = f"{current} {w}"
        if _string_width(candidate, font, size) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = w

    lines.append(current)

    # If a single "word" is too wide (eg a URL), hard-split it.
    fixed: List[str] = []
    for line in lines:
        if _string_width(line, font, size) <= max_width:
            fixed.append(line)
            continue

        chunk = ""
        for ch in line:
            cand = chunk + ch
            if _string_width(cand, font, size) <= max_width:
                chunk = cand
            else:
                if chunk:
                    fixed.append(chunk)
                chunk = ch
        if chunk:
            fixed.append(chunk)

    return fixed


def validate_card_lengths(cards: List[CardRow], cfg: LayoutConfig) -> None:
    for i, c in enumerate(cards, start=1):
        if len(c.level) > cfg.max_chars_level:
            raise ValueError(f"Row {i}: level too long ({len(c.level)}>{cfg.max_chars_level}): {c.level!r}")
        if len(c.subject) > cfg.max_chars_subject:
            raise ValueError(f"Row {i}: subject too long ({len(c.subject)}>{cfg.max_chars_subject}): {c.subject!r}")
        if len(c.question) > cfg.max_chars_question:
            raise ValueError(f"Row {i}: question too long ({len(c.question)}>{cfg.max_chars_question}).")
        if len(c.answer) > cfg.max_chars_answer:
            raise ValueError(f"Row {i}: answer too long ({len(c.answer)}>{cfg.max_chars_answer}).")
        if not c.level or not c.subject or not c.question or not c.answer:
            raise ValueError(f"Row {i}: one or more fields are blank.")


def grid_geometry(cfg: LayoutConfig) -> Tuple[float, float, float, float]:
    page_w, page_h = cfg.page_size
    total_gutter_x = cfg.gutter_x * (cfg.cols - 1)
    total_gutter_y = cfg.gutter_y * (cfg.rows - 1)

    usable_w = page_w - 2 * cfg.margin - total_gutter_x
    usable_h = page_h - 2 * cfg.margin - total_gutter_y

    card_w = usable_w / cfg.cols
    card_h = usable_h / cfg.rows
    return page_w, page_h, card_w, card_h


def draw_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    card_w: float,
    card_h: float,
    level: str,
    subject: str,
    body_text: str,
    cfg: LayoutConfig,
) -> None:
    # Outer border
    c.setLineWidth(cfg.border_width)
    c.roundRect(x, y, card_w, card_h, cfg.corner_radius, stroke=1, fill=0)

    # Header line (level)
    header_y_top = y + card_h - cfg.padding
    header_y_bottom = y + card_h - cfg.padding - cfg.header_height

    c.setFont(cfg.font_name, cfg.font_size_header)
    level_x = x + cfg.padding
    level_y = header_y_bottom + (cfg.header_height - cfg.font_size_header) / 2
    c.drawString(level_x, level_y, level)

    # Badge oval on right in header
    badge_x = x + card_w - cfg.padding - cfg.badge_w
    badge_y = header_y_bottom + (cfg.header_height - cfg.badge_h) / 2
    c.ellipse(badge_x, badge_y, badge_x + cfg.badge_w, badge_y + cfg.badge_h, stroke=1, fill=0)

    # Subject initial centred in oval
    c.setFont(cfg.font_name, cfg.font_size_header)
    subj_w = _string_width(subject, cfg.font_name, cfg.font_size_header)
    subj_x = badge_x + (cfg.badge_w - subj_w) / 2
    subj_y = badge_y + (cfg.badge_h - cfg.font_size_header) / 2
    c.drawString(subj_x, subj_y, subject)

    # Body area
    body_x = x + cfg.padding
    body_y = y + cfg.padding
    body_w = card_w - 2 * cfg.padding
    body_h = card_h - 2 * cfg.padding - cfg.header_height

    c.setFont(cfg.font_name, cfg.font_size_body)

    lines = wrap_text(body_text, cfg.font_name, cfg.font_size_body, body_w)

    # Fit check (hard fail)
    line_height = cfg.font_size_body * 1.25
    needed_h = len(lines) * line_height
    if needed_h > body_h:
        raise ValueError(
            "Text does not fit even after wrapping at 11pt. "
            f"Lines={len(lines)} need {needed_h:.1f}pt but have {body_h:.1f}pt."
        )

    # Draw lines top-down inside body box
    start_y = body_y + body_h - line_height
    for i, line in enumerate(lines):
        c.drawString(body_x, start_y - i * line_height, line)


def render_pdf(cards: List[CardRow], out_pdf: Path, cfg: LayoutConfig) -> None:
    validate_card_lengths(cards, cfg)
    page_w, page_h, card_w, card_h = grid_geometry(cfg)

    def card_xy(col: int, row: int) -> Tuple[float, float]:
        # row 0 is top row
        x = cfg.margin + col * (card_w + cfg.gutter_x)
        y = page_h - cfg.margin - (row + 1) * card_h - row * cfg.gutter_y
        return x, y

    def iter_positions() -> List[Tuple[int, int]]:
        return [(col, row) for row in range(cfg.rows) for col in range(cfg.cols)]

    positions = iter_positions()

    c = canvas.Canvas(str(out_pdf), pagesize=cfg.page_size)

    # Render in batches of 8 (one sheet)
    for batch_start in range(0, len(cards), cfg.cols * cfg.rows):
        batch = cards[batch_start : batch_start + cfg.cols * cfg.rows]

        # FRONT PAGE (questions)
        for i, card in enumerate(batch):
            col, row = positions[i]
            x, y = card_xy(col, row)
            draw_card(
                c,
                x,
                y,
                card_w,
                card_h,
                level=card.level,
                subject=card.subject,
                body_text=card.question,
                cfg=cfg,
            )
        c.showPage()

        # BACK PAGE (answers) - mirrored for duplex long-edge by swapping columns
        for i, card in enumerate(batch):
            col, row = positions[i]
            mirrored_col = (cfg.cols - 1) - col  # swap left/right
            x, y = card_xy(mirrored_col, row)
            draw_card(
                c,
                x,
                y,
                card_w,
                card_h,
                level=card.level,
                subject=card.subject,
                body_text=card.answer,
                cfg=cfg,
            )
        c.showPage()

    c.save()


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Generate Trivial Pursuit-style cards from CSV.")
    p.add_argument("csv_path", type=Path, help="Input CSV path")
    p.add_argument("--out", type=Path, default=Path("cards.pdf"), help="Output PDF path")
    args = p.parse_args()

    cards = load_cards(args.csv_path)
    render_pdf(cards, args.out, LayoutConfig())
    print(f"Done: {args.out.resolve()}")
