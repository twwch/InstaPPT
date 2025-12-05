import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from instappt.utils import merge_pdfs_side_by_side
from pypdf import PdfReader

def create_dummy_pdf(filename, text, width=300, height=400):
    c = canvas.Canvas(filename, pagesize=(width, height))
    c.drawString(100, 200, text)
    c.save()

def test_merge_pdfs():
    pdf_a = "test_a.pdf"
    pdf_b = "test_b.pdf"
    output = "test_merged.pdf"
    
    try:
        # Create dummy PDFs
        create_dummy_pdf(pdf_a, "Page A", width=300, height=400)
        create_dummy_pdf(pdf_b, "Page B", width=300, height=400)
        
        # Merge
        merge_pdfs_side_by_side(pdf_a, pdf_b, output)
        
        # Verify
        assert os.path.exists(output), "Output PDF not created"
        
        reader = PdfReader(output)
        assert len(reader.pages) == 1, "Should have 1 page"
        
        page = reader.pages[0]
        # Width should be 300 + 300 = 600
        assert page.mediabox.width == 600, f"Expected width 600, got {page.mediabox.width}"
        # Height should be 400
        assert page.mediabox.height == 400, f"Expected height 400, got {page.mediabox.height}"
        
        print("Test Passed: PDF merged correctly with side-by-side layout.")
        
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        for f in [pdf_a, pdf_b, output]:
            if os.path.exists(f):
                os.remove(f)

if __name__ == "__main__":
    test_merge_pdfs()
