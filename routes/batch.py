import csv
import io
import datetime
from flask import Blueprint, request, jsonify, send_file
from ml.predictor import predict         

batch_bp = Blueprint('batch', __name__)

REQUIRED_COLUMNS = {
    'name', 'roll_number', 'department', 'year',
    'attendance', 'study_hours', 'internal_marks',
    'assignment_score', 'midterm_score', 'extracurricular'
}


@batch_bp.route('/api/batch/upload/', methods=['POST'])
def batch_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded. Send a CSV in the "file" field.'}), 400

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Only .csv files are accepted.'}), 400

    try:
        content = file.read().decode('utf-8-sig')   
    except UnicodeDecodeError:
        return jsonify({'error': 'File encoding must be UTF-8.'}), 400

    reader  = csv.DictReader(io.StringIO(content))
    headers = set(h.strip().lower().replace(' ', '_') for h in (reader.fieldnames or []))

    missing = REQUIRED_COLUMNS - headers
    if missing:
        return jsonify({'error': f'Missing columns: {", ".join(sorted(missing))}'}), 400

    rows = list(reader)
    if not rows:
        return jsonify({'error': 'CSV has no data rows.'}), 400
    if len(rows) > 500:
        return jsonify({'error': 'Maximum 500 rows allowed per upload.'}), 400

    results  = []
    errors   = []

    for i, raw in enumerate(rows, start=2):  
        row = {k.strip().lower().replace(' ', '_'): v.strip() for k, v in raw.items()}

        try:
            payload = {
                'name':             row.get('name', ''),
                'roll_number':      row.get('roll_number', ''),
                'department':       row.get('department', ''),
                'year':             row.get('year', ''),
                'attendance':       float(row.get('attendance', 0) or 0),
                'study_hours':      float(row.get('study_hours', 0) or 0),
                'internal_marks':   float(row.get('internal_marks', 0) or 0),
                'assignment_score': float(row.get('assignment_score', 0) or 0),
                'midterm_score':    float(row.get('midterm_score', 0) or 0),
                'extracurricular':  float(row.get('extracurricular', 0) or 0),
            }

            if not payload['name']:
                raise ValueError('name is required')
            if not payload['roll_number']:
                raise ValueError('roll_number is required')

            prediction = predict(payload)  
            results.append(prediction)

        except ValueError as ve:
            errors.append({'row': i, 'name': row.get('name', ''), 'error': str(ve)})
        except Exception as e:
            errors.append({'row': i, 'name': row.get('name', ''), 'error': f'Prediction failed: {e}'})

    # Summary counts
    high   = sum(1 for r in results if r['result']['risk_level'] == 'High')
    medium = sum(1 for r in results if r['result']['risk_level'] == 'Medium')
    low    = sum(1 for r in results if r['result']['risk_level'] == 'Low')

    return jsonify({
        'success': True,
        'summary': {
            'total_processed': len(results),
            'errors':          len(errors),
            'high':   high,
            'medium': medium,
            'low':    low,
        },
        'results': results,
        'errors':  errors,
    })


@batch_bp.route('/api/batch/report/', methods=['POST'])
def batch_report():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas as rl_canvas

        data    = request.get_json()
        results = data.get('results', [])

        if not results:
            return jsonify({'error': 'No results provided.'}), 400

        def hx(h):
            h = h.lstrip('#')
            return tuple(int(h[i:i+2], 16)/255 for i in (0,2,4))

        C_BG    = hx('#03040a')
        C_PANEL = hx('#0d1220')
        C_CYAN  = hx('#00d4ff')
        C_GOLD  = hx('#f5c842')
        C_GREEN = hx('#00e5a0')
        C_AMBER = hx('#ff9500')
        C_RED   = hx('#ff4560')
        C_TEXT  = hx('#e2e8f8')
        C_TEXT2 = hx('#7a8aaa')
        C_TEXT3 = hx('#3d4d6a')
        C_RIM   = hx('#1a2236')

        W, H   = A4
        MARGIN = 32
        buf    = io.BytesIO()
        c      = rl_canvas.Canvas(buf, pagesize=A4)

        ROWS_PER_PAGE = 28 

        def draw_bg():
            c.setFillColorRGB(*C_BG)
            c.rect(0, 0, W, H, fill=1, stroke=0)
            c.setStrokeColorRGB(0, 0.08, 0.1)
            c.setLineWidth(0.3)
            for xi in range(0, int(W), 28):
                c.line(xi, 0, xi, H)
            for yi in range(0, int(H), 28):
                c.line(0, yi, W, yi)

        def draw_header(page_num, total_pages):
            c.setFillColorRGB(*C_CYAN)
            c.rect(0, H-4, W, 4, fill=1, stroke=0)
            c.setFillColorRGB(0.05, 0.07, 0.12)
            c.rect(0, H-52, W, 48, fill=1, stroke=0)
            c.setFillColorRGB(*C_TEXT)
            c.setFont('Helvetica-Bold', 14)
            c.drawString(MARGIN, H-34, 'NEXUS')
            c.setFillColorRGB(*C_TEXT3)
            c.setFont('Helvetica', 7)
            c.drawString(MARGIN, H-45, 'BATCH PERFORMANCE REPORT')
            ts = datetime.datetime.now().strftime('%d %b %Y  %H:%M')
            c.drawRightString(W-MARGIN, H-34, f'Generated: {ts}')
            c.drawRightString(W-MARGIN, H-44, f'Page {page_num} of {total_pages}')

        def draw_summary_bar(y, high, medium, low, total):
            """Draws a coloured summary row near top of page 1."""
            stats = [
                (str(total),  'Total',   C_CYAN),
                (str(high),   'High',    C_GREEN),
                (str(medium), 'Medium',  C_AMBER),
                (str(low),    'At Risk', C_RED),
            ]
            bw  = (W - 2*MARGIN - 36) / 4
            bx  = MARGIN
            for val, lbl, col in stats:
                c.setFillColorRGB(*C_PANEL)
                c.roundRect(bx, y-48, bw, 56, 8, fill=1, stroke=0)
                c.setFillColorRGB(*col)
                c.rect(bx, y+8, bw, 3, fill=1, stroke=0)
                c.setFont('Helvetica-Bold', 22)
                c.setFillColorRGB(*col)
                c.drawCentredString(bx + bw/2, y-16, val)
                c.setFont('Helvetica', 8)
                c.setFillColorRGB(*C_TEXT3)
                c.drawCentredString(bx + bw/2, y-32, lbl.upper())
                bx += bw + 12

        def draw_table_header(y):
            cols = [(36,'#'), (90,'Name'), (76,'Roll No.'), (90,'Department'),
                    (58,'Year'), (42,'Score'), (36,'Grade'), (60,'Risk')]
            c.setFillColorRGB(*C_RIM)
            c.rect(MARGIN, y-2, W-2*MARGIN, 18, fill=1, stroke=0)
            x = MARGIN + 8
            for w_col, label in cols:
                c.setFillColorRGB(*C_TEXT3)
                c.setFont('Helvetica-Bold', 7)
                c.drawString(x, y+4, label.upper())
                x += w_col
            return y - 20

        def draw_student_row(y, idx, r, shade):
            cols_w = [36, 90, 76, 90, 58, 42, 36, 60]
            rl     = r['result']['risk_level']
            col_risk = C_GREEN if rl=='High' else C_AMBER if rl=='Medium' else C_RED

            if shade:
                c.setFillColorRGB(0.07, 0.1, 0.16)
                c.rect(MARGIN, y-2, W-2*MARGIN, 16, fill=1, stroke=0)

            vals = [
                str(idx),
                r['student']['name'][:14],
                r['student']['roll_number'][:12],
                r['student']['department'][:14],
                r['student']['year'][:10],
                str(r['result']['composite_score']),
                r['result']['predicted_grade'],
                rl,
            ]
            colours = [C_TEXT2, C_TEXT, C_TEXT2, C_TEXT2, C_TEXT2, C_TEXT, C_GOLD, col_risk]
            fonts   = ['Helvetica']*8
            fonts[1] = 'Helvetica-Bold'
            fonts[7] = 'Helvetica-Bold'

            x = MARGIN + 8
            for i, (val, col, fnt) in enumerate(zip(vals, colours, fonts)):
                c.setFillColorRGB(*col)
                c.setFont(fnt, 8)
                c.drawString(x, y+2, val)
                x += cols_w[i]

            return y - 18

        
        total_pages = 1 + (max(0, len(results) - 1) // ROWS_PER_PAGE)
        high   = sum(1 for r in results if r['result']['risk_level']=='High')
        medium = sum(1 for r in results if r['result']['risk_level']=='Medium')
        low    = sum(1 for r in results if r['result']['risk_level']=='Low')

        for page_num in range(1, total_pages + 1):
            draw_bg()
            draw_header(page_num, total_pages)

            y = H - 72

            if page_num == 1:
                # Title
                c.setFillColorRGB(*C_TEXT)
                c.setFont('Helvetica-Bold', 20)
                c.drawString(MARGIN, y, 'Batch Prediction Report')
                y -= 14
                c.setFillColorRGB(*C_TEXT3)
                c.setFont('Helvetica', 8)
                c.drawString(MARGIN, y, f'{len(results)} students processed')
                y -= 20
                draw_summary_bar(y, high, medium, low, len(results))
                y -= 68

                # Section label
                c.setFillColorRGB(*C_TEXT3)
                c.setFont('Helvetica', 7)
                c.drawString(MARGIN, y, 'STUDENT RESULTS')
                c.setStrokeColorRGB(*C_TEXT3)
                c.setLineWidth(0.4)
                c.line(MARGIN+92, y+4, W-MARGIN, y+4)
                y -= 14
                rows_this_page = ROWS_PER_PAGE - 8  
            else:
                rows_this_page = ROWS_PER_PAGE

            y = draw_table_header(y)

            start = (page_num - 1) * ROWS_PER_PAGE - (0 if page_num==1 else 8) if page_num > 1 else 0
            slice_start = 0 if page_num==1 else (ROWS_PER_PAGE - 8) + (page_num - 2) * ROWS_PER_PAGE
            slice_end   = slice_start + rows_this_page
            page_rows   = results[slice_start:slice_end]

            for i, r in enumerate(page_rows):
                global_idx = slice_start + i + 1
                y = draw_student_row(y, global_idx, r, i % 2 == 1)


            c.setFillColorRGB(*C_TEXT3)
            c.setFont('Helvetica', 7)
            c.drawCentredString(W/2, 18, 'NEXUS Student Performance Intelligence  ·  Batch Report  ·  Confidential')
            c.setStrokeColorRGB(*C_TEXT3)
            c.setLineWidth(0.4)
            c.line(MARGIN, 28, W-MARGIN, 28)

            if page_num < total_pages:
                c.showPage()

        c.save()
        buf.seek(0)

        filename = f"NEXUS_Batch_Report_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
        return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=filename)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
