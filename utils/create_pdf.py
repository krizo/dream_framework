import tempfile

from fpdf import FPDF
import random
import os

def generate_test_pdf(file_name="policy_document.pdf", pages=2):
    """
    Generate a test PDF file with Lorem Ipsum content in the system temp directory.

    @param file_name: Name of the PDF file to create
    @param pages: Number of pages to generate
    @return: Path to the generated file
    """
    # Create a temporary directory for our test files
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, file_name)

    # Sample Lorem Ipsum paragraphs
    lorem_paragraphs = [
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
        "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
        "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
        "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium.",
        "Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores.",
        "Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit.",
        "Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur."
    ]

    # Create PDF object
    pdf = FPDF()

    # Add pages with random content
    for i in range(pages):
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Add a title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"Test Document - Page {i+1}", ln=True, align='C')
        pdf.ln(10)

        # Add random paragraphs
        pdf.set_font("Arial", size=12)
        for _ in range(random.randint(3, 6)):
            paragraph = random.choice(lorem_paragraphs)
            pdf.multi_cell(0, 10, paragraph)
            pdf.ln(5)

    # Save the PDF
    pdf.output(file_path)
    return file_path

if __name__ == "__main__":
    # Generate a test PDF file
    pdf_path = generate_test_pdf()
    print(f"Generated test PDF at: {pdf_path}")

    # Generate multiple test files with random content
    test_files = []
    for i in range(1, 4):
        file_path = f"test_data/example{i}.pdf"
        pages = random.randint(1, 5)
        test_files.append(generate_test_pdf(file_path, pages))

    print(f"Generated {len(test_files)} additional test PDF files")