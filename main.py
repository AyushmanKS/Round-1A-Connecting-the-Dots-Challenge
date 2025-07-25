import fitz
import json
import os
import collections
import re

INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"

NEGATIVE_KEYWORDS = [
    'requirement', 'criteria', 'points', 'description', 'total', 'max',
    'figure', 'table', 'page', 'chapter', 'appendix a', 'appendix b'
]

def looks_like_table_row(text):
    return len(re.findall(r'\s{2,}', text)) >= 2

def is_valid_heading_candidate(text):
    text_lower = text.lower().strip()
    if not text_lower:
        return False
    if len(text.split()) == 1 and len(text) < 4:
        return False
    if len(text.split()) > 15:
        return False
    if text.strip().endswith(('.', ':', ',')) or 'http' in text_lower:
        return False
    if any(keyword in text_lower for keyword in NEGATIVE_KEYWORDS):
        return False
    if looks_like_table_row(text_lower):
        return False
    return True

def analyze_and_map_styles(doc):
    styles = collections.defaultdict(int)
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        is_bold = "bold" in span["font"].lower()
                        style = (round(span["size"]), is_bold)
                        styles[style] += len(span["text"])

    if not styles:
        return {}, 12

    body_style = max(styles, key=styles.get)
    body_size = body_style[0]

    heading_styles = {
        style for style in styles
        if style[0] > body_size or (style[0] == body_size and style[1] and not body_style[1])
    }

    ranked_styles = sorted(list(heading_styles), key=lambda s: (s[0], s[1]), reverse=True)

    style_to_level_map = {}
    if len(ranked_styles) > 0:
        style_to_level_map[ranked_styles[0]] = "H1"
    if len(ranked_styles) > 1:
        style_to_level_map[ranked_styles[1]] = "H2"
    if len(ranked_styles) > 2:
        style_to_level_map[ranked_styles[2]] = "H3"
    for i in range(3, len(ranked_styles)):
        style_to_level_map[ranked_styles[i]] = "H3"

    return style_to_level_map

def extract_outline_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening {pdf_path}: {e}")
        return None

    style_level_map = analyze_and_map_styles(doc)

    candidates = []
    seen_texts = set()
    for page_num, page in enumerate(doc, start=1):
        blocks = sorted(page.get_text("dict")["blocks"], key=lambda b: b['bbox'][1])
        for block in blocks:
            if "lines" in block:
                full_text = " ".join(s['text'] for l in block['lines'] for s in l['spans']).strip()

                if full_text.lower() in seen_texts or not is_valid_heading_candidate(full_text):
                    continue

                first_span = block["lines"][0]["spans"][0]
                is_bold = "bold" in first_span["font"].lower()
                style_tuple = (round(first_span["size"]), is_bold)

                if style_tuple in style_level_map:
                    candidates.append({
                        'text': full_text,
                        'page': page_num,
                        'level': style_level_map[style_tuple]
                    })
                    seen_texts.add(full_text.lower())

    outline = []
    last_h1 = None
    last_h2 = None
    for cand in candidates:
        level = cand['level']
        if level == "H2" and not last_h1: level = "H1"
        if level == "H3" and not last_h2: level = "H2"
        if level == "H2" and not last_h1: level = "H1" # Redundant but safe

        if level == "H1":
            last_h1 = cand
            last_h2 = None
        elif level == "H2":
            last_h2 = cand

        outline.append({"level": level, "text": cand['text'], "page": cand['page']})

    title = os.path.basename(os.path.splitext(pdf_path)[0]).replace('_', ' ').replace('-', ' ')
    if doc.metadata.get('title'):
        title = doc.metadata.get('title')
    elif outline and outline[0]['level'] == 'H1':
        # Assume the first H1 is the title and remove it from the outline
        title = outline[0]['text']
        outline.pop(0)

    return {"title": title, "outline": outline}


def main():
    print("Starting PDF processing...")
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print("No PDF files found in /app/input")
        return
    for pdf_filename in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, pdf_filename)
        json_filename = os.path.splitext(pdf_filename)[0] + ".json"
        # THIS IS THE LINE THAT WAS FIXED
        json_path = os.path.join(OUTPUT_DIR, json_filename)
        
        print(f"Processing {pdf_filename}...")
        structured_data = extract_outline_from_pdf(pdf_path)
        if structured_data:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(structured_data, f, indent=2, ensure_ascii=False)
            print(f"Successfully created {json_filename}")
    print("Processing complete.")

if __name__ == "__main__":
    main()