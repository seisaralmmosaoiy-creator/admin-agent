import os
import io
import time
import re
import sqlite3
import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from google.genai import types
from PIL import Image
from pypdf import PdfReader
import docx
from gtts import gTTS

st.set_page_config(page_title="المنظومة الاستشارية والتنفيذية الشاملة", layout="wide", page_icon="🏛️")

# --- دالة تنظيف التوقيتات الصوتية (Timestamps) ---
def clean_text_output(text: str) -> str:
    if not text:
        return ""
    # إزالة التوقيتات بصيغة الدقائق والثواني مثل 02:14 أو 01:57
    cleaned = re.sub(r'\b\d{1,2}:\d{2}\b', '', text)
    # تنظيف المسافات الزائدة
    cleaned = re.sub(r' +', ' ', cleaned)
    return cleaned.strip()

# --- تهيئة قاعدة البيانات المحلية الدائمة (SQLite) ---
DB_FILE = "archive.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            category TEXT,
            title TEXT,
            prompt TEXT,
            response TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_record(category, title, prompt, response):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO records (timestamp, category, title, prompt, response) VALUES (?, ?, ?, ?, ?)",
                  (ts, category, title, prompt, response))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"خطأ في حفظ الأرشيف: {e}")

def get_records(search_query="", category_filter="الكل"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    query = "SELECT id, timestamp, category, title, prompt, response FROM records WHERE 1=1"
    params = []
    
    if category_filter != "الكل":
        query += " AND category = ?"
        params.append(category_filter)
        
    if search_query.strip():
        query += " AND (title LIKE ? OR prompt LIKE ? OR response LIKE ?)"
        s = f"%{search_query.strip()}%"
        params.extend([s, s, s])
        
    query += " ORDER BY id DESC"
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

def delete_record(record_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

init_db()

# --- إعداد الذكاء الاصطناعي ---
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ يرجى ضبط مفتاح GEMINI_API_KEY في إعدادات Secrets.")
    st.stop()

client = genai.Client(api_key=api_key.strip())
MODEL_NAME = "gemini-3.6-flash"

def generate_with_retry(contents, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model=MODEL_NAME, contents=contents)
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
            raise e

def text_to_audio_bytes(text_arabic):
    try:
        clean_text = text_arabic.replace("*", "").replace("#", "")[:500]
        tts = gTTS(text=clean_text, lang='ar', slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.getvalue()
    except Exception:
        return None

def extract_text_from_file(file):
    if file.name.endswith(".pdf"):
        reader = PdfReader(file)
        return "\n".join([p.extract_text() or "" for p in reader.pages])
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    return ""

def create_docx_download(content_text, title="المستند"):
    doc = docx.Document()
    doc.add_heading(title, level=0)
    for paragraph in content_text.split("\n"):
        if paragraph.strip():
            doc.add_paragraph(paragraph)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- الشريط الجانبي ---
with st.sidebar:
    st.header("👤 السكرتير والمستشار الخاص")
    secretary_mode = st.selectbox(
        "طبيعة ونبرة الحوار:",
        [
            "مساعد وسكرتير شخصي شامل (لكل شؤون الحياة والعمل)",
            "مستشار فكري وحكيم ناصح",
            "قائد ومدير أعمال استراتيجي",
            "محقق وباحث علمي دقيق",
            "خبير ديكور وتصميم داخلي",
            "مستشار زراعي واجتماعي"
        ]
    )
    voice_output = st.checkbox("🔊 تشغيل الرد الصوتي تلقائياً", value=True)
    st.markdown("---")
    st.caption("💾 جميع الطلبات والبحوث والمحادثات تؤرشف تلقائياً بشكل دائم خالية من التوقيتات الصوتية.")

st.title("🏛️ المنظومة الاستشارية والتنفيذية الشاملة")

tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab_arch = st.tabs([
    "🎙️ السكرتير الصوتي والشخصي",
    "📚 البحوث الحوزوية والعلمية",
    "📰 التحرير والإعلام الصحفي",
    "📄 فحص ومقارنة الوثائق",
    "🧭 القيادة والتخطيط والتقويم",
    "🌿 الاستشارات الحياتية والديكور",
    "📊 لوحة المؤشرات البيانية",
    "🗄️ الأرشيف الدائم والبحث"
])

# --- التبويب 0: السكرتير الشخصي ---
with tab0:
    st.header("المحادثة والاستشارة الشخصية المباشرة")
    audio_record = st.audio_input("🎙️ تحدث بصوتك مباشرة:")
    text_input_val = st.text_area("أو اكتب رسالتك/طلبك بالتفصيل هنا:", height=110)
    
    if st.button("إرسال للسكرتير", type="primary"):
        contents_list = []
        user_prompt_txt = ""
        if audio_record is not None:
            audio_raw = audio_record.read()
            contents_list = [
                types.Part.from_bytes(data=audio_raw, mime_type="audio/wav"),
                f"""أنت سكرتيري ومساعدي الشخصي الخاص في كل شؤون حياتي. أسلوبك: {secretary_mode}.
استمع لما قلته في هذا التسجيل ونفذ المطلوب بدقة ولباقة وتنسيق متقن.
تعليمات صارمة:
- يُمنع منعاً باتاً كتابة أي توقيتات زمنية أو طوابع صوتية (مثل 01:23 أو 02:14) في النص.
- اكتب المخرجات والكتب الرسمية بلغة عربية نظيفة ومترابطة وجاهزة للاعتماد المباشر."""
            ]
            user_prompt_txt = "🎤 [رسالة صوتية مسجلة]"
        elif text_input_val.strip():
            user_prompt_txt = text_input_val
            contents_list = [
                f"""أنت سكرتيري ومساعدي الشخصي الشامل في كل شؤون حياتي وأفكاري وأعمالي.
الأسلوب: {secretary_mode}
الرسالة: {text_input_val}
أجبني بدقة، رتب الأولويات، وقدم المخرجات المطلوبة بأعلى جودة وخالية من أي توقيتات."""
            ]
        
        if contents_list:
            with st.spinner("السكرتير يجيب وينسق المستند..."):
                try:
                    res = generate_with_retry(contents_list)
                    reply = clean_text_output(res.text)
                    
                    save_record("محادثة شخصية", user_prompt_txt[:30], user_prompt_txt, reply)
                    
                    st.markdown("### 💬 رد السكرتير:")
                    st.markdown(reply)
                    if voice_output:
                        audio_res = text_to_audio_bytes(reply)
                        if audio_res:
                            st.audio(audio_res, format="audio/mp3")
                    docx_out = create_docx_download(reply, "مخرجات السكرتير الشخصي")
                    st.download_button("📥 تحميل الرد (Word)", docx_out, file_name="Secretary_Note.docx")
                except Exception as err:
                    st.error(f"حدث خطأ: {err}")
        else:
            st.warning("يرجى إدخال تسجيل صوتي أو كتابة نص.")

# --- التبويب 1: البحوث الحوزوية ---
with tab1:
    st.header("كتابة وتحقيق الأبحاث الحوزوية والمقالات العلمية")
    c1, c2 = st.columns(2)
    with c1:
        r_type = st.selectbox("المجال:", ["بحث فقهي / أصولي استدلالي", "بحث كلامي وعقائدي", "دراسة قرآنية وحديثية", "تحقيق تراثي ورجالي", "مقال فكري فلسفي", "بحث علمي أكاديمي محكم"])
    with c2:
        r_meth = st.selectbox("المنهجية:", ["استدلالي حوزوي رصين (أقوال، أدلة، مناقشة، المختار)", "تحقيقي أكاديمي موثق بالمصادر", "مقال تحليلي فكري"])
    
    topic = st.text_input("عنوان البحث أو القضية:")
    r_notes = st.text_area("المحاور أو الأدلة المراد تضمينها (اختياري):", height=110)
    
    if st.button("كتابة وتأصيل البحث"):
        if topic.strip():
            with st.spinner("جاري التحقيق الاستدلالي..."):
                try:
                    p = f"""أنت باحث ومحقق حوزوي وأكاديمي خبير.
المجال: {r_type} | المنهج: {r_meth} | الموضوع: {topic}
المحاور: {r_notes if r_notes else 'تأصيل علمي شامل'}
المطلوب:
1. تحرير محل النزاع وثمرة البحث.
2. الهيكلية الاستدلالية بالأقوال، الأدلة، والمناقشات (إن قيل... قلنا).
3. المختار والتحقيق النهائي مع ثبت المصادر والمراجع التراثية/الأكاديمية."""
                    res = generate_with_retry(p)
                    reply = clean_text_output(res.text)
                    
                    save_record("بحث حوزوي/علمي", topic, r_notes, reply)
                    
                    st.markdown("### 📜 النص العلمي المحرر:")
                    st.markdown(reply)
                    docx_res = create_docx_download(reply, f"بحث: {topic}")
                    st.download_button("📥 تحميل البحث (Word)", docx_res, file_name=f"{topic[:20]}.docx")
                except Exception as err:
                    st.error(f"خطأ: {err}")
        else:
            st.warning("يرجى إدخال الموضوع.")

# --- التبويب 2: التحرير الصحفي ---
with tab2:
    st.header("صياغة الأخبار والبيانات الصحفية باحترافية")
    c_t, c_n = st.columns(2)
    with c_t:
        n_type = st.selectbox("القالب الصحفي:", ["خبر صحفي (هرم مقلوب)", "منشور منصات التواصل الاجتماعي (Facebook / X)", "بيان صحفي رسمي", "تقرير إخباري موسع"])
    with c_n:
        n_tone = st.selectbox("نبرة الخطاب:", ["احترافي رصين وجذاب", "حماسي وملهم", "رسمي دقيق", "تفاعلي ومختصر"])
    
    n_facts = st.text_area("الوقائع والبيانات الأساسية للخبر:", height=110)
    if st.button("صياغة المادة الإعلامية"):
        if n_facts.strip():
            with st.spinner("جاري التحرير الصحفي..."):
                try:
                    p = f"أنت رئيس تحرير محترف. القالب: {n_type} | النبرة: {n_tone}\nالوقائع: {n_facts}\nالمطلوب: 3 عناوين جذابة، متن خبر مهيكل، وصيغة مخصصة للسوشيال ميديا مع الوسوم المناسبة."
                    res = generate_with_retry(p)
                    reply = clean_text_output(res.text)
                    
                    save_record("إعلام وصحافة", n_facts[:30], n_facts, reply)
                    
                    st.markdown("### 📰 المادة الصحفية:")
                    st.markdown(reply)
                    docx_res = create_docx_download(reply, "المادة الإعلامية")
                    st.download_button("📥 تحميل المادة (Word)", docx_res, file_name="Press_Release.docx")
                except Exception as err:
                    st.error(f"خطأ: {err}")
        else:
            st.warning("يرجى إدخال الوقائع.")

# --- التبويب 3: فحص الوثائق ---
with tab3:
    st.header("فحص وتحليل ومقارنة الوثائق والصور")
    doc_mode = st.radio("نوع العملية:", ["تدقيق وثيقة واحدة أو صورة", "مقارنة وثيقتين لكشف التعارضات"], horizontal=True)
    if doc_mode == "تدقيق وثيقة واحدة أو صورة":
        up_file = st.file_uploader("ارفع وثيقة أو صورة:", type=["pdf", "docx", "png", "jpg", "jpeg"])
        q_text = st.text_input("المطلوب استخراجه أو تدقيقه:")
        if st.button("بدء التدقيق"):
            if up_file and q_text:
                with st.spinner("جاري الفحص..."):
                    try:
                        if up_file.type.startswith("image/"):
                            img = Image.open(up_file)
                            cnt = [img, f"المهمة: {q_text}\nحلل هذه الصورة/الوثيقة بدقة."]
                        else:
                            txt = extract_text_from_file(up_file)
                            cnt = [f"النص:\n{txt[:10000]}\n\nالمهمة: {q_text}"]
                        res = generate_with_retry(cnt)
                        reply = clean_text_output(res.text)
                        
                        save_record("فحص وثائق", up_file.name, q_text, reply)
                        
                        st.markdown("### 📋 التقرير:")
                        st.markdown(reply)
                        docx_res = create_docx_download(reply, "تقرير تدقيق وثيقة")
                        st.download_button("📥 تحميل التقرير (Word)", docx_res, file_name="Doc_Report.docx")
                    except Exception as err:
                        st.error(f"خطأ: {err}")
    else:
        col1, col2 = st.columns(2)
        with col1:
            fa = st.file_uploader("الوثيقة الأولى:", type=["pdf", "docx"], key="fa")
        with col2:
            fb = st.file_uploader("الوثيقة الثانية:", type=["pdf", "docx"], key="fb")
        if st.button("مقارنة الوثيقتين"):
            if fa and fb:
                with st.spinner("جاري استخراج المقارنة..."):
                    try:
                        ta = extract_text_from_file(fa)
                        tb = extract_text_from_file(fb)
                        p = f"قارن بين الوثيقتين بالتفصيل واستخرج جدول الفروق، التعارضات، والتوصيات:\n[1]:\n{ta[:5000]}\n\n[2]:\n{tb[:5000]}"
                        res = generate_with_retry(p)
                        reply = clean_text_output(res.text)
                        
                        save_record("مقارنة وثائق", f"{fa.name} VS {fb.name}", "مقارنة نسختين", reply)
                        
                        st.markdown("### 🔍 تقرير المقارنة:")
                        st.markdown(reply)
                        docx_res = create_docx_download(reply, "تقرير المقارنة")
                        st.download_button("📥 تحميل التقرير (Word)", docx_res, file_name="Comparison.docx")
                    except Exception as err:
                        st.error(f"خطأ: {err}")

# --- التبويب 4: القيادة والتخطيط ---
with tab4:
    st.header("إدارة الأعمال، التخطيط الاستراتيجي، والتقييم والتقويم")
    mgmt_mode = st.radio("نوع المهمة:", ["بناء خطة استراتيجية ومؤشرات أداء", "تقييم وتقويم الأداء وكشف الانحرافات", "حلول قيادية وإدارة أزمات"], horizontal=True)
    
    if mgmt_mode == "بناء خطة استراتيجية ومؤشرات أداء":
        g_text = st.text_area("الأهداف والموارد المتاحة:", height=110)
        t_frame = st.selectbox("النطاق الزمني:", ["شهري", "فصلي (3 أشهر)", "سنوي"])
        if st.button("توليد الخطة"):
            if g_text:
                with st.spinner("جاري بناء الخطة..."):
                    try:
                        p = f"الأهداف: {g_text} | المدى: {t_frame}\nالمطلوب: خطة مراحل تنفيذية، مصفوفة مسؤوليات (RACI)، وجدول مؤشرات أداء قيادية (SMART KPIs)."
                        res = generate_with_retry(p)
                        reply = clean_text_output(res.text)
                        save_record("خطة استراتيجية", g_text[:30], f"نطاق: {t_frame}", reply)
                        st.markdown(reply)
                        docx_res = create_docx_download(reply, "الخطة الاستراتيجية")
                        st.download_button("📥 تحميل الخطة (Word)", docx_res, file_name="Plan.docx")
                    except Exception as err:
                        st.error(f"خطأ: {err}")
    elif mgmt_mode == "تقييم وتقويم الأداء وكشف الانحرافات":
        plan_in = st.text_area("المخطط له / المستهدفات:")
        act_in = st.text_area("المنجز الفعلي على أرض الواقع:")
        if st.button("إجراء التقييم والتقويم"):
            if plan_in and act_in:
                with st.spinner("جاري التقييم..."):
                    try:
                        p = f"المخطط: {plan_in}\nالمنجز: {act_in}\nالمطلوب: تقييم تفصيلي، نسبة الإنجاز، وخطة تصحيح عاجلة."
                        res = generate_with_retry(p)
                        reply = clean_text_output(res.text)
                        save_record("تقييم وتقويم", "مقارنة منجز", f"مخطط: {plan_in[:30]}", reply)
                        st.markdown(reply)
                        docx_res = create_docx_download(reply, "تقرير التقييم والتقويم")
                        st.download_button("📥 تحميل التقرير (Word)", docx_res, file_name="Evaluation.docx")
                    except Exception as err:
                        st.error(f"خطأ: {err}")
    else:
        crisis_in = st.text_area("التحدي الإداري أو المشكلة القيادية:")
        if st.button("تقديم الحل القيادي"):
            if crisis_in:
                with st.spinner("جاري إعداد الحل..."):
                    try:
                        p = f"المشكلة/التحدي: {crisis_in}\nالمطلوب: تشخيص الجذور، استراتيجية قيادية، وخطوات عملية لتوجيه الفريق."
                        res = generate_with_retry(p)
                        reply = clean_text_output(res.text)
                        save_record("حلول قيادية", crisis_in[:30], crisis_in, reply)
                        st.markdown(reply)
                    except Exception as err:
                        st.error(f"خطأ: {err}")

# --- التبويب 5: الاستشارات الحياتية والديكور ---
with tab5:
    st.header("🌿 المستشار التخصصي: الزراعة، الصحة العامة، العلاقات، والديكور")
    consult_type = st.selectbox(
        "مجال الاستشارة:",
        [
            "🏡 تصميم وديكورات المنازل والمساحات",
            "🌱 استشارات زراعية ونباتات وأسمدة",
            "🩺 إرشادات ونمط حياة صحي عام",
            "🤝 علاقات اجتماعية وأسرية وبناء الذات"
        ]
    )
    consult_input = st.text_area("تفاصيل السؤال أو الحالة:", height=110)
    
    if st.button("طلب الاستشارة"):
        if consult_input.strip():
            with st.spinner("المستشار يحلل..."):
                try:
                    p = f"أنت خبير في {consult_type}.\nالسؤال: {consult_input}\nالمطلوب: نصيحة دقيقة وعملية قابلة للتطبيق."
                    res = generate_with_retry(p)
                    reply = clean_text_output(res.text)
                    save_record(f"استشارة: {consult_type}", consult_input[:30], consult_input, reply)
                    st.markdown(reply)
                    docx_res = create_docx_download(reply, f"استشارة - {consult_type}")
                    st.download_button("📥 تحميل الاستشارة (Word)", docx_res, file_name="Consultation.docx")
                except Exception as err:
                    st.error(f"خطأ: {err}")
        else:
            st.warning("يرجى إدخال التفاصيل.")

# --- التبويب 6: اللوحة البيانية ---
with tab6:
    st.header("📊 لوحة قياس الأداء والمتابعة البيانية")
    default_df = {
        "المسار / المهمة": ["الشؤون الشخصية والمتابعة", "البحوث والتحقيق", "الإعلام والنشر", "التدقيق الإداري", "المشاريع الحياتية"],
        "المستهدف (%)": [100, 100, 100, 100, 100],
        "المتحقق الفعلي (%)": [95, 90, 85, 92, 80]
    }
    df = st.data_editor(pd.DataFrame(default_df), num_rows="dynamic")
    if not df.empty:
        df["الفجوة (%)"] = df["المستهدف (%)"] - df["المتحقق الفعلي (%)"]
        fig = px.bar(
            df, 
            x="المسار / المهمة", 
            y=["المتحقق الفعلي (%)", "الفجوة (%)"],
            title="مقارنة الإنجاز الفعلي مقابل الفجوة المتبقية",
            barmode="stack",
            color_discrete_sequence=["#2ecc71", "#e74c3c"]
        )
        st.plotly_chart(fig, use_container_width=True)

# --- التبويب 7: الأرشيف الدائم والبحث (SQLite) ---
with tab_arch:
    st.header("🗄️ الأرشيف الدائم وقاعدة البيانات")
    st.write("استعرض، ابحث، أو أعد تحميل أي بحث، مستند، أو محادثة تم حفظها في النظام.")
    
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        s_query = st.text_input("🔍 ابحث في الأرشيف (بالكلمة أو العنوان أو المحتوى):", placeholder="اكتب للبحث...")
    with col_s2:
        cat_filter = st.selectbox(
            "تصفية حسب التصنيف:",
            ["الكل", "محادثة شخصية", "بحث حوزوي/علمي", "إعلام وصحافة", "فحص وثائق", "مقارنة وثائق", "خطة استراتيجية", "تقييم وتقويم", "حلول قيادية", "استشارة: 🏡 تصميم وديكورات المنازل والمساحات", "استشارة: 🌱 استشارات زراعية ونباتات وأسمدة", "استشارة: 🩺 إرشادات ونمط حياة صحي عام", "استشارة: 🤝 علاقات اجتماعية وأسرية وبناء الذات"]
        )
        
    records = get_records(s_query, cat_filter)
    st.caption(f"عدد السجلات المطابقة: {len(records)}")
    
    if records:
        for r in records:
            r_id, r_time, r_cat, r_title, r_prompt, r_response = r
            with st.expander(f"📌 [{r_cat}] {r_title} | 🕒 {r_time}"):
                st.markdown(f"**الطلب / المدخلات:**\n{r_prompt}")
                st.markdown("---")
                st.markdown(f"**المخرج الناتج:**\n{r_response}")
                
                col_d1, col_d2 = st.columns([2, 1])
                with col_d1:
                    d_file = create_docx_download(r_response, r_title)
                    st.download_button("📥 تحميل نسخة Word مجدداً", d_file, file_name=f"Archive_{r_id}.docx", key=f"dl_{r_id}")
                with col_d2:
                    if st.button("🗑️ حذف من الأرشيف", key=f"del_{r_id}"):
                        delete_record(r_id)
                        st.rerun()
    else:
        st.info("لا توجد سجلات محفوظة مطابقة لبحثك.")
