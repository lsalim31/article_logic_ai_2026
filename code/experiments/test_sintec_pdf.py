#!/usr/bin/env python3
"""
Test script to run logify2.py on SINTEC NDA PDF document.

Usage:
    python test_sintec_pdf.py <api_key>
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import logify2
sys.path.insert(0, str(Path(__file__).parent.parent / 'from_text_to_logic'))

from logify2 import LogifyConverter2

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_sintec_pdf.py <api_key>")
        return 1

    api_key = sys.argv[1]

    # Paths
    pdf_path = Path(__file__).parent / "SINTEC-UK-LTD-Non-disclosure-agreement-2017.pdf"
    output_path = Path(__file__).parent / "SINTEC-output.json"

    print("="*60)
    print("Testing logify2.py on SINTEC NDA PDF")
    print("="*60)
    print(f"PDF: {pdf_path}")
    print(f"Output: {output_path}")
    print(f"Model: gpt-5.2 (temperature: 0.1, max_tokens: 64000, reasoning_effort: high)")
    print("="*60 + "\n")

    try:
        # Import and extract text
        from logify2 import extract_text_from_document

        print("Step 1: Extracting text from PDF...")
        text = extract_text_from_document(str(pdf_path))
        print(f"  ✓ Extracted {len(text)} characters\n")

        # Initialize converter with custom parameters for enhanced reasoning and larger output budget
        print("Step 2: Initializing logify2 pipeline...")
        converter = LogifyConverter2(
            api_key=api_key,
            model="gpt-5.2",
            temperature=0.1,
            max_tokens=64000,        # Doubled output budget for complex documents
            reasoning_effort="high"  # Enhanced reasoning quality
        )
        print("  ✓ Pipeline initialized\n")

        # Convert to logic
        print("Step 3: Converting to logic structure...")
        logic_structure = converter.convert_text_to_logic(text)
        print("  ✓ Conversion complete\n")

        # Save output
        print("Step 4: Saving output...")
        converter.save_output(logic_structure, str(output_path))
        print(f"  ✓ Output saved to: {output_path}\n")

        print("="*60)
        print("SUCCESS: Test completed!")
        print("="*60)

        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
