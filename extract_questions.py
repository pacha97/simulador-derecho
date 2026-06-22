#!/usr/bin/env python3
"""
Extract questions from the Cuestionario de examen complexivo Derecho 2026 PDF.
Uses pdfplumber for table-aware extraction.
Outputs questions.js for the web app.
"""

import pdfplumber
import re
import json

PDF_PATH = '/Users/miguelangelguzman/Downloads/Cuestionario de examen complexivo Derecho 2026.pdf'
OUTPUT_JS = '/Users/miguelangelguzman/.gemini/antigravity/scratch/simulador-derecho/questions.js'
OUTPUT_JSON = '/Users/miguelangelguzman/.gemini/antigravity/scratch/simulador-derecho/questions.json'

# Section header pages (0-indexed) -> (topic, subtopic)
SECTION_PAGES = {
    6: ("Derecho Constitucional", "Elementos constitutivos del Estado"),
    23: ("Derecho Constitucional", "Derechos y Garantías Constitucionales"),
    44: ("Derecho Constitucional", "Participación y organización del poder"),
    65: ("Derecho Constitucional", "Organización territorial del Estado ecuatoriano"),
    74: ("Derecho Constitucional", "Régimen de Desarrollo y del Buen Vivir"),
    81: ("Derecho Constitucional", "Supremacía de la Constitución"),
    89: ("Derecho Procesal", "Derecho Procesal General"),
    102: ("Derecho Procesal", "Derecho Procesal Penal"),
    122: ("Derecho Procesal", "Métodos Alternativos de Resolución de Conflictos"),
    129: ("Derecho Penal", "Teoría General del Delito"),
    139: ("Derecho Penal", "Agravantes y atenuantes"),
    144: ("Derecho Penal", "Formas de participación"),
    149: ("Derecho Penal", "Extinción de la pena"),
    154: ("Derecho Penal", "Catálogo de delitos - Administración Pública"),
    161: ("Derecho Penal", "Catálogo de delitos - Parte Especial"),
    168: ("Derecho Penal", "Catálogo de delitos - Integridad sexual"),
    174: ("Derecho Penal", "Catálogo de delitos - Propiedad"),
    181: ("Derecho Civil", "Sujetos del Derecho"),
    197: ("Derecho Civil", "Bienes, dominio, posesión, uso, goce y limitaciones"),
    214: ("Derecho Civil", "Sucesiones por causa de muerte"),
    230: ("Derecho Civil", "Obligaciones y Contratos"),
    249: ("Derecho Administrativo", "Administración Pública"),
    255: ("Derecho Administrativo", "Formas jurídicas administrativas"),
    266: ("Derecho Administrativo", "Reclamos y recursos en sede administrativa"),
    277: ("Introducción y Filosofía del Derecho", "Introducción al Derecho"),
    285: ("Introducción y Filosofía del Derecho", "Filosofía del Derecho"),
    291: ("Derecho Laboral", "Contrato Individual de Trabajo"),
    303: ("Derecho Laboral", "Contrato Colectivo de Trabajo"),
}


def get_section_for_page(page_idx):
    """Get topic and subtopic for a page index."""
    sorted_keys = sorted(SECTION_PAGES.keys())
    result = None
    for sp in sorted_keys:
        if page_idx >= sp:
            result = SECTION_PAGES[sp]
        else:
            break
    return result


def clean_text(text):
    """Clean up text extracted from PDF."""
    if not text:
        return ""
    # Fix hyphenation at line breaks
    text = re.sub(r'(\w)-\n\s*(\w)', r'\1\2', text)
    # Replace newlines with spaces
    text = text.replace('\n', ' ')
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def is_header_row(row):
    """Check if a table row is the header row."""
    if not row or not row[0]:
        return False
    return 'Pregunta' in str(row[0]) or 'pregunta' in str(row[0])


# Pages that are section starts but also contain question content (no standalone header page)
CONTENT_SECTION_PAGES = {139, 174}

def is_content_page(page_idx):
    """Check if page has question content (not a section header or front matter)."""
    if page_idx < 6:  # Front matter
        return False
    if page_idx in CONTENT_SECTION_PAGES:  # These section pages also have content
        return True
    if page_idx in SECTION_PAGES:  # Section header pages (standalone)
        return False
    return True


def extract_questions():
    """Extract all questions from the PDF using pdfplumber table extraction."""
    all_questions = []
    
    with pdfplumber.open(PDF_PATH) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        
        for page_idx in range(len(pdf.pages)):
            if not is_content_page(page_idx):
                continue
            
            section = get_section_for_page(page_idx)
            if not section:
                continue
            
            topic, subtopic = section
            page = pdf.pages[page_idx]
            tables = page.extract_tables()
            
            if not tables:
                continue
            
            for table in tables:
                if not table:
                    continue
                
                # Process table rows
                # Structure: 
                #   Row with col[0]=question_num: first option of a new question
                #   Row with col[0]=None: continuation option (b, c, d) of same question
                #
                # Columns: [0]=Pregunta, [1]=Enunciado, [2]=Option letter, [3]=Option text, [4]=Correct marker, [5]=Feedback
                
                current_question = None
                
                for row in table:
                    if not row or len(row) < 4:
                        continue
                    
                    if is_header_row(row):
                        continue
                    
                    # Ensure we have enough columns, pad if needed
                    while len(row) < 6:
                        row.append(None)
                    
                    q_num = str(row[0]).strip() if row[0] else ""
                    enunciado = str(row[1]).strip() if row[1] else ""
                    opt_letter = str(row[2]).strip() if row[2] else ""
                    opt_text = str(row[3]).strip() if row[3] else ""
                    correct_mark = str(row[4]).strip() if row[4] else ""
                    feedback = str(row[5]).strip() if row[5] else ""
                    
                    # Is this a new question (has a question number)?
                    if q_num and q_num.isdigit() and enunciado:
                        # Save previous question if exists
                        if current_question and len(current_question['options']) >= 3:
                            all_questions.append(current_question)
                        
                        # Start new question
                        current_question = {
                            "topic": topic,
                            "subtopic": subtopic,
                            "question": clean_text(enunciado),
                            "options": [],
                            "correct": "",
                            "feedback": ""
                        }
                        
                        # Add first option
                        if opt_letter.lower() in ['a', 'b', 'c', 'd']:
                            current_question['options'].append({
                                "letter": opt_letter.lower(),
                                "text": clean_text(opt_text)
                            })
                            
                            # Check if this option is correct
                            if correct_mark and (correct_mark.upper() == 'X' or 'Correct' in correct_mark):
                                current_question['correct'] = opt_letter.lower()
                        
                        # Add feedback if present
                        if feedback and feedback != 'None':
                            current_question['feedback'] = clean_text(feedback)
                    
                    elif current_question:
                        # Continuation row - additional option
                        if opt_letter.lower() in ['a', 'b', 'c', 'd']:
                            current_question['options'].append({
                                "letter": opt_letter.lower(),
                                "text": clean_text(opt_text)
                            })
                            
                            # Check if this option is correct
                            if correct_mark and (correct_mark.upper() == 'X' or 'Correct' in correct_mark):
                                current_question['correct'] = opt_letter.lower()
                        
                        # Append feedback if present
                        if feedback and feedback != 'None':
                            if current_question['feedback']:
                                current_question['feedback'] += ' ' + clean_text(feedback)
                            else:
                                current_question['feedback'] = clean_text(feedback)
                
                # Don't forget the last question on the page
                if current_question and len(current_question['options']) >= 3:
                    all_questions.append(current_question)
    
    return all_questions


def detect_agravantes_section(all_questions):
    """
    The 'Agravantes y atenuantes' section (page ~140) might not be in SECTION_PAGES.
    Check if we need to add it.
    """
    # Check if there are questions between "Teoría General del Delito" and "Formas de participación"
    # that should be "Agravantes y atenuantes"
    pass


def validate_questions(questions):
    """Validate extracted questions and print statistics."""
    valid = []
    issues = []
    
    for i, q in enumerate(questions):
        problems = []
        
        if not q.get('question'):
            problems.append("no question text")
        if not q.get('options') or len(q['options']) < 3:
            problems.append(f"only {len(q.get('options', []))} options")
        if not q.get('correct'):
            problems.append("no correct answer")
        elif q['correct'] not in [o['letter'] for o in q.get('options', [])]:
            problems.append(f"correct answer '{q['correct']}' not in options")
        
        if problems:
            issues.append((i, problems, q.get('question', '???')[:80]))
        else:
            valid.append(q)
    
    print(f"\n{'='*60}")
    print(f"VALIDATION RESULTS")
    print(f"{'='*60}")
    print(f"Total extracted: {len(questions)}")
    print(f"Valid: {len(valid)}")
    print(f"Issues: {len(issues)}")
    
    if issues:
        print(f"\nFirst 20 issues:")
        for idx, problems, text in issues[:20]:
            print(f"  Q{idx}: {', '.join(problems)} - '{text}'")
    
    # Print topic summary
    print(f"\nBy topic:")
    topics = {}
    for q in valid:
        t = q['topic']
        topics[t] = topics.get(t, 0) + 1
    for t, count in sorted(topics.items()):
        print(f"  {t}: {count}")
    
    # Print subtopic summary
    print(f"\nBy subtopic:")
    subtopics = {}
    for q in valid:
        key = f"{q['topic']} > {q['subtopic']}"
        subtopics[key] = subtopics.get(key, 0) + 1
    for s, count in sorted(subtopics.items()):
        print(f"  {s}: {count}")
    
    return valid


def save_questions(questions):
    """Save questions to JS and JSON files."""
    # JS file
    js_content = "// Auto-generated question bank - Examen Complexivo Derecho 2026\n"
    js_content += f"// Total questions: {len(questions)}\n"
    js_content += f"// Generated from PDF extraction\n\n"
    js_content += "const QUESTIONS = " + json.dumps(questions, ensure_ascii=False, indent=2) + ";\n"
    
    with open(OUTPUT_JS, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print(f"\nSaved {len(questions)} questions to {OUTPUT_JS}")
    
    # JSON file for debugging
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    print(f"Debug JSON saved to {OUTPUT_JSON}")


def main():
    print("=" * 60)
    print("Extractor de Preguntas - Examen Complexivo Derecho 2026")
    print("=" * 60)
    
    questions = extract_questions()
    valid = validate_questions(questions)
    save_questions(valid)


if __name__ == '__main__':
    main()
