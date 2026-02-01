# Trivia Card Generator

A Python tool that generates printable category-based trivia cards from CSV files.

## Disclaimer

This is an independent educational tool for creating custom trivia cards. It is not affiliated with, endorsed by, or connected to any commercial trivia game products or trademarks.

## Purpose

This project creates professional, print-ready trivia cards with:

- **A4 portrait layout** (2 columns × 4 rows = 8 cards per sheet)
- **Multi-category format** - 6 questions per card (one per subject)
- **Colored subject bullets** - Positioned by slot (1-6), not subject type
- **Double-sided printing** (duplex, long-edge flip) with proper alignment
- **Questions on front, answers on back** (rotated 180° for correct flip orientation)
- **Level grouping** (Primary, Secondary, Adult, etc.)
- **Flexible subjects** - Each level can use different subject codes

The output is a single interleaved PDF:
- Page 1: Question fronts
- Page 2: Answer backs
- Page 3: Question fronts
- Page 4: Answer backs
- etc.

Users can print once and cut – perfect for school, home, or game nights.

## Technical Approach

Built with Python and ReportLab for precise PDF generation.

**Why ReportLab?**
- Precise layout control
- Reliable duplex alignment
- Professional print output
- No dependency on Word/Office

**Core Features:**
- CSV parsing with automatic header detection
- Content validation and length checking
- Intelligent text wrapping based on actual font metrics
- Automatic rejection of oversized content
- Position-based color assignment (colors by slot, not subject)
- Proper duplex alignment with 180° rotation for long-edge printing
- Flexible subject codes - different levels can use different subjects

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install reportlab
   ```

2. **Create your CSV file** with 6 questions per level:
   ```csv
   level,subject,question,answer
   Primary School,M,What is 7 x 8?,56
   Primary School,S,What gas do plants produce?,Oxygen
   Primary School,E,Who wrote Harry Potter?,J.K. Rowling
   ... (3 more questions for Primary School)
   Secondary School,M,What is the square root of 144?,12
   ... (5 more questions for Secondary School)
   ```

3. **Generate your cards:**
   ```bash
   python card_generator_v2.py your_cards.csv --out my_trivia.pdf
   ```

4. **Print and play!**

## Requirements

- Python ≥ 3.9
- reportlab

**Installation:**
```bash
pip install reportlab
```

**For Development/Testing:**
```bash
pip install reportlab pytest
```

No other dependencies required.

## Input Format (CSV)

### Format (with headers)
```csv
level,subject,question,answer
Primary School,M,What is 7 x 8?,56
Primary School,S,What gas do plants produce?,Oxygen
Primary School,E,Who wrote Harry Potter?,J.K. Rowling
Primary School,H,What year did WW2 end?,1945
Primary School,G,What is the capital of France?,Paris
Primary School,C,What does RAM stand for?,Random Access Memory
```

**Column Requirements:**
1. **level** - Difficulty level (e.g., "Primary School", "Secondary School", "Adult")
2. **subject** - Subject code (Any single character or short code, must have 6 unique per card)
3. **question** - The question text
4. **answer** - The answer text

**Important:** 
- Each card requires exactly **6 questions with 6 different subjects**
- No duplicate subjects within the same card
- Subject codes can be anything (M, S, E, H, G, C for primary; P, A, L, M, S, T for adults, etc.)
- Different levels can use different subject sets
- Colors are assigned by position (1-6) not by subject type

### Color Positions (All Levels)

Colors are assigned by position on the card, not by subject:

- **Position 1** - 🟡 Yellow
- **Position 2** - 🟢 Green
- **Position 3** - 🩷 Pink  
- **Position 4** - 🟤 Brown
- **Position 5** - 🔵 Blue
- **Position 6** - 🟠 Orange

**Example:**
- **Primary cards**: Position 1=Math, Position 2=Science, etc.
- **Adult cards**: Position 1=Politics, Position 2=Arts, etc.

The colors stay consistent across all levels, making gameplay uniform even with different subject sets.

### Example Subject Codes

**Primary School:**
- **M** (Math), **S** (Science), **E** (English), **H** (History), **G** (Geography), **C** (Computing)

**Adult:**
- **P** (Politics), **A** (Arts), **L** (Literature), **M** (Music), **S** (Sports), **T** (Technology)

You can use any codes you like as long as each card has 6 unique subjects.

⚠️ **Empty fields are not allowed** – the script will reject incomplete cards.

## Usage

### Multi-Category Layout (Recommended)

**Generate cards with colored subject bullets:**
```bash
python card_generator_v2.py cards.csv --out output.pdf
```

**Features:**
- 6 questions per card (one per subject position)
- Colored oval bullets assigned by position (not subject type)
- Questions on front, answers on back
- Answers rotated 180° for proper long-edge duplex alignment
- Vertically centered text alignment
- Supports any subject codes (different levels can have different subjects)

### Classic Layout (Single Question Per Card)

**Generate traditional single-question cards:**
```bash
python card_generator.py cards.csv --out output.pdf
```

### Using the Notebook

The code can also be run from the Jupyter notebook `card_generator.ipynb`.

### Printing Instructions

1. **Paper:** A4
2. **Duplex:** Flip on long edge
3. **Scale:** 100% (no "fit to page")
4. **Cut** along grid lines after printing
5. **Test first** with a sample sheet to verify alignment

When you cut and flip each card, the answer will appear right-side up on the reverse!

## Code Architecture

### New Layout (card_generator_v2.py)

#### Main Components

**1. `Question` & `Card`**
Dataclasses representing the structure:
- `Question` - subject, text, answer
- `Card` - level, list of 6 questions

**2. `POSITION_COLORS`**
List of colors assigned to positions 1-6 on each card:
```python
POSITION_COLORS = [
    HexColor('#FFD700'),      # Position 1 - Yellow
    HexColor('#228B22'),      # Position 2 - Green
    HexColor('#FF69B4'),      # Position 3 - Pink
    HexColor('#8B4513'),      # Position 4 - Brown
    HexColor('#0066CC'),      # Position 5 - Blue
    HexColor('#FF8C00'),      # Position 6 - Orange
]
```

Colors are assigned by position, not subject code, allowing different levels to use different subjects while maintaining consistent color positions.

**3. `load_cards_from_csv()`**
- Reads CSV file
- Groups questions by level
- Creates Card objects with 6 questions each
- Validates that each card has 6 unique subjects (subject codes can be anything)
- No longer enforces specific subject codes

**4. `draw_subject_badge()`**
- Draws colored oval bullet
- Centers subject initial in white text
- Color is passed in based on position (1-6), not subject code

**5. `draw_card_questions()` & `draw_card_answers()`**
- Renders questions with colored bullets on front
- Renders answers with matching bullets on back (rotated 180° when `rotate_180=True`)
- Colors assigned by position (index 0-5) in the card's question list
- Vertically centers text with badges
- Wraps long text (max 2 lines)

**6. `render_pdf()`**
- Splits cards into batches of 8 (one sheet)
- Draws front page with questions
- Draws back page with answers:
  - Keeps columns in same position
  - Reverses rows (top↔bottom)
  - Rotates each card 180° for correct alignment when flipped
- Writes interleaved PDF optimized for duplex long-edge printing

### Classic Layout (card_generator.py)

Original single-question-per-card format. See code comments for details.

**To modify layout, start with:**
- `LayoutConfig` for dimensions and styling
- `draw_card_questions()` / `draw_card_answers()` for rendering logic

## Design Constraints

### Typography
- Body text: 11pt minimum
- Header: 10pt
- No automatic font shrinking

### Length Limits (Default)
Defined in `LayoutConfig`:
```python
max_chars_question = 170
max_chars_answer = 120
max_chars_level = 20
max_chars_subject = 3
```

These are conservative limits. Long words may still fail even under the limit.

### Failure Policy
**The script fails fast if content won't fit.**

This prevents producing unusable PDFs. Better to reject a card than print garbage.

## Known Limitations

### 1. Printer Drift
Different printers may shift backs slightly. If misalignment occurs, offsets can be added:
```python
back_offset_x = 2 * mm
back_offset_y = 1 * mm
```

### 2. No Hyphenation
Long words are split at character level if they don't fit.

### 3. No GUI
Command-line only (for now).

### 4. Single Font
Currently uses Helvetica throughout.

## Common Errors & Fixes

### "Subject code cannot be empty"
**Cause:** A row in your CSV has an empty subject field.

**Fix:** Add a valid subject code to all rows.

### "Level X card Y has duplicate subjects"
**Cause:** The same subject appears twice within a single card (6 questions).

**Fix:** Each card must have 6 different subjects. Ensure each group of 6 questions has unique subject codes.

### "Level X card Y has only N questions"
**Cause:** A level doesn't have questions in multiples of 6.

**Fix:** Add more questions to reach a multiple of 6 (6, 12, 18, etc.). Each complete card needs exactly 6 questions.

### "ModuleNotFoundError: No module named 'reportlab'"
**Cause:** reportlab not installed.

**Fix:**
```bash
pip install reportlab
```

### "Text does not fit even after wrapping"
**Cause:** Question/answer text is too long for the card space.

**Fix:**
- Shorten the content in your CSV
- Questions/answers wrap to max 2 lines each

### "Row X: question too long"
**Cause:** Character limit exceeded during validation.

**Fix:**
- Edit the CSV to shorten content
- Or update limits in `LayoutConfig`

### Backs Misaligned After Printing
**Cause:** Printer duplex offset.

**Fix:**
- Test print on plain paper first
- Some printers may require manual offset adjustments in the code

## Customization

### Changing Colors

Edit `POSITION_COLORS` in `card_generator_v2.py`:
```python
POSITION_COLORS = [
    HexColor('#0066CC'),  # Change position 1 to your color
    HexColor('#FF69B4'),  # Position 2
    # ...
]
```

Note: Colors are assigned by position, not subject code.

### Changing Layout

Modify `LayoutConfig` class:
```python
@dataclass(frozen=True)
class LayoutConfig:
    badge_w: float = 10 * mm        # Badge width
    badge_h: float = 6 * mm         # Badge height
    font_size_body: float = 9       # Text size
    # ...
}
```

### Changing Grid Size

Default is 2×4 (8 cards per sheet). To change:
```python
cols: int = 3  # 3 columns
rows: int = 3  # 3 rows
```
⚠️ Test duplex alignment after changing!
- Test with different offset values until aligned

## Testing Checklist

Before finalising a PDF:

- [ ] CSV validates with no errors
- [ ] Test print on plain paper
- [ ] Check front/back alignment
- [ ] Check smallest font is readable
- [ ] Check badge positioning
- [ ] Cut one sheet and verify usability

### Running Automated Tests

The project includes a comprehensive test suite with 36+ tests covering all major functionality.

**Run all tests:**
```bash
python -m pytest test_card_generator.py -v
```

**Run with coverage report:**
```bash
python -m pytest test_card_generator.py -v --tb=short
```

**Run specific test class:**
```bash
python -m pytest test_card_generator.py::TestLoadCards -v
```

**Test Coverage:**
- ✅ CardRow dataclass tests
- ✅ LayoutConfig validation
- ✅ CSV loading (with/without headers, alternate formats)
- ✅ Card validation (length limits, empty fields)
- ✅ Text wrapping (word wrap, long URLs, character splitting)
- ✅ Grid geometry calculations
- ✅ PDF rendering (single/multiple sheets)
- ✅ Duplex mirroring logic
- ✅ Full integration workflow tests

## Future Improvements

Suggested extensions if time allows:

### 1. Config File
Externalise `LayoutConfig` to YAML/JSON for easier customisation.

### 2. Preview Mode
Generate low-res preview images before printing.

### 3. GUI
Simple Tkinter or web UI for non-technical users.

### 4. Themes
Multiple fonts and colour schemes.

### 5. Auto-Reflow Mode
Optional mode that shrinks font instead of rejecting oversized content.

## Maintenance Notes

### If Modifying Layout
Only change code in:
- `LayoutConfig` (dataclass)
- `draw_card()` (rendering)
- `grid_geometry()` (calculations)

**⚠️ Avoid editing mirroring logic unless you understand duplex printing.**

### If Changing Grid Dimensions
Update `cols` and `rows` in `LayoutConfig`, then test duplex alignment thoroughly.

## Design Philosophy

This project was designed for:
- Educational trivia cards for various age groups
- School and home use
- Personal and non-commercial applications
- Low-friction printing
- **Reliability over "clever" formatting**

The **"fail fast" approach is deliberate:** Bad cards are worse than no cards.

## Project Structure

```
Trivia card generator/
├── card_generator.ipynb     # Jupyter notebook implementation
├── card_generator.py        # Classic layout (single question per card)
├── card_generator_v2.py     # New layout (6 questions with colored bullets)
├── test_card_generator.py   # Comprehensive test suite (36+ tests)
├── sample_cards.csv         # Example input (classic format)
├── sample_cards_v2.csv      # Example input (grouped by level)
├── README.md                # This file
└── *.pdf                    # Generated output files
```

## License

[Add your license here]

## Author

Created for educational and personal use.

**Intended Use:** This tool is designed for personal, educational, and non-commercial purposes only. Users are responsible for ensuring their use complies with applicable laws and regulations.
