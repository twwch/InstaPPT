import json
import os
import pandas as pd
from .models import TranslationSegment, SDKConfig
from typing import List, Dict
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

def generate_json_report(segments: List[TranslationSegment], output_path: str):
    """Save segments as JSON."""
    data = [seg.model_dump() for seg in segments]
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def generate_bilingual_pdf(segments: List[TranslationSegment], output_path: str):
    """
    Generates a side-by-side bilingual comparison PDF (Original vs Final Text).
    """
    font_name = register_chinese_font()
    
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    # Create custom style with Chinese font
    header_style = ParagraphStyle(
        'HeaderCN', 
        parent=styles['Heading1'], 
        fontName=font_name,
        alignment=1 # Center
    )
    normal_style = ParagraphStyle(
        'NormalCN',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=14
    )
    
    elements.append(Paragraph("双语对照报告 (Bilingual Comparison)", header_style))
    elements.append(Spacer(1, 20))
    
    data = [["原文 (Original)", "译文 (Translated)"]]
    
    for seg in segments:
        orig = Paragraph(seg.original_text, normal_style)
        final = Paragraph(seg.final_text if seg.final_text else "", normal_style)
        data.append([orig, final])
        
    # Table col widths: A4 width is ~595. Margins ~72 each side. Usable ~450.
    # Split 50/50
    t = Table(data, colWidths=[225, 225])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), font_name),
        ('BACKGROUND', (0,0), (-1,0), colors.navy),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    
    elements.append(t)
    doc.build(elements)

def generate_excel_report(segments: List[TranslationSegment], output_path: str):
    """Save evaluation report as Excel."""
    rows = []
    for seg in segments:
        row = {
            "Original": seg.original_text,
            "Translation A": seg.translated_text_a,
            "Duration A (s)": seg.duration_a,
            "Score A": seg.evaluation_a.overall_score if seg.evaluation_a else 0,
            "Suggestions A": seg.evaluation_a.suggestions if seg.evaluation_a else "",
            "Translation C (Optimized)": seg.optimized_text_c,
            "Duration C (s)": seg.duration_c,
            "Score C": seg.evaluation_c.overall_score if seg.evaluation_c else 0,
            "Final Used": seg.final_text
        }
        # Add detailed metrics if needed
        if seg.evaluation_c:
            row["Accuracy C"] = seg.evaluation_c.metrics.accuracy
            row["Fluency C"] = seg.evaluation_c.metrics.fluency
            if seg.evaluation_c.duration_seconds:
                row["Eval C Duration (s)"] = seg.evaluation_c.duration_seconds
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_excel(output_path, index=False)

def register_chinese_font():
    """Register a Chinese font for ReportLab."""
    # Try common macOS fonts
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc", 
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
    ]
    
    font_name = "Helvetica" # Fallback
    for path in font_paths:
        if os.path.exists(path):
            try:
                # PingFang.ttc often has multiple faces, usually index 0 works or 'PingFangSC-Regular'
                # For simplicity in reportlab with ttc, we might need specific handling or just use valid one
                # Let's try registering.
                pdfmetrics.registerFont(TTFont('ChineseData', path))
                font_name = 'ChineseData'
                break
            except Exception:
                continue
    return font_name

def save_model_mapping(output_dir: str, models: Dict[str, str] = None) -> Dict[str, str]:
    """Save model alias mapping."""
    if models is None:
        mapping = {
            "A": "翻译模型 (Translator)",
            "B": "润色模型 (Optimizer)",
            "C": "评估模型 (Evaluator)"
        }
    else:
        mapping = models
        
    with open(os.path.join(output_dir, "model_mapping.json"), 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    return mapping

def generate_pdf_report(segments: List[TranslationSegment], output_path: str, models: Dict[str, str] = None):
    """Generate a stylized PDF report."""
    output_dir = os.path.dirname(output_path)
    save_model_mapping(output_dir, models)
    
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []
    
    font_name = register_chinese_font()
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'TitleCN', parent=styles['Title'], fontName=font_name, fontSize=24, leading=30, spaceAfter=20
    )
    header_style = ParagraphStyle(
        'HeaderCN', parent=styles['Heading2'], fontName=font_name, fontSize=14, textColor=colors.navy, spaceAfter=10
    )
    normal_style = ParagraphStyle(
        'NormalCN', parent=styles['Normal'], fontName=font_name, fontSize=10, leading=14
    )
    small_style = ParagraphStyle(
        'SmallCN', parent=styles['Normal'], fontName=font_name, fontSize=8, textColor=colors.gray
    )

    # 1. Header Info
    elements.append(Paragraph("此文件由译曲同工提供翻译服务", small_style))
    elements.append(Paragraph("更多信息请访问 aitranspro.com", small_style))
    elements.append(Paragraph("——内容仅供内部评估与试阅——", small_style))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("翻译质量评估报告", title_style))
    elements.append(Paragraph(f"文件: {os.path.basename(output_path).replace('comparison.pdf', '')}", normal_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("源语言: auto   目标语言: Target Language", normal_style)) 
    elements.append(Paragraph("日期: 2025-12-05", normal_style))
    elements.append(Spacer(1, 20))

    # 2. Model Mapping Table
    elements.append(Paragraph("模型说明", header_style))
    
    # Model names hidden for anonymization as requested
    
    data_models = [
        ["别名", "角色"],
        ["A", "翻译模型"],
        ["B", "润色模型 (优化)"],
        ["C", "评估模型"]
    ]
    t_models = Table(data_models, colWidths=[100, 300])
    t_models.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), font_name),
        ('BACKGROUND', (0,0), (-1,0), colors.navy),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    elements.append(t_models)
    elements.append(Spacer(1, 20))

    # 3. Summary Scores (Aggregate)
    elements.append(Paragraph("模型综合评分", header_style))
    
    # Filter segments that have evaluations
    segs_with_a = [s for s in segments if s.evaluation_a]
    count_a = len(segs_with_a)
    count_b = len(segments) # We always have a score for B (either C or inherited A)
    
    # Initialize sums
    metrics_a = {"accuracy": 0, "fluency": 0, "consistency": 0, "terminology": 0, "completeness": 0, "overall": 0}
    metrics_b = {"accuracy": 0, "fluency": 0, "consistency": 0, "terminology": 0, "completeness": 0, "overall": 0}
    
    for s in segments:
        # Model A
        if s.evaluation_a:
            m = s.evaluation_a.metrics
            metrics_a["accuracy"] += m.accuracy
            metrics_a["fluency"] += m.fluency
            metrics_a["consistency"] += m.consistency
            metrics_a["terminology"] += m.terminology
            metrics_a["completeness"] += m.completeness
            metrics_a["overall"] += s.evaluation_a.overall_score
            
        # Model B (Optimization)
        # Use C if available, else inherit A
        eval_b = s.evaluation_c if s.evaluation_c else s.evaluation_a
        if eval_b:
            m = eval_b.metrics
            metrics_b["accuracy"] += m.accuracy
            metrics_b["fluency"] += m.fluency
            metrics_b["consistency"] += m.consistency
            metrics_b["terminology"] += m.terminology
            metrics_b["completeness"] += m.completeness
            metrics_b["overall"] += eval_b.overall_score

    # Calculate Averages
    def calc_avg(metrics, count):
        if count == 0: return {k: 0.0 for k in metrics}
        return {k: v / count for k, v in metrics.items()}
        
    avg_a = calc_avg(metrics_a, count_a)
    avg_b = calc_avg(metrics_b, count_b)
    
    data_scores = [
        ["评分维度", "A\n(翻译)", "B\n(润色)"],
        ["准确性", f"{avg_a['accuracy']:.2f}", f"{avg_b['accuracy']:.2f}"],
        ["流畅性", f"{avg_a['fluency']:.2f}", f"{avg_b['fluency']:.2f}"],
        ["一致性", f"{avg_a['consistency']:.2f}", f"{avg_b['consistency']:.2f}"],
        ["术语准确性", f"{avg_a['terminology']:.2f}", f"{avg_b['terminology']:.2f}"],
        ["完整性", f"{avg_a['completeness']:.2f}", f"{avg_b['completeness']:.2f}"],
        ["综合评分", f"{avg_a['overall']:.2f}", f"{avg_b['overall']:.2f}"]
    ]
    
    t_scores = Table(data_scores, colWidths=[150, 125, 125])
    t_scores.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), font_name),
        ('BACKGROUND', (0,0), (-1,0), colors.navy),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,-1), (-1,-1), colors.beige),
    ]))
    elements.append(t_scores)
    elements.append(Spacer(1, 20))
    elements.append(PageBreak())

    # 4. Detailed Segments
    elements.append(Paragraph("详细段落评估", header_style))
    
    for i, seg in enumerate(segments, 1):
        elements.append(Paragraph(f"段落 {i}", header_style))
        elements.append(Paragraph(f"原文: {seg.original_text[:100]}...", normal_style))
        
        score_a = f"{seg.evaluation_a.overall_score:.2f}" if seg.evaluation_a else "N/A"
        text_a = seg.translated_text_a or ""
        
        score_b = f"{seg.evaluation_c.overall_score:.2f}" if seg.evaluation_c else "N/A"
        text_b = seg.optimized_text_c if seg.optimized_text_c else "(无需优化 / Skipped)"
        
        data_seg = [
            ["模型", "角色", "译文", "评分"],
            ["A", "翻译", Paragraph(text_a, normal_style), score_a],
            ["B", "润色", Paragraph(text_b, normal_style), score_b]
        ]
        
        t_seg = Table(data_seg, colWidths=[40, 40, 350, 50])
        t_seg.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), font_name),
            ('BACKGROUND', (0,0), (-1,0), colors.dodgerblue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        elements.append(t_seg)
        
        elements.append(Spacer(1, 5))
        elements.append(Paragraph("评估详情:", ParagraphStyle('BoldCN', parent=normal_style, fontName=font_name, fontSize=10)))
        
        # Details A
        if seg.evaluation_a:
            m = seg.evaluation_a.metrics
            details_a = f"准确性:{m.accuracy} 流畅性:{m.fluency} 一致性:{m.consistency} 术语:{m.terminology} 完整性:{m.completeness}"
            elements.append(Paragraph(f"• A (翻译) 评分明细: {details_a}", normal_style))
            elements.append(Paragraph(f"• 建议 (C->A): {seg.evaluation_a.suggestions}", normal_style))
        else:
             elements.append(Paragraph("• A (翻译): 无评估记录", normal_style))

        # Details B 
        if seg.evaluation_c:
             m = seg.evaluation_c.metrics
             details_b = f"准确性:{m.accuracy} 流畅性:{m.fluency} 一致性:{m.consistency} 术语:{m.terminology} 完整性:{m.completeness}"
             elements.append(Paragraph(f"• B (润色) 评分明细: {details_b}", normal_style))
             elements.append(Paragraph(f"• 建议 (C->B): {seg.evaluation_c.suggestions}", normal_style))
        elif seg.optimized_text_c and not seg.evaluation_c:
             # Optimized but maybe eval failed?
             elements.append(Paragraph("• B (润色): 已优化但评估失败", normal_style))
        
        elements.append(Spacer(1, 15))

    doc.build(elements)

def generate_visual_comparison_pdf(original_pptx: str, translated_pptx: str, output_path: str):
    """
    Generates a visual side-by-side comparison PDF using LibreOffice and pypdf.
    """
    import subprocess
    import shutil
    from pypdf import PdfReader, PdfWriter, PageObject, Transformation
    
    # 1. Check for LibreOffice (soffice) - Only on non-Windows
    soffice = None
    if os.name != 'nt':
        soffice = shutil.which("soffice")
        if not soffice:
            # Try common paths on macOS if not in PATH
            possible_paths = [
                "/Applications/LibreOffice.app/Contents/MacOS/soffice",
                "/usr/bin/soffice",
                "/usr/local/bin/soffice"
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    soffice = p
                    break
                    
        if not soffice:
            print("\n" + "="*60)
            print("WARNING: Visual Comparison Report Skipped")
            print("Reason: LibreOffice (soffice) command not found.")
            print("Solution: Please install LibreOffice (e.g., 'brew install --cask libreoffice')")
            print("="*60 + "\n")
            return

    print("Generating visual comparison PDF (this may take a while)...")
    
    try:
        # 2. Convert PPTXs to PDF
        # We use a temp dir
        temp_dir = os.path.join(os.path.dirname(output_path), "temp_conversion")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        def convert_to_pdf(pptx_path, out_dir):
            base = os.path.basename(pptx_path)
            name_no_ext = os.path.splitext(base)[0]
            out_pdf = os.path.join(out_dir, name_no_ext + ".pdf")
            
            if os.name == 'nt':
                # Windows Logic
                convert_pptx_to_pdf_windows(pptx_path, out_pdf)
                return out_pdf
            else:
                # macOS / Linux Logic (LibreOffice)
                cmd = [soffice, "--headless", "--convert-to", "pdf", "--outdir", out_dir, pptx_path]
                print(f"DEBUG: Running command: {' '.join(cmd)}")
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
            if os.path.exists(out_pdf):
                print(f"DEBUG: Generated PDF {out_pdf} size: {os.path.getsize(out_pdf)} bytes")
            else:
                print(f"DEBUG: Failed to generate PDF {out_pdf}")
                
            return out_pdf

        pdf_a_path = convert_to_pdf(original_pptx, temp_dir)
        pdf_b_path = convert_to_pdf(translated_pptx, temp_dir)
        
        # 3. Image-Based Comparison (Rasterize to fix font issues)
        # Check if pdftoppm is available
        pdftoppm = shutil.which("pdftoppm")
        if pdftoppm:
            print("Using Image-Based Comparison (pdftoppm found)...")
            images_a = pdf_to_images(pdf_a_path, temp_dir)
            images_b = pdf_to_images(pdf_b_path, temp_dir)
            stitch_images_to_pdf(images_a, images_b, output_path)
        else:
            print("pdftoppm not found, falling back to PDF merge (may have font issues)...")
            # Fallback to PDF merge
            merge_pdfs_side_by_side(pdf_a_path, pdf_b_path, output_path)
            
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"Visual comparison saved to: {output_path}")
        
    except Exception as e:
        print(f"Error generating visual comparison: {e}")

def pdf_to_images(pdf_path: str, output_dir: str) -> List[str]:
    """
    Convert PDF to images using pdftoppm.
    Returns list of image paths sorted by page number.
    """
    import subprocess
    import glob
    
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    prefix = os.path.join(output_dir, base_name)
    
    # pdftoppm -png -r 150 input.pdf prefix
    cmd = ["pdftoppm", "-png", "-r", "150", pdf_path, prefix]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Find generated images
    # pdftoppm generates prefix-1.png, prefix-2.png etc. or prefix-01.png depending on page count
    # We use glob
    pattern = f"{prefix}-*.png"
    images = glob.glob(pattern)
    
    # Sort by page number (extracted from filename)
    # Filename format: prefix-page_number.png
    def get_page_num(path):
        try:
            # Split by '-' and take the last part, then remove extension
            part = path.rsplit('-', 1)[-1]
            num = os.path.splitext(part)[0]
            return int(num)
        except:
            return 0
            
    images.sort(key=get_page_num)
    return images

def stitch_images_to_pdf(images_a: List[str], images_b: List[str], output_path: str):
    """
    Stitch images side-by-side and save as PDF.
    """
    from PIL import Image
    
    stitched_images = []
    num_pages = min(len(images_a), len(images_b))
    
    for i in range(num_pages):
        img_a = Image.open(images_a[i])
        img_b = Image.open(images_b[i])
        
        # Resize B to match A's height if needed (though they should be same from same PPT)
        if img_a.size != img_b.size:
             img_b = img_b.resize(img_a.size)
             
        w_a, h_a = img_a.size
        w_b, h_b = img_b.size
        
        total_width = w_a + w_b
        max_height = max(h_a, h_b)
        
        new_img = Image.new('RGB', (total_width, max_height), 'white')
        new_img.paste(img_a, (0, 0))
        new_img.paste(img_b, (w_a, 0))
        
        stitched_images.append(new_img)
        
    if stitched_images:
        # Save as PDF
        stitched_images[0].save(
            output_path, "PDF", resolution=100.0, save_all=True, append_images=stitched_images[1:]
        )

def save_token_usage(detailed_logs: List[dict], models: dict, output_path: str):
    """
    Save detailed token usage logs and a summary.
    """
    # Calculate summary
    summary = {
        "A (Translator)": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cached_count": 0, "model": models.get("A")},
        "B (Optimizer)": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cached_count": 0, "model": models.get("B")},
        "C (Evaluator)": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cached_count": 0, "model": models.get("C")}
    }
    
    for log in detailed_logs:
        tag = log.get("tag", "")
        key = None
        if "Stage A" in tag: key = "A (Translator)"
        elif "Stage C" in tag: key = "B (Optimizer)"
        elif "Stage B" in tag: key = "C (Evaluator)"
        
        if key:
            u = log.get("usage", {})
            summary[key]["prompt_tokens"] += u.get("prompt_tokens", 0)
            summary[key]["completion_tokens"] += u.get("completion_tokens", 0)
            summary[key]["total_tokens"] += u.get("total_tokens", 0)
            if u.get("cached"):
                summary[key]["cached_count"] += 1

    import datetime
    
    # Format timestamps
    formatted_logs = []
    for log in detailed_logs:
        new_log = log.copy()
        if "timestamp" in new_log and isinstance(new_log["timestamp"], (int, float)):
            dt = datetime.datetime.fromtimestamp(new_log["timestamp"])
            new_log["timestamp"] = dt.strftime("%Y-%m-%d %H:%M:%S")
        formatted_logs.append(new_log)

    data = {
        "summary": summary,
        "detailed_logs": formatted_logs
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def generate_bilingual_pdf(segments: List[TranslationSegment], output_path: str):
    """
    Generates a side-by-side bilingual comparison PDF (Original vs Final Text).
    """
    font_name = register_chinese_font()
    
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    # Create custom style with Chinese font
    header_style = ParagraphStyle(
        'HeaderCN', 
        parent=styles['Heading1'], 
        fontName=font_name,
        alignment=1 # Center
    )
    normal_style = ParagraphStyle(
        'NormalCN',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=14
    )
    
    elements.append(Paragraph("双语对照报告 (Bilingual Comparison)", header_style))
    elements.append(Spacer(1, 20))
    
    data = [["原文 (Original)", "译文 (Translated)"]]
    
    for seg in segments:
        orig = Paragraph(seg.original_text, normal_style)
        final = Paragraph(seg.final_text if seg.final_text else "", normal_style)
        data.append([orig, final])
        
    # Table col widths: A4 width is ~595. Margins ~72 each side. Usable ~450.
    # Split 50/50
    t = Table(data, colWidths=[225, 225])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), font_name),
        ('BACKGROUND', (0,0), (-1,0), colors.navy),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    
    elements.append(t)
    doc.build(elements)
