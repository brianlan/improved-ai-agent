#!/usr/bin/env python3

import os
import sys
import argparse
from fpdf import FPDF
from PIL import Image

A4_WIDTH = 210
A4_HEIGHT = 297


def get_image_files(directory):
    valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
    image_files = []
    
    for filename in os.listdir(directory):
        if filename.lower().endswith(valid_extensions):
            image_files.append(filename)
    
    return sorted(image_files)


def calculate_image_placement(img_width, img_height):
    scale_w = A4_WIDTH / img_width
    scale_h = A4_HEIGHT / img_height
    scale = max(scale_w, scale_h)
    
    scaled_w = img_width * scale
    scaled_h = img_height * scale
    x = (A4_WIDTH - scaled_w) / 2
    y = (A4_HEIGHT - scaled_h) / 2
    
    return x, y, scaled_w, scaled_h


def convert_images_to_pdf(input_dir, output_pdf, paper_size='A4'):
    global A4_WIDTH, A4_HEIGHT
    
    if paper_size.upper() == 'A4':
        A4_WIDTH = 210
        A4_HEIGHT = 297
    elif paper_size.upper() == 'LETTER':
        A4_WIDTH = 215.9
        A4_HEIGHT = 279.4
    else:
        raise ValueError(f"Unsupported paper size: {paper_size}")
    
    image_files = get_image_files(input_dir)
    
    if not image_files:
        print(f"No image files found in {input_dir}")
        return False
    
    print(f"Found {len(image_files)} images")
    
    pdf = FPDF(orientation='portrait', unit='mm', format=paper_size.upper())
    pdf.set_auto_page_break(auto=True, margin=0)
    
    for image_file in image_files:
        image_path = os.path.join(input_dir, image_file)
        
        with Image.open(image_path) as img:
            img_width, img_height = img.size
        
        x, y, scaled_w, scaled_h = calculate_image_placement(img_width, img_height)
        
        pdf.add_page()
        pdf.image(image_path, x=x, y=y, w=scaled_w, h=scaled_h)
        
        print(f"Added: {image_file}")
    
    pdf.output(output_pdf)
    print(f"PDF saved to: {output_pdf}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Convert a directory of images to a PDF file.'
    )
    parser.add_argument('input_dir', help='Directory containing images')
    parser.add_argument('output_pdf', help='Output PDF file path')
    parser.add_argument(
        '--paper-size',
        default='A4',
        choices=['A4', 'Letter'],
        help='Paper size (default: A4)'
    )
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.input_dir):
        print(f"Error: Input directory does not exist: {args.input_dir}")
        sys.exit(1)
    
    output_dir = os.path.dirname(args.output_pdf)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    success = convert_images_to_pdf(args.input_dir, args.output_pdf, args.paper_size)
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
