---
name: critical-thinking-fix-page
description: Fix or insert a specific page in an OCR'd merged markdown document by re-processing with customized OCR rules. Use after critical-thinking-chapter-ocr to correct problematic pages or add missing pages. Takes the merged .md file, source PDF, page number N, custom OCR rules, and operation type (fix/insert) as input. Re-OCR pages N-1, N, N+1 with the target page using special rules, then surgically replace or insert content in the merged document. Use when: (1) A specific page has OCR errors, (2) Tables or special layouts were incorrectly extracted, (3) Content needs re-extraction with different rules, (4) A page is missing from the merged document, (5) Fixing issues identified during review of critical-thinking-chapter-ocr output.
---

# Critical Thinking Fix Page

Re-process a specific page in an OCR'd merged document with customized OCR rules, then surgically replace (fix) or insert (missing page) the content while maintaining continuity with adjacent pages.

## Prerequisites

```bash
pip install pymupdf
```

## Input Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `merged_md_path` | string | Path to the merged .md file from critical-thinking-chapter-ocr |
| `pdf_path` | string | Path to the source PDF textbook |
| `page_number` | integer | The page number N to fix or insert (1-indexed PDF page) |
| `custom_ocr_rule` | string | Custom OCR rules to apply to page N (string, not file path) |
| `operation` | string | `"fix"` (default) or `"insert"`. Fix replaces existing page N content; insert adds missing page N between N-1 and N+1 |

## Workflow

### MANDATORY: Create Todo List First

**Before starting any work, create a comprehensive todo list using `todowrite`.**

**Full Workflow Todo Template:**
```
todowrite(todos=[
  { content: "Step 1: Create backup of merged document", status: "pending", priority: "high" },
  { content: "Step 2: Extract PDF pages N-1, N, N+1 to ./workspace/fix_page/", status: "pending", priority: "high" },
  { content: "Step 3.1: OCR page N-1 (previous page) — standard rules", status: "pending", priority: "high" },
  { content: "Step 3.2: OCR page N (target page) — custom rules + standard rules", status: "pending", priority: "high" },
  { content: "Step 3.3: OCR page N+1 (next page) — standard rules", status: "pending", priority: "high" },
  { content: "Step 4: Oracle identifies page N boundaries/insertion point (operation: fix/insert)", status: "pending", priority: "high" },
  { content: "Step 5: Replace/Insert page N content in merged document", status: "pending", priority: "high" },
  { content: "Step 6: Verify continuity with adjacent pages", status: "pending", priority: "medium" },
])
```

---

### Step 1: Create Backup

**ALWAYS create a backup before modifying the merged document.**

```bash
cp <merged_md_path> "<merged_md_path>.bak"
```

**Example:**
```bash
cp ./workspace/ocr_results_vlm/merged_78-91.md "./workspace/ocr_results_vlm/merged_78-91.md.bak"
```

**Todo Tracking:**
- Mark "Step 1: Create backup..." todo `in_progress` before running
- Mark `completed` after backup succeeds

---

### Step 2: Extract PDF Pages

Extract pages N-1, N, and N+1 as PNG images at 150 DPI.

**Edge Case Handling:**
- If N=1 (first page), skip N-1 extraction
- If N is the last page, skip N+1 extraction
- Determine available pages dynamically

```bash
python3 $HOME/.config/opencode/skills/critical-thinking-fix-page/scripts/extract_pages.py \
    <pdf_path> <start_page> <end_page> ./workspace/fix_page
```

**Example (fixing page 85):**
```bash
# Extract pages 84, 85, 86
python3 $HOME/.config/opencode/skills/critical-thinking-fix-page/scripts/extract_pages.py \
    /path/to/book.pdf 84 86 ./workspace/fix_page
```

**Edge Case (fixing page 1):**
```bash
# Only extract pages 1, 2 (skip N-1 which doesn't exist)
python3 $HOME/.config/opencode/skills/critical-thinking-fix-page/scripts/extract_pages.py \
    /path/to/book.pdf 1 2 ./workspace/fix_page
```

**Todo Tracking:**
- Mark "Step 2: Extract PDF pages..." todo `in_progress` before running
- Mark `completed` after extraction succeeds

---

### Step 3: OCR Pages with VLM Subagent

**IMPORTANT: The `multimodal-looker` subagent can only READ files. The orchestrating agent must coordinate page-by-page OCR calls and write the output files.**

Call `multimodal-looker` **sequentially, one page at a time** to avoid rate limits.

#### Standard OCR Prompt (for pages N-1 and N+1)

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

#### Custom OCR Prompt (for page N)

Combine the standard OCR prompt with the custom rule:

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

--- CUSTOM RULES FOR THIS PAGE ---

{custom_ocr_rule}
```

#### Subagent Invocation Pattern

**For page N-1 (standard rules):**
```
task(
  subagent_type="multimodal-looker",
  run_in_background=false,
  load_skills=[],
  description="OCR page N-1",
  prompt="Read the image at ./workspace/fix_page/page_{N-1:03d}.png and perform OCR.

[Insert Standard OCR Prompt above]

Return ONLY the extracted markdown text. Do not write any files - I will save the output."
)
```

**For page N (custom rules):**
```
task(
  subagent_type="multimodal-looker",
  run_in_background=false,
  load_skills=[],
  description="OCR page N with custom rules",
  prompt="Read the image at ./workspace/fix_page/page_{N:03d}.png and perform OCR.

[Insert Custom OCR Prompt above with custom_ocr_rule substituted]

Return ONLY the extracted markdown text. Do not write any files - I will save the output."
)
```

**For page N+1 (standard rules):**
```
task(
  subagent_type="multimodal-looker",
  run_in_background=false,
  load_skills=[],
  description="OCR page N+1",
  prompt="Read the image at ./workspace/fix_page/page_{N+1:03d}.png and perform OCR.

[Insert Standard OCR Prompt above]

Return ONLY the extracted markdown text. Do not write any files - I will save the output."
)
```

#### Orchestrator Workflow

1. Create output directory: `mkdir -p ./workspace/fix_page_ocr`
2. For each page to OCR:
   - Mark corresponding todo `in_progress`
   - Invoke `multimodal-looker` subagent with appropriate prompt
   - Wait for result (sequential execution)
   - Write the returned OCR text to `./workspace/fix_page_ocr/page_{NNN}.md`
   - Mark todo `completed`

---

### Step 4: Oracle Identifies Page Boundaries

**Use the Oracle subagent to analyze the merged document and identify boundaries based on the operation type.**

**Todo Tracking:**
- Mark "Step 4: Oracle identifies page N boundaries/insertion point..." todo `in_progress`
- Mark `completed` after Oracle returns the boundary information

#### Fix Mode: Find Existing Page N Boundaries

**Use when `operation="fix"` to find the line range of existing page N content.**

**Oracle Prompt (Fix Mode):**
```
You are a document analysis expert. Your task is to identify the exact content boundaries of a specific page in a merged OCR document.

**Operation:** FIX - Replace existing page content

**Context:**
- A merged markdown document was created from multiple OCR'd PDF pages
- We need to locate and replace the content from page {N}
- We have fresh OCR results for pages {N-1}, {N}, and {N+1} to help identify boundaries

**Inputs:**
1. Merged document path: {merged_md_path}
2. Page N OCR result: ./workspace/fix_page_ocr/page_{N:03d}.md
3. Page N-1 OCR result: ./workspace/fix_page_ocr/page_{N-1:03d}.md (if exists)
4. Page N+1 OCR result: ./workspace/fix_page_ocr/page_{N+1:03d}.md (if exists)

**Your Task:**
1. Read the merged document
2. Read the OCR results for pages N-1, N, N+1
3. Use the OCR content to identify where page N's content starts and ends in the merged document:
   - Find the END of page N-1 content in the merged document (use unique text fingerprints)
   - Find the START of page N+1 content in the merged document (use unique text fingerprints)
   - The content between these boundaries is page N's content
4. Return the exact line numbers and a short excerpt for verification

**Output Format:**
```
## Page Boundary Analysis (FIX Mode)

### Page N-1 End (if applicable)
- Last unique phrase from page N-1 OCR: "[quote]"
- Found in merged document at line: [line_number]
- Excerpt context: "...[context]..."

### Page N+1 Start (if applicable)
- First unique phrase from page N+1 OCR: "[quote]"
- Found in merged document at line: [line_number]
- Excerpt context: "...[context]..."

### Page N Content Range
- Start line: [start_line] (inclusive)
- End line: [end_line] (inclusive)
- Content to replace: [number of lines]

### Verification Excerpt
First 3 lines of page N content in merged doc:
```
[line_content]
[line_content]
[line_content]
```

Last 3 lines of page N content in merged doc:
```
[line_content]
[line_content]
[line_content]
```
```

**CRITICAL:** Be precise with line numbers. These will be used to surgically replace content. If boundaries are unclear, state the ambiguity and provide your best estimate with confidence level.
```

---

#### Insert Mode: Find Insertion Point

**Use when `operation="insert"` to find where to insert the missing page N content.**

**Oracle Prompt (Insert Mode):**
```
You are a document analysis expert. Your task is to identify the insertion point for a missing page in a merged OCR document.

**Operation:** INSERT - Add missing page content

**Context:**
- A merged markdown document was created from multiple OCR'd PDF pages
- Page {N} is MISSING from the merged document
- We need to find the exact insertion point between page N-1 and page N+1
- We have fresh OCR results for pages N-1, N, and N+1

**Inputs:**
1. Merged document path: {merged_md_path}
2. Page N OCR result (the missing page to insert): ./workspace/fix_page_ocr/page_{N:03d}.md
3. Page N-1 OCR result: ./workspace/fix_page_ocr/page_{N-1:03d}.md (if exists)
4. Page N+1 OCR result: ./workspace/fix_page_ocr/page_{N+1:03d}.md (if exists)

**Your Task:**
1. Read the merged document
2. Read the OCR results for pages N-1, N, N+1
3. Find the insertion point:
   - Locate the END of page N-1 content in the merged document (use unique text fingerprints from N-1 OCR)
   - Locate the START of page N+1 content in the merged document (use unique text fingerprints from N+1 OCR)
   - The insertion point is AFTER page N-1 content ends and BEFORE page N+1 content starts
4. Verify that page N content is indeed missing (not present in the merged document)
5. Return the exact line number for insertion

**Output Format:**
```
## Insertion Point Analysis (INSERT Mode)

### Page N-1 End (if applicable)
- Last unique phrase from page N-1 OCR: "[quote]"
- Found in merged document at line: [line_number]
- Excerpt context: "...[context]..."

### Page N+1 Start (if applicable)
- First unique phrase from page N+1 OCR: "[quote]"
- Found in merged document at line: [line_number]
- Excerpt context: "...[context]..."

### Insertion Point
- Insert AFTER line: [line_number] (insert new content after this line)
- Insert BEFORE line: [line_number] (the start of page N+1 content)

### Missing Page Verification
- Page N content found in merged doc: [NO / YES - if YES, abort and report error]
- First unique phrase from page N OCR: "[quote]"

### Verification Excerpt
Last 3 lines before insertion point:
```
[line_content]
[line_content]
[line_content]
```

First 3 lines after insertion point (should be page N+1 content):
```
[line_content]
[line_content]
[line_content]
```
```

**CRITICAL:** 
1. Verify that page N content is NOT already in the merged document. If found, this should be a FIX operation, not INSERT.
2. Be precise with line numbers. Content will be inserted between these lines.
```

---

**Subagent Invocation:**
```
task(
  subagent_type="oracle",
  run_in_background=false,
  load_skills=[],
  description="Identify page N boundaries [{operation} mode]",
  prompt="[Insert appropriate Oracle Prompt above based on operation type]"
)
```

---

### Step 5: Replace or Insert Page N Content

Using the boundary information from Oracle, apply the new page N content based on the operation type.

**Todo Tracking:**
- Mark "Step 5: Replace/Insert page N content..." todo `in_progress`
- Mark `completed` after the operation succeeds

---

#### Fix Mode: Replace Existing Content

**Use when `operation="fix"` to replace the existing page N content.**

**Replacement Strategy:**

1. **Read the merged document** using `read` tool
2. **Extract lines** outside the replacement range
3. **Construct new document**:
   - Lines 1 to (start_line - 1) from merged doc
   - New page N content from `./workspace/fix_page_ocr/page_{N:03d}.md`
   - Lines (end_line + 1) onwards from merged doc
4. **Write the updated document** back to the merged file

**Implementation:**

```python
# Pseudo-code for FIX mode:

# 1. Read merged document
merged_content = read(merged_md_path)

# 2. Read new page N OCR
new_page_content = read("./workspace/fix_page_ocr/page_{N:03d}.md")

# 3. Split merged document into lines
lines = merged_content.split('\n')

# 4. Extract content before and after page N
before_page_n = '\n'.join(lines[:start_line - 1])
after_page_n = '\n'.join(lines[end_line:])

# 5. Construct new merged document
new_merged = before_page_n + '\n\n' + new_page_content + '\n\n' + after_page_n

# 6. Write back
write(merged_md_path, new_merged)
```

**Use `edit` tool for replacement:**
- Old content: lines from start_line to end_line in merged doc
- New content: fresh OCR from page_N.md

---

#### Insert Mode: Insert New Content

**Use when `operation="insert"` to insert the missing page N content.**

**Insertion Strategy:**

1. **Read the merged document** using `read` tool
2. **Find the insertion point** (the line after page N-1 content ends)
3. **Construct new document**:
   - Lines 1 to insertion_line from merged doc
   - New page N content from `./workspace/fix_page_ocr/page_{N:03d}.md`
   - Lines (insertion_line + 1) onwards from merged doc
4. **Write the updated document** back to the merged file

**Implementation:**

```python
# Pseudo-code for INSERT mode:

# 1. Read merged document
merged_content = read(merged_md_path)

# 2. Read new page N OCR
new_page_content = read("./workspace/fix_page_ocr/page_{N:03d}.md")

# 3. Split merged document into lines
lines = merged_content.split('\n')

# 4. Extract content before and after insertion point
# insertion_line is the line AFTER which we insert (from Oracle's "Insert AFTER line")
before_insertion = '\n'.join(lines[:insertion_line])
after_insertion = '\n'.join(lines[insertion_line:])

# 5. Construct new merged document with inserted page
new_merged = before_insertion + '\n\n' + new_page_content + '\n\n' + after_insertion

# 6. Write back
write(merged_md_path, new_merged)
```

**Use `edit` tool for insertion:**
- Find the unique phrase at the end of page N-1 (from Oracle report)
- Insert new content after that phrase

---

#### Operation Summary

| Operation | Action | Lines Affected |
|-----------|--------|----------------|
| `fix` | Replace | Delete lines [start, end], insert new content |
| `insert` | Insert | Insert new content at insertion point (no deletion) |

---

### Step 6: Verify Continuity

**Use Oracle to verify the replacement maintains proper sentence flow.**

**Todo Tracking:**
- Mark "Step 6: Verify continuity..." todo `in_progress`
- Mark `completed` after verification passes

**Verification Prompt:**
```
You are a document quality reviewer. Verify that a recently modified page maintains proper continuity with adjacent pages.

**Inputs:**
1. Updated merged document: {merged_md_path}
2. Page N-1 OCR result: ./workspace/fix_page_ocr/page_{N-1:03d}.md (if exists)
3. Page N OCR result: ./workspace/fix_page_ocr/page_{N:03d}.md
4. Page N+1 OCR result: ./workspace/fix_page_ocr/page_{N+1:03d}.md (if exists)

**Your Task:**
1. Read the updated merged document
2. Focus on the transitions:
   - End of page N-1 → Start of page N
   - End of page N → Start of page N+1
3. Check for:
   - **Sentence continuity**: No broken sentences at boundaries
   - **No duplicated content**: Content from one page doesn't appear in adjacent pages
   - **No missing content**: All OCR content from pages N-1, N, N+1 appears in the merged doc
   - **Proper formatting**: Headers, tables, footnotes are intact

**Output Format:**
```
## Continuity Verification

### Page N-1 → Page N Transition
- Status: [GOOD / ISSUE]
- Last sentence of N-1: "[quote]"
- First sentence of N: "[quote]"
- Issue (if any): [description or "None"]

### Page N → Page N+1 Transition
- Status: [GOOD / ISSUE]
- Last sentence of N: "[quote]"
- First sentence of N+1: "[quote]"
- Issue (if any): [description or "None"]

### Overall Assessment
- [PASS / FAIL]
- Summary: [brief summary]
```
```

**Subagent Invocation:**
```
task(
  subagent_type="oracle",
  run_in_background=false,
  load_skills=[],
  description="Verify page continuity",
  prompt="[Insert Verification Prompt above]"
)
```

**If verification fails:** Review the issues, manually fix, or restore from backup and retry.

---

## Example Usage

### Example 1: Fix Mode (Replace Existing Page)

**Scenario:** Page 85 in the merged document (pages 78-91) has a table that was incorrectly OCR'd. Need to re-process with custom rules for table extraction.

**Parameters:**
- `merged_md_path`: `./workspace/ocr_results_vlm/merged_78-91.md`
- `pdf_path`: `/path/to/CriticalThinking.pdf`
- `page_number`: `85`
- `custom_ocr_rule`: `"The table on this page is an argument analysis. Each row has: (1) argument label, (2) premises, (3) conclusion. Extract as markdown table with columns: Argument | Premises | Conclusion"`
- `operation`: `"fix"` (default)

**Workflow Execution:**

```
// 0. Create todos
todowrite(todos=[
  { content: "Step 1: Create backup of ./workspace/ocr_results_vlm/merged_78-91.md", ... },
  { content: "Step 2: Extract PDF pages 84-86 to ./workspace/fix_page/", ... },
  { content: "Step 3.1: OCR page 84 — standard rules", ... },
  { content: "Step 3.2: OCR page 85 — custom table rules", ... },
  { content: "Step 3.3: OCR page 86 — standard rules", ... },
  { content: "Step 4: Oracle identifies page 85 boundaries [fix mode]", ... },
  { content: "Step 5: Replace page 85 content in merged doc", ... },
  { content: "Step 6: Verify continuity with pages 84 and 86", ... },
])

// 1. Backup
cp ./workspace/ocr_results_vlm/merged_78-91.md "./workspace/ocr_results_vlm/merged_78-91.md.bak"

// 2. Extract pages
python3 $HOME/.config/opencode/skills/critical-thinking-fix-page/scripts/extract_pages.py \
    /path/to/CriticalThinking.pdf 84 86 ./workspace/fix_page

// 3. OCR pages (sequential)
task(subagent_type="multimodal-looker", run_in_background=false, description="OCR page 84", prompt="...")
task(subagent_type="multimodal-looker", run_in_background=false, description="OCR page 85", prompt="...with custom rules...")
task(subagent_type="multimodal-looker", run_in_background=false, description="OCR page 86", prompt="...")

// 4. Oracle identifies boundaries (fix mode)
task(subagent_type="oracle", run_in_background=false, description="Identify page 85 boundaries [fix mode]", prompt="...")

// 5. Replace content (using edit tool based on Oracle's line numbers)

// 6. Verify continuity
task(subagent_type="oracle", run_in_background=false, description="Verify continuity", prompt="...")
```

---

### Example 2: Insert Mode (Add Missing Page)

**Scenario:** Page 82 was accidentally skipped during the original OCR process. The merged document jumps from page 81 content directly to page 83 content. Need to insert the missing page.

**Parameters:**
- `merged_md_path`: `./workspace/ocr_results_vlm/merged_78-91.md`
- `pdf_path`: `/path/to/CriticalThinking.pdf`
- `page_number`: `82`
- `custom_ocr_rule`: `""` (empty string - use standard rules only)
- `operation`: `"insert"`

**Workflow Execution:**

```
// 0. Create todos
todowrite(todos=[
  { content: "Step 1: Create backup of ./workspace/ocr_results_vlm/merged_78-91.md", ... },
  { content: "Step 2: Extract PDF pages 81-83 to ./workspace/fix_page/", ... },
  { content: "Step 3.1: OCR page 81 — standard rules", ... },
  { content: "Step 3.2: OCR page 82 — standard rules (missing page)", ... },
  { content: "Step 3.3: OCR page 83 — standard rules", ... },
  { content: "Step 4: Oracle identifies insertion point [insert mode]", ... },
  { content: "Step 5: Insert page 82 content in merged doc", ... },
  { content: "Step 6: Verify continuity with pages 81 and 83", ... },
])

// 1. Backup
cp ./workspace/ocr_results_vlm/merged_78-91.md "./workspace/ocr_results_vlm/merged_78-91.md.bak"

// 2. Extract pages
python3 $HOME/.config/opencode/skills/critical-thinking-fix-page/scripts/extract_pages.py \
    /path/to/CriticalThinking.pdf 81 83 ./workspace/fix_page

// 3. OCR pages (sequential)
task(subagent_type="multimodal-looker", run_in_background=false, description="OCR page 81", prompt="...")
task(subagent_type="multimodal-looker", run_in_background=false, description="OCR page 82", prompt="...")
task(subagent_type="multimodal-looker", run_in_background=false, description="OCR page 83", prompt="...")

// 4. Oracle identifies insertion point (insert mode)
// Oracle will verify page 82 content is NOT in merged doc, then find insertion point
task(subagent_type="oracle", run_in_background=false, description="Identify insertion point [insert mode]", prompt="...")

// 5. Insert content at the identified insertion point (no deletion)

// 6. Verify continuity
task(subagent_type="oracle", run_in_background=false, description="Verify continuity", prompt="...")
```

---

## Notes

- **Backup is automatic**: Always created in Step 1, can be restored if needed
- **Edge pages handled**: If N=1 or N=last page, adjacent pages are skipped
- **Custom rules are additive**: Custom rules are appended to standard OCR rules, not replacing them
- **Sequential OCR**: Must call multimodal-looker one page at a time to avoid rate limits
- **Oracle for precision**: Using Oracle ensures accurate boundary detection for surgical operations
- **Operation modes**:
  - `fix` (default): Replaces existing page N content — Oracle finds start/end lines, content is swapped
  - `insert`: Adds missing page N — Oracle finds insertion point, content is inserted without deletion
- **Insert mode verification**: Oracle verifies the page is actually missing before allowing insert (prevents duplicates)
