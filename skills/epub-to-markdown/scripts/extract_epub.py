#!/usr/bin/env python3
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from html.parser import HTMLParser
from typing import List, Tuple, Optional


class HTMLToMarkdownConverter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.markdown_parts = []
        self.current_text = []
        self.in_script = False
        self.in_style = False
        self.skip_content = False
        self.list_stack = []
        self.link_href = None
        self.link_text = []
        self.in_link = False
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag in ('script', 'style'):
            if tag == 'script':
                self.in_script = True
            else:
                self.in_style = True
            return
            
        if tag in ('nav',):
            self.skip_content = True
            return
            
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self._flush_text()
            level = int(tag[1])
            self.markdown_parts.append('\n' + '#' * level + ' ')
            
        elif tag == 'p':
            self._flush_text()
            self.markdown_parts.append('\n\n')
            
        elif tag in ('em', 'i'):
            self.current_text.append('*')
        elif tag in ('strong', 'b'):
            self.current_text.append('**')
            
        elif tag == 'a':
            self.in_link = True
            self.link_href = attrs_dict.get('href', '')
            self.link_text = []
            
        elif tag == 'ul':
            self._flush_text()
            self.list_stack.append('ul')
        elif tag == 'ol':
            self._flush_text()
            self.list_stack.append('ol')
            self.list_counter = 1
        elif tag == 'li':
            self._flush_text()
            indent = '  ' * (len(self.list_stack) - 1)
            if self.list_stack and self.list_stack[-1] == 'ul':
                self.markdown_parts.append(f'\n{indent}- ')
            else:
                self.markdown_parts.append(f'\n{indent}{self.list_counter}. ')
                self.list_counter += 1
                
        elif tag == 'blockquote':
            self._flush_text()
            self.markdown_parts.append('\n\n> ')
            
        elif tag == 'br':
            self.current_text.append('\n')
            
        elif tag == 'table':
            self._flush_text()
            self.markdown_parts.append('\n\n')
        elif tag == 'tr':
            self._flush_text()
            self.in_table_row = True
            self.table_cells = []
        elif tag in ('td', 'th'):
            self._flush_text()
            self.in_table_cell = True
            self.current_cell_text = []
            if tag == 'th':
                self.is_header_row = True
                
    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_script = False
            return
        elif tag == 'style':
            self.in_style = False
            return
        elif tag in ('nav',):
            self.skip_content = False
            return
            
        if self.in_script or self.in_style or self.skip_content:
            return
            
        if tag in ('em', 'i'):
            self.current_text.append('*')
        elif tag in ('strong', 'b'):
            self.current_text.append('**')
            
        elif tag == 'a':
            if self.in_link:
                link_text = ''.join(self.link_text).strip()
                if link_text and self.link_href and not self.link_href.startswith('#'):
                    self.current_text.append(f'[{link_text}]({self.link_href})')
                else:
                    self.current_text.append(link_text)
                self.in_link = False
                self.link_href = None
                self.link_text = []
                
        elif tag in ('ul', 'ol'):
            if self.list_stack:
                self.list_stack.pop()
            self._flush_text()
            self.markdown_parts.append('\n')
            
        elif tag == 'tr':
            self._flush_text()
            if hasattr(self, 'table_cells') and self.table_cells:
                row = '| ' + ' | '.join(self.table_cells) + ' |'
                self.markdown_parts.append(row + '\n')
                if hasattr(self, 'is_header_row') and self.is_header_row:
                    sep = '|' + '|'.join(['---'] * len(self.table_cells)) + '|'
                    self.markdown_parts.append(sep + '\n')
                    self.is_header_row = False
                    
        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self._flush_text()
            self.markdown_parts.append('\n')
            
        elif tag == 'blockquote':
            self._flush_text()
            self.markdown_parts.append('\n\n')
            
        elif tag == 'p':
            self._flush_text()
            self.markdown_parts.append('\n\n')
            
    def handle_data(self, data):
        if self.in_script or self.in_style or self.skip_content:
            return
            
        text = data.replace('\n', ' ').replace('\r', '').replace('\t', ' ')
        text = ' '.join(text.split())
        
        if text:
            if self.in_link:
                self.link_text.append(text)
            else:
                self.current_text.append(text)
                
    def _flush_text(self):
        if self.current_text:
            text = ''.join(self.current_text)
            text = ' '.join(text.split())
            if text:
                self.markdown_parts.append(text)
            self.current_text = []
            
    def get_markdown(self) -> str:
        self._flush_text()
        markdown = ''.join(self.markdown_parts)
        markdown = re.sub(r'\n{4,}', '\n\n\n', markdown)
        return markdown.strip()


def parse_opf_file(opf_path: Path) -> List[Tuple[str, str]]:
    tree = ET.parse(opf_path)
    root = tree.getroot()
    
    ns = {'opf': 'http://www.idpf.org/2007/opf'}
    
    manifest = {}
    manifest_elem = root.find('opf:manifest', ns)
    if manifest_elem is not None:
        for item in manifest_elem.findall('opf:item', ns):
            item_id = item.get('id')
            href = item.get('href')
            if item_id and href:
                manifest[item_id] = href
    
    reading_order = []
    spine = root.find('opf:spine', ns)
    if spine is not None:
        for itemref in spine.findall('opf:itemref', ns):
            idref = itemref.get('idref')
            if idref and idref in manifest:
                reading_order.append((idref, manifest[idref]))
    
    return reading_order


def find_opf_file(epub_dir: Path) -> Optional[Path]:
    possible_paths = [
        epub_dir / 'ops' / '*.opf',
        epub_dir / 'OEBPS' / '*.opf',
        epub_dir / '*.opf',
        epub_dir / '**' / '*.opf',
    ]
    
    for pattern in possible_paths:
        matches = list(epub_dir.glob(str(pattern.relative_to(epub_dir) if pattern.is_absolute() else pattern)))
        if matches:
            return matches[0]
    
    return None


def extract_html_content(html_path: Path) -> str:
    try:
        content = html_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        content = html_path.read_text(encoding='latin-1')
    
    converter = HTMLToMarkdownConverter()
    converter.feed(content)
    return converter.get_markdown()


def extract_epub_to_markdown(epub_dir: str, output_file: str, skip_linear_no: bool = True):
    epub_path = Path(epub_dir).resolve()
    output_path = Path(output_file).resolve()
    
    opf_path = find_opf_file(epub_path)
    if not opf_path:
        print(f"Error: Could not find OPF file in {epub_dir}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found OPF file: {opf_path}")
    
    reading_order = parse_opf_file(opf_path)
    if not reading_order:
        print(f"Error: Could not determine reading order from {opf_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(reading_order)} documents in reading order")
    
    html_base = opf_path.parent
    
    markdown_parts = []
    
    for idref, href in reading_order:
        html_path = html_base / href
        
        if not html_path.exists():
            print(f"Warning: File not found: {html_path}", file=sys.stderr)
            continue
        
        print(f"Processing: {href}")
        
        content = extract_html_content(html_path)
        if content.strip():
            if markdown_parts:
                markdown_parts.append('\n\n---\n\n')
            markdown_parts.append(content)
    
    full_markdown = '\n'.join(markdown_parts)
    full_markdown = re.sub(r'\n{5,}', '\n\n\n\n', full_markdown)
    
    output_path.write_text(full_markdown, encoding='utf-8')
    print(f"\nSuccessfully extracted to: {output_path}")
    print(f"Total length: {len(full_markdown)} characters")


def main():
    parser = argparse.ArgumentParser(
        description='Extract EPUB HTML files to a single markdown document'
    )
    parser.add_argument(
        'epub_dir',
        help='Path to the EPUB extraction directory'
    )
    parser.add_argument(
        '-o', '--output',
        default='book.md',
        help='Output markdown file path (default: book.md)'
    )
    parser.add_argument(
        '--include-all',
        action='store_true',
        help='Include all files, even those marked as linear="no"'
    )
    
    args = parser.parse_args()
    
    extract_epub_to_markdown(
        args.epub_dir,
        args.output,
        skip_linear_no=not args.include_all
    )


if __name__ == '__main__':
    main()
