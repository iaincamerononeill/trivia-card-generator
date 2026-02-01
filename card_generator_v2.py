from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import HexColor


# Trivial Pursuit-style colors assigned by position (1-6)
# Colors are assigned to questions in order, regardless of subject
POSITION_COLORS = [
    HexColor('#FFD700'),      # Position 1 - Yellow
    HexColor('#228B22'),      # Position 2 - Green
    HexColor('#FF69B4'),      # Position 3 - Pink
    HexColor('#8B4513'),      # Position 4 - Brown
    HexColor('#0066CC'),      # Position 5 - Blue
    HexColor('#FF8C00'),      # Position 6 - Orange
]


@dataclass(frozen=True)
class Question:
    subject: str
    text: str
    answer: str


@dataclass(frozen=True)
class Card:
    level: str
    questions: List[Question]  # Should have 6 questions


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
    padding: float = 5 * mm

    # Header
    header_height: float = 8 * mm

    # Subject badge (oval bullet)
    badge_w: float = 10 * mm
    badge_h: float = 6 * mm
    badge_margin: float = 2 * mm

    # Typography
    font_name: str = "Helvetica"
    font_name_bold: str = "Helvetica-Bold"
    font_size_body: float = 9
    font_size_header: float = 10
    font_size_subject: float = 7


def _clean(s: str) -> str:
    return (s or "").strip().replace("\ufeff", "")


def _string_width(text: str, font: str, size: float) -> float:
    return pdfmetrics.stringWidth(text, font, size)


def wrap_text(text: str, font: str, size: float, max_width: float) -> List[str]:
    """Greedy word wrap using actual rendered width."""
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

    # Hard-split long words
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


def load_cards_from_csv(csv_path: Path) -> List[Card]:
    """Load cards from CSV, grouping questions by level (6 per card)."""
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Group by level
    level_groups: Dict[str, List[Question]] = {}
    for row in rows:
        level = _clean(row['level'])
        subject = _clean(row['subject'])
        question = _clean(row['question'])
        answer = _clean(row['answer'])
        
        # Subject can be any code (will be validated for uniqueness per card later)
        if not subject:
            raise ValueError("Subject code cannot be empty")
        
        q = Question(subject=subject, text=question, answer=answer)
        
        if level not in level_groups:
            level_groups[level] = []
        level_groups[level].append(q)
    
    # Create cards with 6 questions each
    cards: List[Card] = []
    for level, questions in level_groups.items():
        # Split into groups of 6
        for i in range(0, len(questions), 6):
            card_questions = questions[i:i+6]
            
            # Ensure exactly 6 questions
            if len(card_questions) < 6:
                raise ValueError(
                    f"Level '{level}' card {i//6 + 1} has only {len(card_questions)} questions.\n"
                    f"Each card needs exactly 6 questions (one per subject)."
                )
            
            # Check for duplicate subjects within this card
            card_subjects = [q.subject for q in card_questions]
            if len(card_subjects) != len(set(card_subjects)):
                duplicates = [s for s in card_subjects if card_subjects.count(s) > 1]
                raise ValueError(
                    f"Level '{level}' card {i//6 + 1} has duplicate subjects: {', '.join(set(duplicates))}\n"
                    f"Each card must have 6 different subjects."
                )
            
            cards.append(Card(level=level, questions=card_questions))
    
    return cards


def grid_geometry(cfg: LayoutConfig) -> Tuple[float, float, float, float]:
    page_w, page_h = cfg.page_size
    total_gutter_x = cfg.gutter_x * (cfg.cols - 1)
    total_gutter_y = cfg.gutter_y * (cfg.rows - 1)

    usable_w = page_w - 2 * cfg.margin - total_gutter_x
    usable_h = page_h - 2 * cfg.margin - total_gutter_y

    card_w = usable_w / cfg.cols
    card_h = usable_h / cfg.rows
    return page_w, page_h, card_w, card_h


def draw_subject_badge(c: canvas.Canvas, x: float, y: float, subject: str, color: HexColor, cfg: LayoutConfig):
    """Draw colored oval badge with subject initial."""
    # Color is now passed in based on position
    
    # Draw filled oval
    c.setFillColor(color)
    c.setStrokeColor(color)
    c.ellipse(x, y, x + cfg.badge_w, y + cfg.badge_h, stroke=1, fill=1)
    
    # Draw subject text in white
    c.setFillColor(HexColor('#FFFFFF'))
    c.setFont(cfg.font_name_bold, cfg.font_size_subject)
    
    subj_w = _string_width(subject, cfg.font_name_bold, cfg.font_size_subject)
    text_x = x + (cfg.badge_w - subj_w) / 2
    text_y = y + (cfg.badge_h - cfg.font_size_subject) / 2
    c.drawString(text_x, text_y, subject)


def draw_card_questions(c: canvas.Canvas, x: float, y: float, card_w: float, card_h: float, 
                       card: Card, cfg: LayoutConfig):
    """Draw the front of a card with 6 questions."""
    # Outer border
    c.setStrokeColor(HexColor('#000000'))
    c.setLineWidth(cfg.border_width)
    c.roundRect(x, y, card_w, card_h, cfg.corner_radius, stroke=1, fill=0)

    # Header with level
    c.setFillColor(HexColor('#000000'))
    c.setFont(cfg.font_name_bold, cfg.font_size_header)
    header_x = x + cfg.padding
    header_y = y + card_h - cfg.padding - cfg.font_size_header
    c.drawString(header_x, header_y, card.level)

    # Questions area
    questions_start_y = y + card_h - cfg.padding - cfg.header_height - cfg.padding
    available_height = card_h - 2 * cfg.padding - cfg.header_height
    question_height = available_height / 6

    c.setFont(cfg.font_name, cfg.font_size_body)
    
    for i, q in enumerate(card.questions):
        if not q.text:
            continue
            
        q_y = questions_start_y - (i * question_height)
        
        # Draw colored subject badge (color by position)
        badge_x = x + cfg.padding
        badge_y = q_y - cfg.badge_h / 2  # Center the badge in the question area
        color = POSITION_COLORS[i]  # Assign color by position in card
        draw_subject_badge(c, badge_x, badge_y, q.subject, color, cfg)
        
        # Draw question text
        text_x = badge_x + cfg.badge_w + cfg.badge_margin
        text_width = card_w - 2 * cfg.padding - cfg.badge_w - cfg.badge_margin
        
        c.setFillColor(HexColor('#000000'))
        lines = wrap_text(q.text, cfg.font_name, cfg.font_size_body, text_width)
        
        line_height = cfg.font_size_body * 1.2
        # Center text vertically with the badge
        total_text_height = len(lines[:2]) * line_height
        text_start_y = badge_y + (cfg.badge_h + total_text_height) / 2 - line_height / 2
        
        for j, line in enumerate(lines[:2]):  # Max 2 lines per question
            line_y = text_start_y - (j * line_height)
            c.drawString(text_x, line_y, line)


def draw_card_answers(c: canvas.Canvas, x: float, y: float, card_w: float, card_h: float,
                     card: Card, cfg: LayoutConfig, rotate_180: bool = False):
    """Draw the back of a card with 6 answers.
    
    Args:
        rotate_180: If True, rotates the card content 180° for long-edge duplex printing
                   so that when cut and flipped, the answer appears right-side up.
    """
    if rotate_180:
        # Save the graphics state
        c.saveState()
        
        # Rotate 180° around the center of the card
        center_x = x + card_w / 2
        center_y = y + card_h / 2
        c.translate(center_x, center_y)
        c.rotate(180)
        c.translate(-center_x, -center_y)
    
    # Outer border
    c.setStrokeColor(HexColor('#000000'))
    c.setLineWidth(cfg.border_width)
    c.roundRect(x, y, card_w, card_h, cfg.corner_radius, stroke=1, fill=0)

    # Header with level
    c.setFillColor(HexColor('#000000'))
    c.setFont(cfg.font_name_bold, cfg.font_size_header)
    header_x = x + cfg.padding
    header_y = y + card_h - cfg.padding - cfg.font_size_header
    c.drawString(header_x, header_y, f"{card.level} - ANSWERS")

    # Answers area
    answers_start_y = y + card_h - cfg.padding - cfg.header_height - cfg.padding
    available_height = card_h - 2 * cfg.padding - cfg.header_height
    answer_height = available_height / 6

    c.setFont(cfg.font_name, cfg.font_size_body)
    
    for i, q in enumerate(card.questions):
        if not q.answer:
            continue
            
        a_y = answers_start_y - (i * answer_height)
        
        # Draw colored subject badge (color by position)
        badge_x = x + cfg.padding
        badge_y = a_y - cfg.badge_h / 2  # Center the badge in the answer area
        color = POSITION_COLORS[i]  # Assign color by position in card
        draw_subject_badge(c, badge_x, badge_y, q.subject, color, cfg)
        
        # Draw answer text
        text_x = badge_x + cfg.badge_w + cfg.badge_margin
        text_width = card_w - 2 * cfg.padding - cfg.badge_w - cfg.badge_margin
        
        c.setFillColor(HexColor('#000000'))
        lines = wrap_text(q.answer, cfg.font_name, cfg.font_size_body, text_width)
        
        line_height = cfg.font_size_body * 1.2
        # Center text vertically with the badge
        total_text_height = len(lines[:2]) * line_height
        text_start_y = badge_y + (cfg.badge_h + total_text_height) / 2 - line_height / 2
        
        for j, line in enumerate(lines[:2]):  # Max 2 lines per answer
            line_y = text_start_y - (j * line_height)
            c.drawString(text_x, line_y, line)
    
    if rotate_180:
        # Restore the graphics state
        c.restoreState()


def render_pdf(cards: List[Card], out_pdf: Path, cfg: LayoutConfig) -> None:
    page_w, page_h, card_w, card_h = grid_geometry(cfg)

    def card_xy(col: int, row: int) -> Tuple[float, float]:
        x = cfg.margin + col * (card_w + cfg.gutter_x)
        y = page_h - cfg.margin - (row + 1) * card_h - row * cfg.gutter_y
        return x, y

    def iter_positions() -> List[Tuple[int, int]]:
        return [(col, row) for row in range(cfg.rows) for col in range(cfg.cols)]

    positions = iter_positions()
    c = canvas.Canvas(str(out_pdf), pagesize=cfg.page_size)

    # Render in batches of 8 (one sheet = 2x4 grid)
    for batch_start in range(0, len(cards), cfg.cols * cfg.rows):
        batch = cards[batch_start : batch_start + cfg.cols * cfg.rows]

        # FRONT PAGE (questions)
        for i, card in enumerate(batch):
            col, row = positions[i]
            x, y = card_xy(col, row)
            draw_card_questions(c, x, y, card_w, card_h, card, cfg)
        c.showPage()

        # BACK PAGE (answers) - for duplex long-edge printing
        # Layout ensures when printed, flipped along long edge, cut, and each card flipped:
        # - Keep columns the same
        # - Reverse rows (top row of questions → bottom row of answers)
        # - Rotate each card 180° so answers appear right-side up when flipped
        for i, card in enumerate(batch):
            col, row = positions[i]
            mirrored_row = (cfg.rows - 1) - row
            x, y = card_xy(col, mirrored_row)
            draw_card_answers(c, x, y, card_w, card_h, card, cfg, rotate_180=True)
        c.showPage()

    c.save()


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Generate Trivial Pursuit-style cards from CSV.")
    p.add_argument("csv_path", type=Path, help="Input CSV path")
    p.add_argument("--out", type=Path, default=Path("cards.pdf"), help="Output PDF path")
    args = p.parse_args()

    cards = load_cards_from_csv(args.csv_path)
    render_pdf(cards, args.out, LayoutConfig())
    print(f"Done: {args.out.resolve()}")
    print(f"Generated {len(cards)} cards with 6 questions each")
