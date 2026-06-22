#!/usr/bin/env python3
"""
Extract ALL 1500 questions from the Cuestionario de examen complexivo Derecho 2026 PDF.
Version 2: Improved extraction with cross-page question handling and better row parsing.
"""

import pdfplumber
import re
import json

PDF_PATH = '/Users/miguelangelguzman/Downloads/Cuestionario de examen complexivo Derecho 2026.pdf'
OUTPUT_JS = '/Users/miguelangelguzman/.gemini/antigravity/scratch/simulador-derecho/questions.js'
OUTPUT_JSON = '/Users/miguelangelguzman/.gemini/antigravity/scratch/simulador-derecho/questions.json'

# Section definitions: page_index -> (topic, subtopic, has_content_on_header_page)
# Some sections don't have a standalone header page - the header is on the same page as the first table
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

# Pages that are section headers but also contain tables
CONTENT_SECTION_PAGES = {139, 174}

# Header pages that have no question content
HEADER_ONLY_PAGES = set()
for sp, _, _ in SECTIONS:
    if sp not in CONTENT_SECTION_PAGES:
        HEADER_ONLY_PAGES.add(sp)


def get_section_for_page(page_idx):
    """Get topic and subtopic for a given page index."""
    result = None
    for sp, topic, subtopic in SECTIONS:
        if page_idx >= sp:
            result = (topic, subtopic)
        else:
            break
    return result


def clean_text(text):
    """Clean up text extracted from PDF."""
    if not text:
        return ""
    text = re.sub(r'(\w)-\n\s*(\w)', r'\1\2', text)
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def is_header_row(row):
    """Check if a table row is the column header row."""
    if not row or len(row) < 2:
        return False
    cell0 = str(row[0] or '').strip()
    return cell0 == 'Pregunta'


def extract_all():
    """
    Extract all questions using an improved approach:
    1. Collect ALL table rows across ALL pages in order
    2. Group rows into questions by detecting question-number rows
    3. Handle edge cases: merged cells, missing markers, etc.
    """
    all_rows = []  # List of (page_idx, row_data)
    
    with pdfplumber.open(PDF_PATH) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        
        for page_idx in range(len(pdf.pages)):
            # Skip front matter
            if page_idx < 6:
                continue
            # Skip header-only pages
            if page_idx in HEADER_ONLY_PAGES:
                continue
                
            page = pdf.pages[page_idx]
            
            # Try with custom table settings for better extraction
            tables = page.extract_tables({
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 5,
                "join_tolerance": 5,
                "edge_min_length": 10,
                "min_words_vertical": 1,
                "min_words_horizontal": 1,
            })
            
            if not tables:
                # Fallback to default settings
                tables = page.extract_tables()
            
            if not tables:
                continue
            
            for table in tables:
                for row in table:
                    if not row:
                        continue
                    if is_header_row(row):
                        continue
                    # Pad row to 6 columns
                    while len(row) < 6:
                        row.append(None)
                    all_rows.append((page_idx, row))
    
    print(f"Total data rows collected: {len(all_rows)}")
    
    # Now group rows into questions
    questions = group_rows_into_questions(all_rows)
    return questions


def group_rows_into_questions(all_rows):
    """
    Group sequential rows into question objects.
    
    Each question has 4 rows (options a, b, c, d):
    - Row with q_num in col[0]: first option (usually 'a')
    - 3 rows with empty col[0]: remaining options (b, c, d)
    
    Table columns:
    [0] = Question number (only on first row)
    [1] = Enunciado (question text, only on first row)
    [2] = Option letter (a/b/c/d)
    [3] = Option text
    [4] = Correct marker (X/x/Correcto/Correcta, or empty)
    [5] = Feedback text (usually only on first row, sometimes spans)
    """
    questions = []
    current_q = None
    
    for page_idx, row in all_rows:
        section = get_section_for_page(page_idx)
        if not section:
            continue
        
        topic, subtopic = section
        
        # Extract cell values
        q_num = str(row[0]).strip() if row[0] else ""
        enunciado = str(row[1]).strip() if row[1] else ""
        opt_letter = str(row[2]).strip().lower() if row[2] else ""
        opt_text = str(row[3]).strip() if row[3] else ""
        correct_mark = str(row[4]).strip() if row[4] else ""
        feedback = str(row[5]).strip() if row[5] else ""
        
        # Clean "None" strings
        if q_num == "None": q_num = ""
        if enunciado == "None": enunciado = ""
        if opt_letter == "none": opt_letter = ""
        if opt_text == "None": opt_text = ""
        if correct_mark == "None": correct_mark = ""
        if feedback == "None": feedback = ""
        
        # Is this a new question?
        is_new_question = q_num and q_num.isdigit() and enunciado and len(enunciado) > 5
        
        if is_new_question:
            # Save previous question
            if current_q:
                finalize_question(current_q)
                if is_valid_question(current_q):
                    questions.append(current_q)
            
            # Start new question
            current_q = {
                "topic": topic,
                "subtopic": subtopic,
                "question": clean_text(enunciado),
                "options": [],
                "correct": "",
                "feedback": "",
                "_page": page_idx + 1,
                "_num": q_num,
            }
        
        if not current_q:
            continue
        
        # Add option if valid
        if opt_letter in ['a', 'b', 'c', 'd'] and opt_text:
            # Check if we already have this letter (avoid duplicates)
            existing_letters = [o['letter'] for o in current_q['options']]
            if opt_letter not in existing_letters:
                current_q['options'].append({
                    "letter": opt_letter,
                    "text": clean_text(opt_text)
                })
            
            # Check correct marker
            if correct_mark:
                cm = correct_mark.strip()
                if cm.upper() == 'X' or cm.lower().startswith('correct'):
                    current_q['correct'] = opt_letter
        
        # Accumulate feedback
        if feedback:
            if current_q['feedback']:
                current_q['feedback'] += ' ' + clean_text(feedback)
            else:
                current_q['feedback'] = clean_text(feedback)
    
    # Don't forget the last question
    if current_q:
        finalize_question(current_q)
        if is_valid_question(current_q):
            questions.append(current_q)
    
    return questions


def finalize_question(q):
    """Final cleanup and validation of a question before saving."""
    # If no correct answer was found via the marker column,
    # try to find it in the option text or feedback
    if not q['correct']:
        # Some questions mark correct with 'X' or 'x' at end of option text
        for opt in q['options']:
            text = opt['text']
            if text.endswith('X') or text.endswith('x'):
                # Check it's actually a marker, not part of a word
                if len(text) > 1 and text[-2] in '.;:) ':
                    q['correct'] = opt['letter']
                    opt['text'] = text[:-1].rstrip()
                    break
            # Check for 'Correcto' or 'Correcta' at end
            for marker in ['Correcto', 'Correcta', 'correcto', 'correcta']:
                if text.endswith(marker):
                    q['correct'] = opt['letter']
                    opt['text'] = text[:-len(marker)].rstrip()
                    break
            if q['correct']:
                break
    
    # Try to detect correct answer from feedback text
    if not q['correct'] and q['feedback']:
        fb = q['feedback'].lower()
        # Patterns like "la respuesta correcta es la opción b" or "opción a es correcta"
        for letter in ['a', 'b', 'c', 'd']:
            patterns = [
                f'opción {letter} es correcta',
                f'opción {letter} es la correcta',
                f'respuesta correcta es {letter}',
                f'respuesta correcta es la {letter}',
                f'literal {letter} es correct',
                f'literal {letter})',
            ]
            for p in patterns:
                if p in fb:
                    q['correct'] = letter
                    break
            if q['correct']:
                break
    
    # Clean up internal fields
    q['feedback'] = q.get('feedback', '').strip()
    
    # Remove internal tracking fields
    q.pop('_page', None)
    q.pop('_num', None)


def is_valid_question(q):
    """Check if a question is valid."""
    if not q.get('question') or len(q['question']) < 10:
        return False
    if not q.get('options') or len(q['options']) < 3:
        return False
    if not q.get('correct'):
        return False
    # Verify correct answer exists in options
    option_letters = [o['letter'] for o in q['options']]
    if q['correct'] not in option_letters:
        return False
    return True


def save_questions(questions):
    """Save questions to JS and JSON files."""
    js_content = "// Auto-generated question bank - Examen Complexivo Derecho 2026\n"
    js_content += f"// Total questions: {len(questions)}\n"
    js_content += "// Generated from PDF extraction v2\n\n"
    js_content += "const QUESTIONS = " + json.dumps(questions, ensure_ascii=False, indent=2) + ";\n"
    
    with open(OUTPUT_JS, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved {len(questions)} questions to {OUTPUT_JS}")


def print_stats(questions, invalid_count=0):
    """Print detailed statistics."""
    print(f"\n{'='*70}")
    print(f"EXTRACTION RESULTS")
    print(f"{'='*70}")
    print(f"Total valid questions: {len(questions)}")
    if invalid_count:
        print(f"Invalid (discarded): {invalid_count}")
    
    # By topic
    topics = {}
    for q in questions:
        topics[q['topic']] = topics.get(q['topic'], 0) + 1
    
    expected_topics = {
        "Derecho Constitucional": 375,
        "Derecho Procesal": 225,
        "Derecho Penal": 270,
        "Derecho Civil": 270,
        "Derecho Administrativo": 150,
        "Introducción y Filosofía del Derecho": 60,
        "Derecho Laboral": 150,
    }
    
    print(f"\n{'Topic':<45} {'Expected':>8} {'Got':>6} {'%':>6}")
    print('-' * 70)
    for topic in expected_topics:
        exp = expected_topics[topic]
        got = topics.get(topic, 0)
        pct = (got / exp * 100) if exp > 0 else 0
        print(f"{topic:<45} {exp:>8} {got:>6} {pct:>5.1f}%")
    print('-' * 70)
    print(f"{'TOTAL':<45} {sum(expected_topics.values()):>8} {len(questions):>6} {len(questions)/sum(expected_topics.values())*100:>5.1f}%")
    
    # By subtopic
    subtopics = {}
    for q in questions:
        key = f"{q['topic']} > {q['subtopic']}"
        subtopics[key] = subtopics.get(key, 0) + 1
    
    print(f"\nBy subtopic:")
    for s, count in sorted(subtopics.items()):
        print(f"  {s}: {count}")


def main():
    print("=" * 70)
    print("Extractor de Preguntas v2 - Examen Complexivo Derecho 2026")
    print("=" * 70)
    
    questions = extract_all()
    
    # Also collect invalid for reporting
    all_rows = []
    with pdfplumber.open(PDF_PATH) as pdf:
        for page_idx in range(len(pdf.pages)):
            if page_idx < 6 or page_idx in HEADER_ONLY_PAGES:
                continue
            page = pdf.pages[page_idx]
            tables = page.extract_tables({
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 5,
                "join_tolerance": 5,
            })
            if not tables:
                tables = page.extract_tables()
            if not tables:
                continue
            for table in tables:
                for row in table:
                    if row and not is_header_row(row):
                        while len(row) < 6:
                            row.append(None)
                        all_rows.append((page_idx, row))
    
    # Count how many question starts we found
    q_starts = sum(1 for _, r in all_rows 
                   if r[0] and str(r[0]).strip().isdigit() 
                   and r[1] and len(str(r[1]).strip()) > 5)
    
    print(f"\nQuestion starts detected in tables: {q_starts}")
    print(f"Valid questions extracted: {len(questions)}")
    
    print_stats(questions)
    save_questions(questions)
    
    # Report questions without correct answer
    # Re-extract to get invalid ones too
    all_extracted = group_rows_into_questions(all_rows)
    invalid = [q for q in all_extracted if not is_valid_question(q)]
    
    if invalid:
        print(f"\n⚠️  Questions discarded ({len(invalid)}):")
        for q in invalid[:20]:
            reason = []
            if not q.get('correct'):
                reason.append('no correct answer')
            if len(q.get('options', [])) < 3:
                reason.append(f'only {len(q.get("options", []))} options')
            print(f"  - [{', '.join(reason)}] {q.get('question', '???')[:80]}")


if __name__ == '__main__':
    main()
