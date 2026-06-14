import zipfile
import xml.etree.ElementTree as ET

def extract_docx_headings(docx_path):
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    headings = []
    
    with zipfile.ZipFile(docx_path) as z:
        with z.open("word/document.xml") as f:
            tree = ET.parse(f)
            root = tree.getroot()
            
            for p in root.findall(".//w:p", ns):
                pStyle = p.find(".//w:pStyle", ns)
                is_heading = False
                if pStyle is not None:
                    style_val = pStyle.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val")
                    if style_val and ("Heading" in style_val or style_val.isdigit()):
                        is_heading = True
                
                texts = [t.text for t in p.findall(".//w:t", ns) if t.text]
                full_text = "".join(texts).strip()
                
                if full_text:
                    if is_heading or ("第" in full_text and "章" in full_text and (len(full_text) < 50)):
                        headings.append(full_text)
                    elif any(full_text.startswith(str(i) + ".") for i in range(1, 10)) and len(full_text) < 100:
                        headings.append(full_text)
                        
    return headings

path = r"C:\Users\翁艺恺\Desktop\UserStoryLLM\backend\知识融入大语言模型的智能用户故事生成系统设计与实现.docx"
all_headings = extract_docx_headings(path)

chapters = [h for h in all_headings if ("第" in h and "章" in h)]
ch4_title = ""
ch4_subsections = []
in_ch4 = False

for h in all_headings:
    if "第" in h and "章" in h:
        if "第4章" in h:
            ch4_title = h
            in_ch4 = True
        else:
            in_ch4 = False
    elif in_ch4:
        if h.startswith("4."):
            ch4_subsections.append(h)

print("--- ALL_HEADINGS_START ---")
for c in chapters:
    print(c)
print("--- CH4_TITLE_START ---")
print(ch4_title)
print("--- CH4_SUBSECTIONS_START ---")
for s in ch4_subsections:
    print(s)
