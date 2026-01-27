#!/bin/bash
# Script to integrate the logic_solver appendix section

echo "Integrating logic_solver appendix section..."

# Backup original appendix
cp /workspace/repo/article/appendix.tex /workspace/repo/article/appendix.tex.backup

# Add the new section at the end
echo "" >> /workspace/repo/article/appendix.tex
echo "% Logic Solver Implementation Details" >> /workspace/repo/article/appendix.tex
echo "\input{appendix_logic_solver}" >> /workspace/repo/article/appendix.tex

echo "✓ Added logic_solver section to appendix.tex"
echo "✓ Backup created: appendix.tex.backup"
echo ""
echo "Next steps:"
echo "1. Compile the document:"
echo "   cd /workspace/repo/article"
echo "   pdflatex main_text.tex"
echo "   bibtex main_text"
echo "   pdflatex main_text.tex"
echo "   pdflatex main_text.tex"
echo ""
echo "2. Verify citations appear correctly in the PDF"
echo "3. Check that section numbering is correct"
echo ""
echo "New citations added to biblio.bib:"
echo "  - ignatiev2019rc2 (RC2 MaxSAT solver)"
echo "  - audemard2009glucose (Glucose SAT solver)"
