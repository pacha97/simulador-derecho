#!/usr/bin/env python3
"""
Extract ALL 1500 questions from the PDF.
V4: Uses option letters (a,b,c,d) as primary grouping structure.
Fixes the issue where header pages were skipped, ensuring all 5996 data rows are processed.
"""

import pdfplumber
import re
import json

PDF_PATH = '/Users/miguelangelguzman/Downloads/Cuestionario de examen complexivo Derecho 2026.pdf'
OUTPUT_JS = '/Users/miguelangelguzman/.gemini/antigravity/scratch/simulador-derecho/questions.js'
OUTPUT_JSON = '/Users/miguelangelguzman/.gemini/antigravity/scratch/simulador-derecho/questions.json'

SECTIONS = [
    (6,   "Derecho Constitucional", "Elementos constitutivos del Estado"),
    (23,  "Derecho Constitucional", "Derechos y Garantías Constitucionales"),
    (44,  "Derecho Constitucional", "Participación y organización del poder"),
    (65,  "Derecho Constitucional", "Organización territorial del Estado ecuatoriano"),
    (74,  "Derecho Constitucional", "Régimen de Desarrollo y del Buen Vivir"),
    (81,  "Derecho Constitucional", "Supremacía de la Constitución"),
    (89,  "Derecho Procesal", "Derecho Procesal General"),
    (102, "Derecho Procesal", "Derecho Procesal Penal"),
    (122, "Derecho Procesal", "Métodos Alternativos de Resolución de Conflictos"),
    (129, "Derecho Penal", "Teoría General del Delito"),
    (139, "Derecho Penal", "Agravantes y atenuantes"),
    (144, "Derecho Penal", "Formas de participación"),
    (149, "Derecho Penal", "Extinción de la pena"),
    (154, "Derecho Penal", "Catálogo de delitos - Administración Pública"),
    (161, "Derecho Penal", "Catálogo de delitos - Parte Especial"),
    (168, "Derecho Penal", "Catálogo de delitos - Integridad sexual"),
    (174, "Derecho Penal", "Catálogo de delitos - Propiedad"),
    (181, "Derecho Civil", "Sujetos del Derecho"),
    (197, "Derecho Civil", "Bienes, dominio, posesión, uso, goce y limitaciones"),
    (214, "Derecho Civil", "Sucesiones por causa de muerte"),
    (230, "Derecho Civil", "Obligaciones y Contratos"),
    (249, "Derecho Administrativo", "Administración Pública"),
    (255, "Derecho Administrativo", "Formas jurídicas administrativas"),
    (266, "Derecho Administrativo", "Reclamos y recursos en sede administrativa"),
    (277, "Introducción y Filosofía del Derecho", "Introducción al Derecho"),
    (285, "Introducción y Filosofía del Derecho", "Filosofía del Derecho"),
    (291, "Derecho Laboral", "Contrato Individual de Trabajo"),
    (303, "Derecho Laboral", "Contrato Colectivo de Trabajo"),
]

def get_section(pi):
    result = None
    for sp, t, s in SECTIONS:
        if pi >= sp:
            result = (t, s)
        else:
            break
    return result

def clean(text):
    if not text:
        return ""
    text = re.sub(r'(\w)-\n\s*(\w)', r'\1\2', text)
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def cell(val):
    """Convert cell to clean string, treating None as empty."""
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s == "None" else s

def main():
    print("=" * 70)
    print("Extractor v4 - Option-letter based grouping (No skipped pages)")
    print("=" * 70)
    
    all_rows = []
    
    with pdfplumber.open(PDF_PATH) as pdf:
        print(f"Pages: {len(pdf.pages)}")
        
        for pi in range(6, len(pdf.pages)):
            page = pdf.pages[pi]
            tables = page.extract_tables()
            if not tables:
                continue
            
            for table in tables:
                for row in table:
                    if not row:
                        continue
                    while len(row) < 6:
                        row.append(None)
                    if cell(row[0]) == 'Pregunta':
                        continue
                    all_rows.append((pi, row))
    
    print(f"Total data rows collected: {len(all_rows)}")
    
    questions = []
    i = 0
    
    while i < len(all_rows):
        pi, row = all_rows[i]
        opt_l = cell(row[2]).lower()
        
        if opt_l != 'a':
            i += 1
            continue
        
        q_rows = [(pi, row)]
        j = i + 1
        expected_letters = ['b', 'c', 'd']
        
        for exp_l in expected_letters:
            if j < len(all_rows):
                next_pi, next_row = all_rows[j]
                next_opt = cell(next_row[2]).lower()
                if next_opt == exp_l:
                    q_rows.append((next_pi, next_row))
                    j += 1
                else:
                    break
        
        if len(q_rows) < 3:
            i += 1
            continue
        
        section = get_section(q_rows[0][0])
        if not section:
            i = j
            continue
        
        topic, subtopic = section
        
        enunciado = ""
        q_num = ""
        for rpi, rrow in q_rows:
            qn = cell(rrow[0])
            en = cell(rrow[1])
            if qn and qn.isdigit() and en and len(en) > 5:
                enunciado = en
                q_num = qn
                break
        
        if not enunciado and i > 0:
            prev_pi, prev_row = all_rows[i - 1]
            prev_qn = cell(prev_row[0])
            prev_en = cell(prev_row[1])
            if prev_qn and prev_qn.isdigit() and prev_en and len(prev_en) > 5:
                enunciado = prev_en
                q_num = prev_qn
        
        if not enunciado:
            en = cell(q_rows[0][1])
            if en and len(en) > 5:
                enunciado = en
                
        options = []
        correct = ""
        feedback = ""
        
        for rpi, rrow in q_rows:
            ol = cell(rrow[2]).lower()
            ot = cell(rrow[3])
            mark = cell(rrow[4])
            fb = cell(rrow[5])
            
            if ol in ['a', 'b', 'c', 'd'] and ot:
                options.append({"letter": ol, "text": clean(ot)})
                if mark and (mark.upper() == 'X' or mark.lower().startswith('correct')):
                    correct = ol
            if fb:
                if feedback:
                    feedback += ' ' + clean(fb)
                else:
                    feedback = clean(fb)
                    
        # Fallback for the 7 questions missing correct markers:
        if not correct and feedback:
            fb_lower = feedback.lower()
            # Common patterns found in feedback: "la opción b es la correcta"
            for letter in ['a', 'b', 'c', 'd']:
                if f"opción {letter} es la correcta" in fb_lower or f"opción {letter} es correcta" in fb_lower:
                    correct = letter
                    break
                    
        q = {
            "topic": topic,
            "subtopic": subtopic,
            "question": clean(enunciado),
            "options": options,
            "correct": correct,
            "feedback": feedback,
        }
        
        if q['question'] and len(q['options']) >= 3 and q['correct']:
            if q['correct'] in [o['letter'] for o in q['options']]:
                questions.append(q)
            else:
                print(f"  ⚠️ Correct '{q['correct']}' not in options: page {q_rows[0][0]+1}")
        else:
            reasons = []
            if not q['question']: reasons.append('no text')
            if len(q['options']) < 3: reasons.append(f'{len(q["options"])} opts')
            if not q['correct']: reasons.append('no correct')
            print(f"  ⚠️ Invalid Q page {q_rows[0][0]+1}: {', '.join(reasons)} | {q.get('question','')[:60]}")
        
        i = j
    
    print(f"\n{'='*70}")
    print(f"RESULTS: {len(questions)} valid questions extracted")
    print(f"{'='*70}")
    
    expected_topics = {
        "Derecho Constitucional": 375,
        "Derecho Procesal": 225,
        "Derecho Penal": 270,
        "Derecho Civil": 270,
        "Derecho Administrativo": 150,
        "Introducción y Filosofía del Derecho": 60,
        "Derecho Laboral": 150,
    }
    
    topics = {}
    for q in questions:
        topics[q['topic']] = topics.get(q['topic'], 0) + 1
    
    print(f"\n{'Topic':<45} {'Expected':>8} {'Got':>6} {'%':>6}")
    print('-' * 70)
    for t in expected_topics:
        exp = expected_topics[t]
        got = topics.get(t, 0)
        print(f"{t:<45} {exp:>8} {got:>6} {got/exp*100:>5.1f}%")
    print('-' * 70)
    total_exp = sum(expected_topics.values())
    print(f"{'TOTAL':<45} {total_exp:>8} {len(questions):>6} {len(questions)/total_exp*100:>5.1f}%")
    
    js = "// Auto-generated question bank - Examen Complexivo Derecho 2026\n"
    js += f"// Total questions: {len(questions)}\n"
    js += "// Generated from PDF extraction v4\n\n"
    js += "const QUESTIONS = " + json.dumps(questions, ensure_ascii=False, indent=2) + ";\n"
    
    with open(OUTPUT_JS, 'w', encoding='utf-8') as f:
        f.write(js)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Saved to {OUTPUT_JS}")

if __name__ == '__main__':
    main()
