---
name: critical-thinking-chapter-ocr
description: OCR textbook pages from a PDF using VLM (multimodal-looker subagent) and merge into a single markdown document with sentence continuity fixes. Use when extracting text from PDF textbooks for: (1) Converting PDF pages to markdown, (2) Batch OCR processing a page range, (3) Extracting textbook content with footnotes and tables, (4) Processing academic books with headers, footnotes, and diagrams, (5) Merging multiple OCR pages into one document with proper sentence flow.
---

# Critical Thinking Chapter OCR

Extract and convert PDF textbook pages to markdown using VLM-based OCR, merge into a single document, and fix sentence continuity.

## Prerequisites

```bash
pip install pymupdf
```

## Workflow

### MANDATORY: Create Todo List First

**Before starting any work, create a comprehensive todo list using `todowrite`.** This ensures:
- Progress visibility for the user
- Recovery from interruptions
- No skipped or duplicated steps

**Full Workflow Todo Template (pages {start}-{end}):**
```
todowrite(todos=[
  // Step 1: Extract
  { content: "Step 1: Extract PDF pages {start}-{end} to ./workspace/ocr_pages/", status: "pending", priority: "high" },
  
  // Step 2: OCR (one todo per page)
  { content: "Step 2.1: OCR page {start} — write to ./workspace/ocr_results_vlm/page_{NNN}.md", status: "pending", priority: "high" },
  { content: "Step 2.2: OCR page {start+1} — write to ./workspace/ocr_results_vlm/page_{NNN}.md", status: "pending", priority: "high" },
  // ... one todo per page ...
  { content: "Step 2.N: OCR page {end} — write to ./workspace/ocr_results_vlm/page_{NNN}.md", status: "pending", priority: "high" },
  
  // Step 3: Merge
  { content: "Step 3: Merge pages to ./workspace/ocr_results_vlm/merged_{start}-{end}.md", status: "pending", priority: "high" },
  
  // Step 4: Cleanup
  { content: "Step 4: Fix sentence continuity via writing subagent", status: "pending", priority: "high" },
  
  // Step 5: Cross-check
  { content: "Step 5: Cross-check merged doc against individual OCR files via Oracle subagent", status: "pending", priority: "high" },
  
  // Step 6: Proposition handling
  { content: "Step 6: Wrap angle-bracket propositions in backticks", status: "pending", priority: "medium" },
  
  // Step 7: Header rectification
  { content: "Step 7: Rectify header levels via writing subagent", status: "pending", priority: "medium" },
  
  // Step 8: Final formatting
  { content: "Step 8: Final formatting — escape leading + characters", status: "pending", priority: "medium" },
])
```

**Execution Rules (MANDATORY):**
1. Mark todo `in_progress` BEFORE starting each step
2. Mark todo `completed` IMMEDIATELY after finishing (never batch)
3. Only ONE todo can be `in_progress` at a time
4. If session is interrupted, resume from the first `pending` todo

---

### Step 1: Extract PDF Pages

Extract pages as PNG images at 150 DPI:

```bash
python3 $HOME/.config/opencode/skills/critical-thinking-chapter-ocr/scripts/extract_pages.py \
    <pdf_path> <start_page> <end_page> ./workspace/ocr_pages
```

### Step 2: OCR with VLM Subagent

**IMPORTANT: The `multimodal-looker` subagent can only READ files. The orchestrating agent must coordinate page-by-page OCR calls and write the output files.**

The orchestrator should call `multimodal-looker` **sequentially, one page at a time** to avoid rate limits.

**Execution Pattern (follow todo list):**
1. For each page todo (already created in initial todo list):
   - Mark todo `in_progress`
   - Invoke `multimodal-looker` subagent with the page image path
   - Wait for result (sequential execution prevents rate limits)
   - Write the returned OCR text to `./workspace/ocr_results_vlm/page_{NNN}.md`
   - Mark todo `completed`
2. Continue until all OCR todos are complete

**OCR Prompt for Each Page:**
```
You are performing OCR on a textbook page. Follow these rules:

1. **Ignore headers**: Skip the page number, chapter number (e.g., "CHAPTER 1"), and chapter title at the top of the page (the content above the first horizontal divider line).
2. **Main text**: Extract in reading order, top-to-bottom, single-column layout.
3. **TABLES**: If a table exists, use markdown table format with | separators.
4. **LOCAL 2-COLUMN LAYOUT**: If you detect a LOCAL (partial page) 2-column layout where:
   - Same number of lines in left and right columns
   - Content aligns horizontally (parallel/related content)
   - Examples: English argument ↔ symbolic logic, placeholder ↔ concrete terms, argument ↔ explanation
   - NO headers for the 2 columns
   Convert this to a markdown table with | separators, NO table headers.
5. **Headers**: Use ## for section headers, **text** for bold, *text* for italic.
6. **Footnotes**: If superscript footnote markers exist, use [^N] in body and [^N]: content at END.
7. **Ignore**: Decorative elements, horizontal bars, ornaments, graphs, diagrams, and figures. Do not describe them—skip them entirely.
8. **CRITICAL**: Output ONLY extracted text. Do NOT repeat or hallucinate content. Do not include any description of images or graphics.
9. If text is unclear, indicate with [unclear] rather than guess.
```

**Orchestrator Workflow:**

1. Create output directory: `mkdir -p ./workspace/ocr_results_vlm`
2. For each page from `{start_page}` to `{end_page}`:
   - Mark corresponding todo `in_progress`
   - Invoke `multimodal-looker` subagent with the page image path
   - Wait for result (sequential execution prevents rate limits)
   - Write the returned OCR text to `./workspace/ocr_results_vlm/page_{NNN}.md`
   - Mark todo `completed`

**Subagent Invocation Pattern:**
```
task(
  subagent_type="multimodal-looker",
  run_in_background=false,
  load_skills=[],
  description="OCR page {page_num}",
  prompt="Read the image at ./workspace/ocr_pages/page_{page_num:03d}.png and perform OCR.

[Insert OCR Prompt above]

Return ONLY the extracted markdown text. Do not write any files - I will save the output."
)
```

After receiving the OCR text from the subagent, the orchestrator writes it to the output file using the `write` tool.

### Step 3: Merge Markdown Pages

Combine all OCR pages into one document:

```bash
python3 $HOME/.config/opencode/skills/critical-thinking-chapter-ocr/scripts/merge_markdown.py \
    ./workspace/ocr_results_vlm \
    ./workspace/ocr_results_vlm/merged_<start>-<end>.md \
    --start <start_page> --end <end_page>
```

**Todo Tracking:**
- Mark "Step 3: Merge pages..." todo `in_progress` before running
- Mark `completed` after merge succeeds

### Step 4: Fix Sentence Continuity (LLM Cleanup)

Use an LLM to fix sentence splits at page boundaries and ensure proper text flow.

**Todo Tracking:**
- Mark "Step 4: Fix sentence continuity..." todo `in_progress` before invoking subagent
- Mark `completed` after cleanup succeeds

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

**Subagent Invocation:**
```
task(
  category="writing",
  run_in_background=false,
  load_skills=[],
  description="Fix sentence continuity",
  prompt="[Insert LLM Cleanup Prompt above]

Read the file at ./workspace/ocr_results_vlm/merged_{start}-{end}.md and output the cleaned version. Write the result back to the same file."
)
``` 

### Step 5: Cross-Check Merged Document (Quality Assurance)

**CRITICAL: This step catches hallucinations, missing content, and repeated text that may have been introduced during cleanup.**

Use the Oracle subagent to cross-check the cleaned merged document against the individual OCR page files.

**Todo Tracking:**
- Mark "Step 5: Cross-check merged doc..." todo `in_progress` before invoking Oracle
- Mark `completed` after verification report is received

**Cross-Check Prompt:**
```
You are a quality assurance reviewer for an OCR textbook project. Your task is to verify the integrity of a cleaned, merged document.

**Input:**
1. Individual OCR page files: ./workspace/ocr_results_vlm/page_{NNN}.md (pages {start}-{end})
2. Cleaned merged document: ./workspace/ocr_results_vlm/merged_{start}-{end}.md

**Your Task:**
1. Read ALL individual OCR page files
2. Read the cleaned merged document
3. Perform a thorough cross-check:

**Check 1: Missing Content**
- Identify any paragraphs, sentences, or content present in individual pages but MISSING from the merged document
- Check each page's content is represented in the merged doc

**Check 2: Hallucinated Content**
- Identify any content in the merged document that does NOT appear in any of the individual page files
- Flag sentences or phrases that seem to have been invented during cleanup

**Check 3: Repeated Content**
- Identify duplicated paragraphs or sentences in the merged document
- Check for content that appears multiple times unnecessarily

**Output Format:**
```
## QA Report

### Missing Content
- [List any missing content with page references, or "None found"]

### Hallucinated Content  
- [List any hallucinated content with specific examples, or "None found"]

### Repeated Content
- [List any duplicated content with locations, or "None found"]

### Overall Assessment
- [PASS / FAIL with reasoning]

### Recommended Fixes
- [If FAIL, list specific fixes needed]
```

**CRITICAL:** Be thorough and precise. Cite specific page numbers and quote relevant text. If you find issues, this report will be used to fix the document.
```

**Subagent Invocation:**
```
task(
  subagent_type="oracle",
  run_in_background=false,
  load_skills=[],
  description="Cross-check merged OCR document",
  prompt="[Insert Cross-Check Prompt above]"
)
```

**After Oracle Report:**
- If Oracle reports **PASS**: Proceed to Step 6
- If Oracle reports **FAIL**: Review the recommended fixes, manually correct the merged document, then optionally re-run this step to verify

### Step 6: Argument Proposition Handling

Update the merged document if it contains argument analysis with proposition in angle brackets like:
- (A) <My client is innocent> because (B) <she was defending herself>

The `<a sentence>` format is used to denote propositions in logical arguments (common in philosophy/logic textbooks). Since Markdown interpret `< >` as HTML tags, these propositions become invisible.

**Solution:** When the angle brackets denote proposition (not HTML), wrap the content in backticks to ensure visibility:
- ✅ (A) `<My client is innocent>` because (B) `<she was defending herself>`

**Todo Tracking:**
- Mark "Step 6: Wrap angle-bracket propositions..." todo `in_progress`
- Use `grep` to find patterns like `(A) <...>` or `(B) <...>`
- Use `edit` tool to wrap propositions in backticks
- Mark `completed` after all propositions are fixed

### Step 7: Rectify Header Levels

Use an LLM to fix header levels based on the book's table of contents structure.

**Todo Tracking:**
- Mark "Step 7: Rectify header levels..." todo `in_progress` before invoking subagent
- Mark `completed` after rectification succeeds

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

**Subagent Invocation:**
```
task(
  category="writing",
  run_in_background=false,
  load_skills=[],
  description="Rectify header levels",
  prompt="[Insert Header Rectification Prompt above]

Read the file at ./workspace/ocr_results_vlm/merged_{start}-{end}.md and output the corrected version. Write the result back to the same file."
)
```

### Step 8: Final Formatting

Apply final formatting fixes to the merged document.

**Todo Tracking:**
- Mark "Step 8: Final formatting..." todo `in_progress`
- Apply formatting rules below
- Mark `completed` after all fixes are applied

**Formatting Rules:**

| Rule | Problem | Solution |
|------|---------|----------|
| Leading `+` character | Markdown renders `+ text` as bullet point | Replace with `&#43;text` (HTML entity) |

**How to Apply:**

1. Use `grep` to find lines starting with `+`:
   ```bash
   grep -n "^+" ./workspace/ocr_results_vlm/merged_*.md
   ```

2. Use `edit` tool to replace:
   - `+ ` at start of line → `&#43; ` (with space after)
   - `+` at start of line (no space) → `&#43;`

**Example:**
```markdown
# Before (renders incorrectly as bullet)
+ This is a sentence that starts with plus.

# After (renders correctly as text)
&#43; This is a sentence that starts with plus.
```

**Note:** Only replace `+` at the **beginning of a line** (after optional whitespace). Do NOT replace `+` in the middle of sentences.

## Scripts

- `scripts/extract_pages.py` - Extract PDF pages as PNG images
- `scripts/merge_markdown.py` - Merge OCR markdown pages into one file

## Example Usage

To OCR and merge pages 78-91 (run from project root):

**0. Create todo list:**
```
todowrite(todos=[
  { content: "Step 1: Extract PDF pages 78-91 to ./workspace/ocr_pages/", status: "pending", priority: "high" },
  { content: "Step 2.1: OCR page 78 — write to ./workspace/ocr_results_vlm/page_078.md", status: "pending", priority: "high" },
  // ... one todo per page 78-91 ...
  { content: "Step 2.14: OCR page 91 — write to ./workspace/ocr_results_vlm/page_091.md", status: "pending", priority: "high" },
  { content: "Step 3: Merge pages to ./workspace/ocr_results_vlm/merged_78-91.md", status: "pending", priority: "high" },
  { content: "Step 4: Fix sentence continuity via writing subagent", status: "pending", priority: "high" },
  { content: "Step 5: Cross-check merged doc against individual OCR files via Oracle subagent", status: "pending", priority: "high" },
  { content: "Step 6: Wrap angle-bracket propositions in backticks", status: "pending", priority: "medium" },
  { content: "Step 7: Rectify header levels via writing subagent", status: "pending", priority: "medium" },
  { content: "Step 8: Final formatting — escape leading + characters", status: "pending", priority: "medium" },
])
```

**1. Extract:** Mark Step 1 todo `in_progress`, run extract script, mark `completed`

**2. OCR:** For each page 78-91:
- Mark page todo `in_progress`
- Invoke `task(subagent_type="multimodal-looker", run_in_background=false, ...)`
- Write result to `./workspace/ocr_results_vlm/page_{NNN}.md`
- Mark todo `completed`

**3. Merge:** Mark Step 3 todo `in_progress`, run merge script, mark `completed`

**4. Cleanup:** Mark Step 4 todo `in_progress`, invoke `task(category="writing", ...)`, mark `completed`

**5. Cross-check:** Mark Step 5 todo `in_progress`, invoke `task(subagent_type="oracle", ...)`, review QA report, apply fixes if needed, mark `completed`

**6. Propositions:** Mark Step 6 todo `in_progress`, use `grep` + `edit` to fix, mark `completed`

**7. Headers:** Mark Step 7 todo `in_progress`, invoke `task(category="writing", ...)`, mark `completed`

**8. Final Formatting:** Mark Step 8 todo `in_progress`, use `grep` to find leading `+`, use `edit` to replace with `&#43;`, mark `completed`
