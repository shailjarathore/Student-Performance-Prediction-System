from flask import Blueprint, request, jsonify, send_file
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
import datetime

report_bp = Blueprint('report', __name__)


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def draw_rounded_rect(c, x, y, w, h, r, fill_color=None, stroke_color=None, stroke_width=1):
    if fill_color:
        c.setFillColorRGB(*fill_color)
    if stroke_color:
        c.setStrokeColorRGB(*stroke_color)
        c.setLineWidth(stroke_width)
    else:
        c.setLineWidth(0)

    p = c.beginPath()
    p.moveTo(x + r, y)
    p.lineTo(x + w - r, y)
    p.curveTo(x + w, y, x + w, y, x + w, y + r)
    p.lineTo(x + w, y + h - r)
    p.curveTo(x + w, y + h, x + w, y + h, x + w - r, y + h)
    p.lineTo(x + r, y + h)
    p.curveTo(x, y + h, x, y + h, x, y + h - r)
    p.lineTo(x, y + r)
    p.curveTo(x, y, x, y, x + r, y)
    p.close()

    if fill_color and stroke_color:
        c.drawPath(p, fill=1, stroke=1)
    elif fill_color:
        c.drawPath(p, fill=1, stroke=0)
    elif stroke_color:
        c.drawPath(p, fill=0, stroke=1)


@report_bp.route('/api/report/', methods=['POST'])
def generate_report():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        student  = data.get('student', {})
        result   = data.get('result', {})
        recos    = data.get('recommendations', [])

        #colors
        C_BG       = hex_to_rgb('#03040a')
        C_PANEL    = hex_to_rgb('#0d1220')
        C_CYAN     = hex_to_rgb('#00d4ff')
        C_GOLD     = hex_to_rgb('#f5c842')
        C_GREEN    = hex_to_rgb('#00e5a0')
        C_AMBER    = hex_to_rgb('#ff9500')
        C_RED      = hex_to_rgb('#ff4560')
        C_TEXT     = hex_to_rgb('#e2e8f8')
        C_TEXT2    = hex_to_rgb('#7a8aaa')
        C_TEXT3    = hex_to_rgb('#3d4d6a')
        C_RIM      = hex_to_rgb('#1a2236')

        risk_level = result.get('risk_level', 'Medium')
        if risk_level == 'High':
            C_ACCENT = C_GREEN
            verdict  = 'High Performance'
        elif risk_level == 'Medium':
            C_ACCENT = C_AMBER
            verdict  = 'Medium Performance'
        else:
            C_ACCENT = C_RED
            verdict  = 'Low Performance'

        #canvas
        buf    = BytesIO()
        W, H   = A4
        c      = canvas.Canvas(buf, pagesize=A4)
        MARGIN = 32

        def page_bg():
            c.setFillColorRGB(*C_BG)
            c.rect(0, 0, W, H, fill=1, stroke=0)
            # subtle grid lines
            c.setStrokeColorRGB(0, 0.08, 0.1)
            c.setLineWidth(0.3)
            step = 28
            for xi in range(0, int(W), step):
                c.line(xi, 0, xi, H)
            for yi in range(0, int(H), step):
                c.line(0, yi, W, yi)

        #Page1
        page_bg()

        #bar
        c.setFillColorRGB(*C_ACCENT)
        c.rect(0, H - 4, W, 4, fill=1, stroke=0)

        #nav
        c.setFillColorRGB(0.05, 0.07, 0.12)
        c.rect(0, H - 52, W, 48, fill=1, stroke=0)
        c.setFillColorRGB(*C_TEXT)
        c.setFont('Helvetica-Bold', 14)
        c.drawString(MARGIN, H - 34, 'NEXUS')
        c.setFillColorRGB(*C_TEXT3)
        c.setFont('Helvetica', 7)
        c.drawString(MARGIN, H - 45, 'STUDENT PERFORMANCE INTELLIGENCE')
        ts = datetime.datetime.now().strftime('%d %b %Y  %H:%M')
        c.setFillColorRGB(*C_TEXT3)
        c.setFont('Helvetica', 7)
        c.drawRightString(W - MARGIN, H - 34, f'Generated: {ts}')
        c.drawRightString(W - MARGIN, H - 44, 'CONFIDENTIAL ACADEMIC REPORT')

        y = H - 80

        #header
        c.setFillColorRGB(*C_TEXT)
        c.setFont('Helvetica-Bold', 22)
        c.drawString(MARGIN, y, student.get('name', '—'))

        y -= 18
        c.setFillColorRGB(*C_TEXT2)
        c.setFont('Helvetica', 9)
        meta = f"{student.get('roll_number','—')}   ·   {student.get('department','—')}   ·   {student.get('year','—')}"
        c.drawString(MARGIN, y, meta)

        y -= 28

        
        CARD_H = 110
        draw_rounded_rect(c, MARGIN, y - CARD_H, W - 2*MARGIN, CARD_H, 10,
                          fill_color=C_PANEL, stroke_color=C_RIM, stroke_width=0.8)

        c.setFillColorRGB(*C_ACCENT)
        c.rect(MARGIN, y - CARD_H, 4, CARD_H, fill=1, stroke=0)

        c.setFillColorRGB(*C_ACCENT)
        c.setFont('Helvetica-Bold', 20)
        c.drawString(MARGIN + 24, y - 36, verdict)

        c.setFillColorRGB(*C_TEXT2)
        c.setFont('Helvetica', 8)
        c.drawString(MARGIN + 24, y - 50, 'PERFORMANCE LEVEL')


        score_x = W - MARGIN - 140
        c.setFillColorRGB(*C_TEXT3)
        c.setFont('Helvetica', 7)
        c.drawString(score_x, y - 28, 'COMPOSITE SCORE')
        c.setFillColorRGB(*C_TEXT)
        c.setFont('Helvetica-Bold', 32)
        c.drawString(score_x, y - 58, str(result.get('composite_score', '—')))
        c.setFillColorRGB(*C_TEXT2)
        c.setFont('Helvetica', 9)
        c.drawString(score_x + 50, y - 48, '/ 100')


        risk_x = W - MARGIN - 260
        c.setFillColorRGB(*C_TEXT3)
        c.setFont('Helvetica', 7)
        c.drawString(risk_x, y - 28, 'RISK SCORE')
        c.setFillColorRGB(*C_ACCENT)
        c.setFont('Helvetica-Bold', 28)
        c.drawString(risk_x, y - 56, str(result.get('risk_score', '—')) + '%')


        grade_x = score_x + 90
        c.setFillColorRGB(*C_TEXT3)
        c.setFont('Helvetica', 7)
        c.drawString(grade_x, y - 28, 'PREDICTED GRADE')
        c.setFillColorRGB(*C_GOLD)
        c.setFont('Helvetica-Bold', 28)
        c.drawString(grade_x, y - 56, result.get('predicted_grade', '—'))

        y -= CARD_H + 24


        c.setFillColorRGB(*C_TEXT3)
        c.setFont('Helvetica', 7)
        c.drawString(MARGIN, y, 'FACTOR BREAKDOWN')
        c.setStrokeColorRGB(*C_TEXT3)
        c.setLineWidth(0.5)
        c.line(MARGIN + 110, y + 4, W - MARGIN, y + 4)
        y -= 16

        fs = result.get('feature_scores', {})
        factors = [
            ('Attendance',       fs.get('attendance', 0),       C_CYAN),
            ('Study Hours',      fs.get('study_hours', 0),      C_GOLD),
            ('Internal Marks',   fs.get('internal_marks', 0),   C_GREEN),
            ('Assignment Score', fs.get('assignment_score', 0), C_AMBER),
            ('Mid-term Score',   fs.get('midterm_score', 0),    hex_to_rgb('#4f7cff')),
        ]

        BAR_W  = W - 2*MARGIN - 100
        BAR_H  = 7
        LABEL_W = 96

        for label, val, colour in factors:
            c.setFillColorRGB(*C_TEXT2)
            c.setFont('Helvetica', 8)
            c.drawString(MARGIN, y, label)

            bx = MARGIN + LABEL_W
            # track
            draw_rounded_rect(c, bx, y - 1, BAR_W, BAR_H, 3,
                              fill_color=C_RIM)
            # fill
            fill_w = max(4, BAR_W * min(val, 100) / 100)
            draw_rounded_rect(c, bx, y - 1, fill_w, BAR_H, 3,
                              fill_color=colour)

            c.setFillColorRGB(*C_TEXT)
            c.setFont('Helvetica-Bold', 8)
            c.drawRightString(W - MARGIN, y + 5, f'{val}%')

            y -= 22

        y -= 16

        c.setFillColorRGB(*C_TEXT3)
        c.setFont('Helvetica', 7)
        c.drawString(MARGIN, y, 'RECOMMENDED ACTIONS')
        c.setStrokeColorRGB(*C_TEXT3)
        c.setLineWidth(0.5)
        c.line(MARGIN + 128, y + 4, W - MARGIN, y + 4)
        y -= 18

        COL_W  = (W - 2*MARGIN - 12) / 2
        col_x  = [MARGIN, MARGIN + COL_W + 12]
        col    = 0
        reco_y = y

        for reco in recos[:6]:
            cx = col_x[col]
            RECO_H = 52
            draw_rounded_rect(c, cx, reco_y - RECO_H, COL_W, RECO_H, 8,
                              fill_color=C_PANEL, stroke_color=C_RIM, stroke_width=0.6)

            c.setFillColorRGB(*C_CYAN)
            c.setFont('Helvetica-Bold', 8)
            c.drawString(cx + 12, reco_y - 18, reco.get('title', ''))


            detail = reco.get('detail', '')
            c.setFillColorRGB(*C_TEXT2)
            c.setFont('Helvetica', 7)

            words = detail.split()
            line1, line2 = [], []
            for w in words:
                test = ' '.join(line1 + [w])
                if c.stringWidth(test, 'Helvetica', 7) < COL_W - 24:
                    line1.append(w)
                else:
                    line2.append(w)
            c.drawString(cx + 12, reco_y - 30, ' '.join(line1))
            if line2:
                c.drawString(cx + 12, reco_y - 40, ' '.join(line2))

            col += 1
            if col == 2:
                col = 0
                reco_y -= RECO_H + 10


        c.setFillColorRGB(*C_TEXT3)
        c.setFont('Helvetica', 7)
        c.drawCentredString(W / 2, 18, 'NEXUS Student Performance Intelligence  ·  This report is auto-generated and for academic advisory use only.')
        c.setStrokeColorRGB(*C_TEXT3)
        c.setLineWidth(0.4)
        c.line(MARGIN, 28, W - MARGIN, 28)

        c.showPage()
        c.save()
        buf.seek(0)

        safe_name = student.get('name', 'student').replace(' ', '_')
        filename  = f"NEXUS_Report_{safe_name}.pdf"

        return send_file(
            buf,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500