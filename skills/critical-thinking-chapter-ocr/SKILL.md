---
name: critical-thinking-chapter-ocr
description: OCR textbook pages from a PDF using VLM (@multimodal-looker) and merge into a single markdown document with sentence continuity fixes. Use when extracting text from PDF textbooks for: (1) Converting PDF pages to markdown, (2) Batch OCR processing a page range, (3) Extracting textbook content with footnotes and tables, (4) Processing academic books with headers, footnotes, and diagrams, (5) Merging multiple OCR pages into one document with proper sentence flow.
---

# Critical Thinking Chapter OCR

Extract and convert PDF textbook pages to markdown using VLM-based OCR, merge into a single document, and fix sentence continuity.

## Workflow

### Step 1: Extract PDF Pages

Extract pages as PNG images at 150 DPI:

```bash
python3 $HOME/.config/opencode/skills/critical-thinking-chapter-ocr/scripts/extract_pages.py \
    <pdf_path> <start_page> <end_page> /tmp/ocr_pages
```

### Step 2: OCR with VLM Subagent

Delegate the task to @multimodal-looker subagent to OCR all pages (leverage this model's native image capability instead of calling other tools).

**OCR Prompt:**
```
You are performing OCR on a textbook page. Follow these rules:

1. **Ignore headers**: Skip the page number, chapter number (e.g., "CHAPTER 1"), and chapter title at the top of the page (the content above the first horizontal divider line).
2. **Main text**: Extract in reading order, top-to-bottom, single-column layout.
3. **TABLES**: If a table exists, use markdown table format with | separators.
4. **Headers**: Use ## for section headers, **text** for bold, *text* for italic.
5. **Footnotes**: If superscript footnote markers exist, use [^N] in body and [^N]: content at END.
6. **Ignore**: Decorative elements, horizontal bars, ornaments, graphs, diagrams, and figures. Do not describe them—skip them entirely.
7. **CRITICAL**: Output ONLY extracted text. Do NOT repeat or hallucinate content. Do not include any description of images or graphics.
8. If text is unclear, indicate with [unclear] rather than guess.
```

**Subagent Task Template:**
```
OCR pages {start_page}-{end_page} from the textbook at /tmp/ocr_pages/

**CRITICAL INSTRUCTIONS:**
1. Process pages SEQUENTIALLY, one page at a time (page by page) to avoid rate limits.
2. Use your NATIVE IMAGE CAPABILITY to read and OCR each page directly — do NOT call any external OCR tools or APIs.
3. Save each page as: ./workspace/ocr_results_vlm/page_{NNN}.md (relative to project root)

Use the OCR prompt above for each page.

Process ALL pages. Report summary when done.
```

### Step 3: Merge Markdown Pages

Combine all OCR pages into one document:

```bash
python3 $HOME/.config/opencode/skills/critical-thinking-chapter-ocr/scripts/merge_markdown.py \
    ./workspace/ocr_results_vlm \
    ./workspace/ocr_results_vlm/merged_<start>-<end>.md \
    --start <start_page> --end <end_page>
```

### Step 4: Fix Sentence Continuity (LLM Cleanup)

Use an LLM to fix sentence splits at page boundaries and ensure proper text flow.

**LLM Cleanup Prompt:**
```
You are helping clean up a merged textbook chapter. The original content was split across multiple PDF pages during OCR, resulting in:
1. Possible sentence fragments at page boundaries
2. Possible repeated words/phrases at page boundaries
3. Possible orphaned punctuation

Your task:
1. Read the merged document carefully
2. Fix any sentence splits that occur at page boundaries - join incomplete sentences across page breaks
3. Remove any duplicate words/phrases that appear at the boundaries (a word may appear at the end of one page and the beginning of the next)
4. Ensure all paragraphs flow naturally
5. Preserve all markdown formatting: headers (##, ###), footnotes ([^N]), tables, bold, italic
6. Do NOT change the actual content - only fix structural issues

Output the cleaned version with proper sentence continuity.
```

**Note:** Delegate this cleanup job to @writing subagent. 

### Step 5: Argument Proposition Handling

Update the merged document if it contains argument analysis with proposition in angle brackets like:
- (A) <My client is innocent> because (B) <she was defending herself>

The `<a sentence>` format is used to denote propositions in logical arguments (common in philosophy/logic textbooks). Since Markdown interpret `< >` as HTML tags, these propositions become invisible.

**Solution:** When the angle brackets denote proposition (not HTML), wrap the content in backticks to ensure visibility:
- - ✅ (A) `<My client is innocent>` because (B) `<she was defending herself>`

### Step 6: Rectify Header Levels

Use an LLM to fix header levels based on the book's table of contents structure.

**ToC Header Convention:**
- `## CHAPTER X` (H2) - Chapter titles
- `### Section` (H3) - First level sections
- `#### Sub-section` (H4) - Second level sections

**Header Rectification Prompt:**
```
You are helping format a textbook chapter. The book's table of contents uses:
- ## for CHAPTER titles (H2)
- ### for major sections (H3)
- #### for subsections (H4)

Review the markdown and fix any inconsistent header levels. Also verify:
- Footnotes properly linked with [^N] syntax
- Tables in proper markdown format
- No repeated or hallucinated content

Output the corrected markdown.
```

## Scripts

- `scripts/extract_pages.py` - Extract PDF pages as PNG images
- `scripts/merge_markdown.py` - Merge OCR markdown pages into one file

## Example Usage

To OCR and merge pages 78-91 (run from project root):

1. Extract: `python3 $HOME/.config/opencode/skills/critical-thinking-chapter-ocr/scripts/extract_pages.py book.pdf 78 91 /tmp/ocr_pages`
2. OCR: Spawn @multimodal-looker subagent and leverage the model's image capability to do OCR. Output to `./workspace/ocr_results_vlm/`.
3. Merge: `python3 $HOME/.config/opencode/skills/critical-thinking-chapter-ocr/scripts/merge_markdown.py ./workspace/ocr_results_vlm ./workspace/ocr_results_vlm/merged_78-91.md --start 78 --end 91`
4. Cleanup: Spawn @writing subagent to cleanup prompt
5. Argument Proposition Handling
6. Header fix: Spawn @writing subagent with header rectification prompt
