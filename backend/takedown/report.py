from io import BytesIO

from reportlab.pdfgen import canvas


def create_report(title: str, details: str) -> bytes:
    output = BytesIO()
    pdf = canvas.Canvas(output)
    pdf.setTitle(title)
    pdf.drawString(72, 760, title)
    pdf.setFont("Helvetica", 10)
    for index, line in enumerate(details.splitlines() or [details]):
        pdf.drawString(72, 735 - index * 14, line[:110])
        if 735 - index * 14 < 72:
            break
    pdf.save()
    return output.getvalue()
