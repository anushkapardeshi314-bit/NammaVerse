import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import fitz
import io, os, re, json, hashlib, time
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="NammaVerse | Kannada AI", page_icon="ಕ", layout="wide", initial_sidebar_state="expanded")

# -------------------- Visual system --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Noto+Sans+Kannada:wght@400;500;600;700&display=swap');
:root { --ink:#182321; --muted:#62716c; --cream:#f7f5ef; --green:#164e3b; --lime:#c7f36b; --line:#e3e7df; }
html, body, [class*="css"] { font-family:'DM Sans','Noto Sans Kannada',sans-serif; }
.stApp { background:var(--cream); color:var(--ink); }
.block-container { padding-top:1.4rem; max-width:1400px; }
[data-testid="stSidebar"] { background:#102f27; }
[data-testid="stSidebar"] * { color:#f4f7ef !important; }
.hero { background:linear-gradient(120deg,#123c30 0%,#1c5a43 65%,#397553 100%); padding:2.2rem 2.4rem; border-radius:26px; color:white; position:relative; overflow:hidden; }
.hero:after { content:'ಕ'; position:absolute; right:4%; top:-80px; font-size:300px; color:rgba(255,255,255,.06); font-family:'Noto Sans Kannada',sans-serif; }
.eyebrow { color:#c7f36b; font-size:.78rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; }
.hero h1 { font-size:clamp(2.3rem,5vw,4.5rem); line-height:1.04; margin:.55rem 0 1rem; color:white; font-weight:700; }
.hero p { max-width:760px; color:#e0eee6; font-size:1.05rem; line-height:1.65; }
.pill { display:inline-block; border:1px solid rgba(255,255,255,.28); border-radius:999px; padding:.35rem .75rem; margin:.2rem .3rem .1rem 0; font-size:.78rem; color:#f5faef; }
.section-title { font-size:1.6rem; font-weight:700; margin:1.2rem 0 .25rem; color:#163c30; }
.section-sub { color:#65736d; margin-bottom:1rem; }
.card { background:#fff; border:1px solid var(--line); border-radius:18px; padding:1.1rem 1.2rem; min-height:145px; box-shadow:0 5px 18px rgba(19,55,41,.035); }
.card h3 { font-size:1.05rem; margin:.25rem 0 .45rem; color:#163c30; }
.card p { color:#62716c; font-size:.91rem; line-height:1.5; margin:0; }
.card .icon { font-size:1.55rem; }
.small-note { color:#62716c; font-size:.84rem; }
div.stButton > button { border-radius:12px; font-weight:650; border:1px solid #d7e0d6; }
div.stButton > button[kind="primary"] { background:#174e3a; border-color:#174e3a; color:white; }
div[data-testid="stMetric"] { background:white; padding:1rem; border:1px solid #e3e7df; border-radius:15px; }
hr { border-color:#e2e7df; }
</style>
""", unsafe_allow_html=True)

if "docs" not in st.session_state: st.session_state.docs = []
if "active_text" not in st.session_state: st.session_state.active_text = ""
if "active_name" not in st.session_state: st.session_state.active_name = ""
if "history" not in st.session_state: st.session_state.history = []

with st.sidebar:
    st.markdown("## ಕ NammaVerse")
    st.caption("Kannada, connected to everyone.")
    page = st.radio("EXPLORE", [
        "Home", "Document Studio", "Ask Your Document", "Kannada Learning", 
        "Voice & Pronunciation", "Namma Heritage Map", "Karnataka Travel Planner",
        "My Library", "Impact & Quality"
    ], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**One language. Many journeys.**")
    st.caption("Digitize • Learn • Speak • Explore")
    st.markdown("---")
    st.caption("Prototype note: OCR, speech and AI quality depend on installed models/services. Review important outputs against the original source.")

# -------------------- Helpers --------------------
def enhance_image(img, mode="Balanced"):
    img = img.convert("RGB")
    if mode in ("Readable", "Old document"):
        img = ImageEnhance.Contrast(img).enhance(1.45 if mode == "Readable" else 1.8)
        img = ImageEnhance.Sharpness(img).enhance(1.6)
        img = img.filter(ImageFilter.MedianFilter(size=3))
    elif mode == "Handwriting":
        img = ImageEnhance.Contrast(img).enhance(1.2)
        img = ImageEnhance.Sharpness(img).enhance(1.3)
    return img

def ocr_image(img, lang, mode):
    img = enhance_image(img, mode)
    config = "--psm 6"
    try:
        return pytesseract.image_to_string(img, lang=lang, config=config), img
    except Exception as e:
        return "", img

def extract_pdf(uploaded, lang, mode):
    data = uploaded.getvalue()
    doc = fitz.open(stream=data, filetype="pdf")
    page_texts = []
    preview = None
    for idx, page in enumerate(doc):
        native = page.get_text("text").strip()
        # If selectable text exists, preserve it. Otherwise OCR rendered page.
        if len(native) > 20:
            text = native
        else:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text, img = ocr_image(img, lang, mode)
            if preview is None: preview = img
        page_texts.append(f"--- Page {idx+1} ---\n{text.strip()}")
    return "\n\n".join(page_texts), preview, len(doc)

def simple_summary(text, max_sentences=5):
    text = re.sub(r'\s+', ' ', text).strip()
    if not text: return "No text available to summarize yet."
    parts = re.split(r'(?<=[.!?।])\s+', text)
    return " ".join(parts[:max_sentences])[:2200]

def extract_dates(text):
    patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
        r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'
    ]
    found=[]
    for p in patterns: found += re.findall(p, text, flags=re.I)
    return list(dict.fromkeys(found))

def get_keywords(text, limit=12):
    words = re.findall(r'[\w\u0C80-\u0CFF]{3,}', text.lower())
    stop = {"ಮತ್ತು","ಅಥವಾ","ಇದು","ಅವರು","ಇರುವ","ಮಾಡಲು","ಅದರ","ಎಂದು","with","that","this","from","have","will","your","you","the","and","for","are","was","were","not","can"}
    counts={}
    for w in words:
        if w not in stop: counts[w]=counts.get(w,0)+1
    return sorted(counts.items(), key=lambda x:x[1], reverse=True)[:limit]

def make_doc_record(name, text, kind):
    return {"name":name, "text":text, "kind":kind, "saved_at":datetime.now().strftime("%d %b %Y, %H:%M"), "chars":len(text)}

def set_active(name, text):
    st.session_state.active_name=name
    st.session_state.active_text=text

# -------------------- Pages --------------------
if page == "Home":
    st.markdown("""
    <div class="hero">
      <div class="eyebrow">THE KANNADA CULTURE + AI PLATFORM</div>
      <h1>NammaVerse<span style="color:#c7f36b">.</span></h1>
      <p>A living digital home for Kannada — turn documents into knowledge, practise real conversations, preserve local voices, and plan meaningful journeys across Karnataka.</p>
      <span class="pill">ಕನ್ನಡ OCR</span><span class="pill">AI learning</span><span class="pill">Voice-first</span><span class="pill">Culture & heritage</span><span class="pill">Travel planning</span>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    st.markdown('<div class="section-title">One platform. Six challenges. One connected experience.</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Designed around the way people actually use language: to learn, speak, understand documents, connect with culture, and explore places.</div>', unsafe_allow_html=True)
    cards = [
        ("📄","Document Intelligence","Extract Kannada text from scans, review uncertain content, summarize and search your documents."),
        ("🗣️","Voice of Kannada","Practise everyday phrases and use speech tools when a supported Kannada voice service is configured."),
        ("🌱","Learn Kannada","Learn useful phrases through situations, vocabulary cards, and mini practice activities."),
        ("🧭","Regional Heritage","Explore community-submitted regional words, expressions, stories, and cultural context."),
        ("🏛️","Karnataka Travel","Build an itinerary based on interests, time, budget, and preferred experiences."),
        ("♿","Access for Everyone","Readable layouts, copyable text, translation-ready workflows, and audio-friendly content.")
    ]
    cols=st.columns(3)
    for i,(icon,title,desc) in enumerate(cards):
        with cols[i%3]:
            st.markdown(f'<div class="card"><div class="icon">{icon}</div><h3>{title}</h3><p>{desc}</p></div>', unsafe_allow_html=True)
    st.write("")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Connected modules","6")
    c2.metric("Document workflow","OCR → Review → Understand")
    c3.metric("Design principle","Human verified")
    c4.metric("Built for","Kannada access")
    st.info("Start with **Document Studio** to try OCR, or open any module from the sidebar. This starter app uses a working local OCR pipeline; cloud AI and speech integrations can be connected later.")
    st.markdown("### What makes NammaVerse different?")
    st.write("Most tools solve one step. NammaVerse connects the full journey: **scan → correct → understand → listen → search → learn → explore**. It also keeps the original source visible so users can verify important details.")

elif page == "Document Studio":
    st.markdown('<div class="section-title">Document Studio</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">From a photo or scanned page to searchable, editable Kannada text.</div>', unsafe_allow_html=True)
    with st.container(border=True):
        c1,c2,c3=st.columns([1.4,1,1])
        with c1:
            uploaded=st.file_uploader("Upload image or PDF", type=["png","jpg","jpeg","webp","tif","tiff","pdf"])
        with c2:
            language=st.selectbox("OCR language", ["Kannada + English", "Kannada", "English"], index=0)
        with c3:
            mode=st.selectbox("Image enhancement", ["Balanced","Readable","Old document","Handwriting"])
        st.caption("Tip: use a clear, well-lit photo. Handwriting support depends heavily on the OCR model and sample quality.")
        if uploaded:
            if language=="Kannada + English": lang="kan+eng"
            elif language=="Kannada": lang="kan"
            else: lang="eng"
            if st.button("✨ Extract text", type="primary", use_container_width=True):
                with st.spinner("Preparing document and extracting text…"):
                    try:
                        if uploaded.name.lower().endswith(".pdf"):
                            text, preview, pages = extract_pdf(uploaded, lang, mode)
                            st.session_state.page_count=pages
                        else:
                            img=Image.open(uploaded)
                            text, preview=ocr_image(img, lang, mode)
                            st.session_state.page_count=1
                        st.session_state.active_text=text
                        st.session_state.active_name=uploaded.name
                        st.session_state.last_preview=preview
                        st.session_state.last_mode=mode
                        st.session_state.last_kind="PDF" if uploaded.name.lower().endswith(".pdf") else "Image"
                        st.success("Extraction complete. Review and correct the text before using it.")
                    except Exception as e:
                        st.error("Could not process this file. Check that Tesseract OCR and Kannada language data are installed. Details: " + str(e))
    if st.session_state.active_text:
        left,right=st.columns([1,1.2], gap="large")
        with left:
            st.markdown("#### Original / enhanced preview")
            preview=st.session_state.get("last_preview")
            if preview is not None: st.image(preview, use_container_width=True)
            else: st.info("For a text-based PDF, selectable text was extracted directly.")
            st.markdown("#### Quick quality signals")
            st.metric("Characters extracted", f"{len(st.session_state.active_text):,}")
            st.metric("Possible date strings", len(extract_dates(st.session_state.active_text)))
        with right:
            st.markdown("#### Review extracted text")
            edited=st.text_area("Editable OCR result", value=st.session_state.active_text, height=330, key="edited_ocr")
            st.session_state.active_text=edited
            b1,b2,b3=st.columns(3)
            b1.download_button("⬇️ Download TXT", data=edited, file_name="kannada_extracted_text.txt", mime="text/plain", use_container_width=True)
            b2.download_button("⬇️ Download JSON", data=json.dumps({"source":st.session_state.active_name,"text":edited,"reviewed_at":datetime.now().isoformat()}, ensure_ascii=False, indent=2), file_name="kannada_document.json", mime="application/json", use_container_width=True)
            if b3.button("＋ Save to Library", use_container_width=True):
                if not any(d["name"]==st.session_state.active_name for d in st.session_state.docs):
                    st.session_state.docs.append(make_doc_record(st.session_state.active_name, edited, st.session_state.get("last_kind","Document")))
                st.success("Saved to this session's library.")
        st.markdown("#### Understand this document")
        a,b,c=st.columns(3)
        with a:
            if st.button("🧠 Create quick summary", use_container_width=True):
                st.session_state.summary=simple_summary(edited)
        with b:
            if st.button("📅 Find dates", use_container_width=True):
                st.session_state.found_dates=extract_dates(edited)
        with c:
            if st.button("🔑 Find key terms", use_container_width=True):
                st.session_state.found_keywords=get_keywords(edited)
        if "summary" in st.session_state: st.info(st.session_state.summary)
        if "found_dates" in st.session_state: st.write("**Dates found:**", ", ".join(st.session_state.found_dates) if st.session_state.found_dates else "No obvious date patterns found.")
        if "found_keywords" in st.session_state: st.write("**Frequent terms:**", ", ".join([f"{w} ({n})" for w,n in st.session_state.found_keywords]) or "No terms found.")
        st.caption("OCR output is a draft, not a verified transcript. Check names, dates, numbers, legal or official details against the original scan.")
    else:
        st.markdown('<div class="card"><div class="icon">🪄</div><h3>Your document, made useful</h3><p>Upload a page to begin. You can edit the extracted result, download it, find dates, and save it to your temporary library.</p></div>', unsafe_allow_html=True)

elif page == "Ask Your Document":
    st.markdown('<div class="section-title">Ask Your Document</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Search and ask questions about the document you have extracted.</div>', unsafe_allow_html=True)
    text=st.session_state.active_text
    if not text:
        st.warning("First upload a document in Document Studio, then return here.")
    else:
        st.success(f"Active document: {st.session_state.active_name or 'Untitled document'}")
        query=st.text_input("Ask a question or search for a phrase", placeholder="e.g. What is this document about? / search for a date")
        if st.button("Search document", type="primary") and query:
            q=query.lower().strip()
            lines=[line.strip() for line in text.splitlines() if line.strip()]
            matches=[(i,line) for i,line in enumerate(lines) if q in line.lower()]
            if matches:
                st.markdown("### Matching passages")
                for i,line in matches[:10]:
                    st.markdown(f"- **Passage {i+1}:** {line}")
            else:
                terms=[t for t in re.findall(r'\w+',q) if len(t)>2]
                ranked=[]
                for i,line in enumerate(lines):
                    score=sum(1 for t in terms if t in line.lower())
                    if score: ranked.append((score,i,line))
                ranked.sort(reverse=True)
                if ranked:
                    st.markdown("### Closest passages")
                    for score,i,line in ranked[:8]:
                        st.markdown(f"- **Passage {i+1} · match score {score}:** {line}")
                else:
                    st.info("No matching passage found. Try a shorter keyword or another spelling.")
        st.markdown("### Quick actions")
        q1,q2,q3=st.columns(3)
        if q1.button("Summarize document"):
            st.info(simple_summary(text, 6))
        if q2.button("Show dates"):
            dates=extract_dates(text)
            st.write(dates if dates else "No obvious date patterns found.")
        if q3.button("Export searchable text"):
            st.download_button("Download TXT", text, file_name="document_search_text.txt", mime="text/plain")
        st.warning("This prototype uses keyword search, not a connected generative-AI model. AI answers with citations can be added by connecting a retrieval-augmented generation (RAG) service.")

elif page == "Kannada Learning":
    st.markdown('<div class="section-title">Kannada for Everyone</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Practical Kannada for everyday situations — start small, practise often.</div>', unsafe_allow_html=True)
    lessons={
      "Greetings":[("ನಮಸ್ಕಾರ","Namaskāra","Hello / Greetings"),("ಧನ್ಯವಾದಗಳು","Dhanyavādagaḷu","Thank you"),("ದಯವಿಟ್ಟು","Dayaviṭṭu","Please"),("ಕ್ಷಮಿಸಿ","Kṣamisi","Excuse me / Sorry")],
      "Travel":[("ಬಸ್ ನಿಲ್ದಾಣ ಎಲ್ಲಿದೆ?","Bus nilḍāṇa ellide?","Where is the bus station?"),("ಇದು ಎಷ್ಟು?","Idu eṣṭu?","How much is this?"),("ನನಗೆ ಸಹಾಯ ಬೇಕು","Nanage sahāya bēku","I need help")],
      "Food & shopping":[("ನೀರು ಬೇಕು","Nīru bēku","I need water"),("ಮೆನು ಕೊಡುತ್ತೀರಾ?","Menu koḍuttīrā?","Could you give me the menu?"),("ನಗದು ಅಥವಾ UPI?","Nagadu athavā UPI?","Cash or UPI?")],
      "Work & study":[("ನನಗೆ ಅರ್ಥವಾಯಿತು","Nanage arthavāyitu","I understood"),("ಮತ್ತೊಮ್ಮೆ ಹೇಳಿ","Mattomme hēḷi","Please say it again"),("ನಿಧಾನವಾಗಿ ಮಾತನಾಡಿ","Nidhānavāgi mātanāḍi","Please speak slowly")]
    }
    category=st.selectbox("Choose a situation", list(lessons.keys()))
    for kannada,roman,meaning in lessons[category]:
        st.markdown(f'<div class="card" style="min-height:90px;margin-bottom:10px"><h3 style="font-family:Noto Sans Kannada,sans-serif;font-size:1.35rem">{kannada}</h3><p><b>{roman}</b> · {meaning}</p></div>', unsafe_allow_html=True)
    st.markdown("### Quick practice")
    phrase=st.selectbox("Choose the meaning", [x[2] for x in lessons[category]])
    if st.button("Reveal Kannada phrase"):
        row=next(x for x in lessons[category] if x[2]==phrase)
        st.success(f"{row[0]}  ·  {row[1]}")
    st.caption("Romanization is approximate. Ask a Kannada speaker to review phrases before using them in formal or sensitive situations.")

elif page == "Voice & Pronunciation":
    st.markdown('<div class="section-title">Voice of Kannada</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">A voice-ready space for listening, speaking, and practising Kannada.</div>', unsafe_allow_html=True)
    st.info("This deployable starter includes text-to-speech where the browser supports it. Speech recognition varies by browser and device; cloud speech services can be integrated for stronger Kannada support.")
    voice_text=st.text_area("Kannada text to listen to", value="ನಮಸ್ಕಾರ! ಕನ್ನಡ ಕಲಿಯಲು ಸ್ವಾಗತ.", height=110)
    st.components.v1.html(f"""
    <div style="font-family:Arial,sans-serif;background:#fff;border:1px solid #e3e7df;border-radius:16px;padding:18px">
      <p style="color:#174e3a;font-weight:700;margin-top:0">Listen in your browser</p>
      <button id="speak" style="background:#174e3a;color:white;border:0;padding:11px 16px;border-radius:10px;cursor:pointer">▶ Play Kannada</button>
      <button id="stop" style="background:#edf2eb;color:#174e3a;border:0;padding:11px 16px;border-radius:10px;cursor:pointer">■ Stop</button>
      <p id="status" style="color:#62716c;font-size:13px">Voice availability depends on your device/browser.</p>
      <script>
        const text = {json.dumps(voice_text, ensure_ascii=False)};
        document.getElementById('speak').onclick = () => {{
          if (!('speechSynthesis' in window)) {{ document.getElementById('status').innerText='Speech synthesis is not supported here.'; return; }}
          window.speechSynthesis.cancel();
          const u = new SpeechSynthesisUtterance(text);
          const voices = window.speechSynthesis.getVoices();
          const v = voices.find(x => x.lang && x.lang.toLowerCase().startsWith('kn')) || voices.find(x => x.lang && x.lang.toLowerCase().startsWith('hi'));
          if (v) {{ u.voice=v; u.lang=v.lang; }} else {{ u.lang='kn-IN'; }}
          u.rate=0.85; window.speechSynthesis.speak(u);
          document.getElementById('status').innerText = v ? 'Using available voice: '+v.name : 'Requested Kannada voice; browser may substitute if unavailable.';
        }};
        document.getElementById('stop').onclick = () => window.speechSynthesis.cancel();
      </script>
    </div>
    """, height=170)
    st.markdown("### Pronunciation practice")
    st.write("1. Listen to a phrase.  2. Repeat it aloud.  3. Compare with a trusted native-speaker recording.  4. Practise in a real-life sentence.")
    st.caption("The browser speech demo is best-effort and does not score pronunciation. A dedicated Kannada speech API is needed for dependable speech recognition and feedback.")

elif page == "Namma Heritage Map":
    st.markdown('<div class="section-title">Namma Heritage Map</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">A community-led seed collection for regional Kannada words, expressions, and cultural context.</div>', unsafe_allow_html=True)
    st.warning("Entries below are starter examples for demonstration. Regional usage varies by community; verify entries with local speakers before publishing them as authoritative.")
    seed=[
      {"Region":"Mysuru","Expression":"ಏನ್ ಸಮಾಚಾರ?","Meaning":"What's the news? / How are things?","Context":"Informal greeting; usage varies"},
      {"Region":"North Karnataka","Expression":"ಏನ್ ಮಾಡ್ತಿದೀರೀ?","Meaning":"What are you doing?","Context":"Colloquial expression; local forms vary"},
      {"Region":"Coastal Karnataka","Expression":"ನಮಸ್ಕಾರ","Meaning":"Hello / Greetings","Context":"Common greeting; local languages and variants coexist"},
      {"Region":"Bengaluru","Expression":"ಸ್ವಲ್ಪ ನಿಧಾನವಾಗಿ ಹೇಳಿ","Meaning":"Please say it a little slowly","Context":"Useful everyday phrase"}
    ]
    if "heritage" not in st.session_state: st.session_state.heritage=seed
    with st.form("heritage_form"):
        c1,c2=st.columns(2)
        region=c1.text_input("Region / community")
        expression=c2.text_input("Kannada word or phrase")
        meaning=st.text_input("Meaning / translation")
        context=st.text_area("When is it used? Add cultural context or source.")
        submitted=st.form_submit_button("＋ Add community entry")
        if submitted:
            if region and expression and meaning:
                st.session_state.heritage.append({"Region":region,"Expression":expression,"Meaning":meaning,"Context":context or "Needs community review"})
                st.success("Added to this session. Review before public sharing.")
            else: st.error("Add a region, phrase, and meaning.")
    df=pd.DataFrame(st.session_state.heritage)
    filter_region=st.selectbox("Filter by region", ["All"]+sorted(df["Region"].unique().tolist()))
    if filter_region!="All": df=df[df["Region"]==filter_region]
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("Download entries as CSV", df.to_csv(index=False).encode("utf-8-sig"), "namma_heritage_entries.csv", "text/csv")
    st.caption("Production version: add consent, contributor attribution preferences, moderation, dialect labels, audio samples, and a source-verification workflow.")

elif page == "Karnataka Travel Planner":
    st.markdown('<div class="section-title">Karnataka Travel Planner</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">A flexible itinerary builder shaped by time, budget, and the kind of Karnataka you want to experience.</div>', unsafe_allow_html=True)
    with st.form("trip_form"):
        c1,c2,c3=st.columns(3)
        days=c1.slider("Trip length (days)",1,10,3)
        budget=c2.selectbox("Budget per person",["Budget","Comfort","Premium"])
        travel_type=c3.selectbox("Travel style",["Heritage & architecture","Nature & wildlife","Food & local culture","Spiritual & peaceful","Family-friendly","Mixed highlights"])
        start=c1.selectbox("Starting point",["Bengaluru","Mysuru","Mangaluru","Hubballi","Belagavi","Other"])
        pace=c2.selectbox("Pace",["Relaxed","Balanced","Packed"])
        transport=c3.selectbox("Transport",["Public transport","Car / taxi","Two-wheeler","Flexible"])
        submitted=st.form_submit_button("✨ Build my sample itinerary", type="primary")
    destinations={
      "Heritage & architecture":[("Bengaluru","City heritage, museums, gardens"),("Mysuru","Palaces, markets, cultural heritage"),("Hampi","Vijayanagara-era monuments"),("Badami","Rock-cut cave temples and architecture"),("Pattadakal","Chalukya-era temple complex")],
      "Nature & wildlife":[("Coorg","Coffee country and hill landscapes"),("Chikkamagaluru","Hill scenery and coffee estates"),("Jog Falls region","Waterfall viewpoints; seasonal conditions matter"),("Kabini region","Wildlife and river landscapes; permits may be needed"),("Gokarna","Coastal scenery and beaches")],
      "Food & local culture":[("Bengaluru","Regional food and markets"),("Mysuru","Mysore pak, markets, cultural sites"),("Dharwad","Local food traditions and music heritage"),("Udupi","Temple-town heritage and regional cuisine"),("Mangaluru","Coastal food and cultural mix")],
      "Spiritual & peaceful":[("Mysuru","Temples and cultural sites"),("Dharmasthala region","Pilgrimage and local heritage"),("Udupi","Krishna temple town"),("Sringeri","River valley and temple heritage"),("Belur & Halebidu","Hoysala temple architecture")],
      "Family-friendly":[("Mysuru","Palace, zoo, gardens"),("Bengaluru","Parks, museums, family attractions"),("Udupi","Coastal outings and cultural sites"),("Shivamogga region","Nature-oriented day trips"),("Hampi","Open-air heritage exploration")],
      "Mixed highlights":[("Bengaluru","Urban culture and gardens"),("Mysuru","Palace and cultural heritage"),("Coorg","Hill landscapes"),("Hampi","Historic ruins"),("Udupi","Coastal culture")]
    }
    if submitted:
        places=destinations[travel_type]
        if days==1: chosen=places[:1]
        else: chosen=[places[min(round(i*(len(places)-1)/max(days-1,1)),len(places)-1)] for i in range(days)]
        st.markdown("### Your draft itinerary")
        st.info(f"{days} day(s) · {budget} budget · {travel_type} · {pace.lower()} pace · transport: {transport}")
        for i,(place,desc) in enumerate(chosen,1):
            st.markdown(f'<div class="card" style="min-height:80px;margin-bottom:10px"><h3>Day {i} · {place}</h3><p>{desc}</p></div>', unsafe_allow_html=True)
        st.caption(f"Starting point: {start}. This is a draft route, not a live route or booking plan. Check travel time, opening hours, weather, accessibility, permits, and local conditions before departure.")
        itinerary="\n".join([f"Day {i}: {p} — {d}" for i,(p,d) in enumerate(chosen,1)])
        st.download_button("Download itinerary", itinerary, "karnataka_itinerary.txt", "text/plain")
    st.markdown("### Planning features to add next")
    st.write("Map-based routing • estimated journey times • seasonal recommendations • accessible travel filters • verified opening hours • Kannada phrase pack for each destination.")

elif page == "My Library":
    st.markdown('<div class="section-title">My Library</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Documents saved during this session.</div>', unsafe_allow_html=True)
    if not st.session_state.docs:
        st.info("Your library is empty. Extract a document and choose **Save to Library**.")
    else:
        df=pd.DataFrame([{k:d[k] for k in ["name","kind","saved_at","chars"]} for d in st.session_state.docs])
        st.dataframe(df, use_container_width=True, hide_index=True)
        chosen=st.selectbox("Open a saved document", [d["name"] for d in st.session_state.docs])
        doc=next(d for d in st.session_state.docs if d["name"]==chosen)
        st.text_area("Saved text", doc["text"], height=250, key="library_view")
        st.download_button("Download selected text", doc["text"], file_name=re.sub(r'[^A-Za-z0-9._-]','_',chosen)+".txt", mime="text/plain")
        if st.button("Delete selected document"):
            st.session_state.docs=[d for d in st.session_state.docs if d["name"]!=chosen]
            st.success("Deleted from this session.")
    st.caption("This starter library is session-only. Add authentication and persistent storage for a production application. Avoid uploading sensitive documents to a public demo.")

elif page == "Impact & Quality":
    st.markdown('<div class="section-title">Impact & Quality Lab</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Make language technology measurable, transparent, and worthy of trust.</div>', unsafe_allow_html=True)
    docs=st.session_state.docs
    c1,c2,c3=st.columns(3)
    c1.metric("Documents saved this session",len(docs))
    c2.metric("Characters in active document",f"{len(st.session_state.active_text):,}")
    c3.metric("Active document", "Yes" if st.session_state.active_text else "No")
    st.markdown("### Research evaluation checklist")
    st.write("Use a manually transcribed ground-truth set to evaluate printed Kannada, handwriting, old scans, low-resolution photos, and mixed Kannada-English pages separately.")
    checklist=[
      "Character Error Rate (CER) against verified transcripts",
      "Word Error Rate (WER) against verified transcripts",
      "OCR confidence calibration and uncertain-word review rate",
      "Processing time per page and failure rate",
      "Search retrieval quality (Precision@k / Recall@k)",
      "Question-answer grounding: every answer linked to a source passage",
      "Human correction time saved, measured in a small usability study",
      "Accessibility checks: keyboard-only use, contrast, text resizing, screen reader"
    ]
    for item in checklist: st.checkbox(item, key="check_"+hashlib.md5(item.encode()).hexdigest()[:8])
    st.markdown("### Trust and provenance")
    st.write("For each production document, store source filename, upload timestamp, OCR engine/version, preprocessing settings, reviewer edits, export history, and optional source citation. Keep the original file separate from corrected text.")
    st.warning("This app is a research prototype. It does not guarantee OCR accuracy, professional translation, legal interpretation, or live travel information.")

st.markdown("---")
st.markdown("<div style='text-align:center;color:#6a7771;font-size:.83rem;padding:.5rem 0 1rem'>ಕ NammaVerse · Kannada, connected to everyone · Built as a hackathon-ready prototype</div>", unsafe_allow_html=True)
