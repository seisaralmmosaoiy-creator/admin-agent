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

st.set_page_config(page_title="الوكيل الاستشاري والتنفيذي الذكي", layout="wide", page_icon="⚡")

# --- تنظيف النصوص من أي طوابع زمنية صوتية ---
def clean_text_output(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r'\b\d{1,2}:\d{2}\b', '', text)
    cleaned = re.sub(r' +', ' ', cleaned)
    return cleaned.strip()

# --- قاعدة البيانات المحلية الدائمة (SQLite) ---
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
        st.error(f"خطأ أرشفة: {e}")

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

def get_recent_context():
    """استرجاع آخر العمليات لربط السياق والقرارات بذكاء"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT category, title, response FROM records ORDER BY id DESC LIMIT 3")
        rows = c.fetchall()
        conn.close()
        if not rows:
            return ""
        ctx = "\n[السياق والقرارات الأخيرة السابقة المحفوظة لديك]:\n"
        for r in rows:
            ctx += f"- {r[0]} ({r[1]}): {r[2][:300]}...\n"
        return ctx
    except:
        return ""

def delete_record(record_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

init_db()

# --- إعداد اتصال الذكاء الاصطناعي بالنماذج الرسمية الحديثة ---
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ يرجى ضبط مفتاح GEMINI_API_KEY في إعدادات Secrets.")
    st.stop()

client = genai.Client(api_key=api_key.strip())

# النماذج الرسمية النشطة بالترتيب لضمان أسرع استجابة وأعلى سعة
MODELS = [
    "gemini-3.7-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-pro-preview"
]

def generate_with_retry(contents):
    last_err = None
    for model_name in MODELS:
        for attempt in range(2):
            try:
                return client.models.generate_content(
                    model=model_name,
                    contents=contents
                )
            except Exception as e:
                last_err = e
                err_str = str(e)
                # إذا كان النموذج غير مدعوم انتقل للذي بعده مباشرة
                if "404" in err_str or "NOT_FOUND" in err_str:
                    break
                # في حالات الضغط المؤقت
                if any(x in err_str for x in ["503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED"]):
                    time.sleep(2)
                    continue
                break
    raise Exception(f"خطأ في الاتصال: {last_err}")

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

def prepare_multimodal_payload(system_instruction, user_text, uploaded_file):
    payload = []
    file_info = ""
    if uploaded_file is not None:
        if uploaded_file.type.startswith("image/"):
            img = Image.open(uploaded_file)
            payload.append(img)
            file_info = f"\n[مرفق صورة: {uploaded_file.name}]"
        else:
            extracted = extract_text_from_file(uploaded_file)
            file_info = f"\n[محتوى المستند ({uploaded_file.name})]:\n{extracted[:10000]}\n"
            
    memory_context = get_recent_context()
    full_prompt = f"{system_instruction}\n{memory_context}\n{file_info}\n[طلب وتوجيه المدير]:\n{user_text}\n"
    payload.append(full_prompt)
    return payload

# --- الشريط الجانبي ---
with st.sidebar:
    st.header("⚡ إعدادات الوكيل المساعد")
    persona_mode = st.selectbox(
        "نمط الشخصية والذكاء:",
        [
            "مساعد تنفيذي فطن وشامل (يربط القرارات ويصيغ بدقة)",
            "مستشار استراتيجي وقانوني صارم",
            "محقق وباحث حوزوي وعلمي دقيق",
            "محرر صحفي وإعلامي محترف"
        ]
    )
    st.markdown("---")
    st.caption("🧠 نظام الذاكرة الفورية والنماذج السريعة مفعّل.")

st.title("🏛️ المنظومة التنفيذية والاستشارية المتكاملة")

tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab_arch = st.tabs([
    "⚡ السكرتير التنفيذي والمباشر",
    "📚 الأبحاث الحوزوية والمقالات",
    "📰 التحرير والإعلام الصحفي",
    "📄 فحص ومقارنة الوثائق",
    "🧭 القيادة والتخطيط والتقويم",
    "🌿 الاستشارات الحياتية والديكور",
    "📊 لوحة المؤشرات البيانية",
    "🗄️ الأرشيف والذاكرة الدائمة"
])

# 0. السكرتير التنفيذي المباشر
with tab0:
    st.header("السكرتير الخاص الفطن (إدارة، كتب رسمية، محاضر، وقضايا خاصة)")
    audio_record = st.audio_input("🎙️ تحدث بصوتك مباشرة:")
    sec_file = st.file_uploader("📎 أرفق ملفاً أو صورة (اختياري):", type=["pdf", "docx", "png", "jpg", "jpeg"], key="sec_file")
    sec_text = st.text_area("أو اكتب هنا التوجيه أو الموضوع المطلوب تنفيذه:", height=100)
    
    if st.button("تنفيذ المهمة عبر السكرتير", type="primary"):
        if audio_record or sec_file or sec_text.strip():
            with st.spinner("جاري التفكير وربط المعطيات والصياغة الفورية..."):
                try:
                    sys_inst = f"""أنت السكرتير والمساعد التنفيذي الخاص الأعلى كفاءة وفطنة. أسلوبك: {persona_mode}.
مهمتك:
1. فهم جوهر التوجيه فوراً وتحديد القالب بدقة (كتاب رسمي، محضر اجتماع، مذكرة داخلية، قرار إداري، أو تحليل شخصي).
2. التزم تماماً برغبة المدير: إذا طلب كتاباً رسمياً صغ كتاباً رسمياً متكاملاً، وإذا طلب محضراً صغ محضراً.
3. التنسيق المؤسسي الرصين: الديباجة، الرقم، التاريخ، متن القرار أو التوجيه، التوقيعات والجهات المبلغة.
4. يمنع منعاً باتاً وضع أي طوابع زمنية صوتية داخل النص."""
                    
                    contents = []
                    if audio_record:
                        audio_raw = audio_record.read()
                        contents.append(types.Part.from_bytes(data=audio_raw, mime_type="audio/wav"))
                        
                    payload = prepare_multimodal_payload(sys_inst, sec_text if sec_text.strip() else "نفذ المطلوب بدقة بناءً على المرفق.", sec_file)
                    contents.extend(payload)
                    
                    res = generate_with_retry(contents)
                    reply = clean_text_output(res.text)
                    
                    title = sec_text[:30] if sec_text.strip() else (sec_file.name if sec_file else "مهمة إدارية")
                    save_record("سكرتارية تنفيذية", title, sec_text, reply)
                    
                    st.markdown("### 📑 المخرج الصادر:")
                    st.markdown(reply)
                    
                    docx_out = create_docx_download(reply, title)
                    st.download_button("📥 تحميل المستند (Word)", docx_out, file_name=f"{title[:20]}.docx")
                except Exception as err:
                    st.error(f"تنبيه: {err}")
        else:
            st.warning("يرجى إدخال نص، تسجيل صوتي، أو إرفاق ملف.")

# 1. البحوث الحوزوية والعلمية
with tab1:
    st.header("الأبحاث الحوزوية والمقالات العلمية المحكمة")
    c1, c2 = st.columns(2)
    with c1:
        r_type = st.selectbox("المجال:", ["بحث فقهي / أصولي استدلالي", "بحث كلامي وعقائدي", "دراسة قرآنية وحديثية", "تحقيق تراثي ورجالي", "مقال فكري وفلسفي", "بحث علمي محكم"])
    with c2:
        r_meth = st.selectbox("المنهجية:", ["استدلالي حوزوي رصين (أقوال، أدلة، مناقشة، المختار)", "تحقيقي توثيقي بالمصادر", "مقال تحليلي فكري"])
    
    topic = st.text_input("موضوع البحث:")
    res_file = st.file_uploader("📎 أرفق وثيقة أو صورة مخطوطة (اختياري):", type=["pdf", "docx", "png", "jpg", "jpeg"], key="res_file")
    r_notes = st.text_area("المحاور أو الأدلة المراد تضمينها:", height=90)
    
    if st.button("تأصيل وكتابة البحث"):
        if topic.strip() or res_file or r_notes.strip():
            with st.spinner("جاري الاستدلال والتحرير العلمي..."):
                try:
                    sys_inst = f"""أنت محقق وباحث حوزوي رصين. التخصص: {r_type} | المنهج: {r_meth}.
المطلوب: تحرير محل النزاع، ثمرة البحث، سوق الأدلة والمناقشات (إن قيل... قلنا)، واختيار الرأي مع ثبت المصادر التراثية المعتمدة."""
                    payload = prepare_multimodal_payload(sys_inst, f"العنوان: {topic}\nالمحاور: {r_notes}", res_file)
                    res = generate_with_retry(payload)
                    reply = clean_text_output(res.text)
                    save_record("بحث علمي/حوزوي", topic if topic else "بحث علمي", r_notes, reply)
                    st.markdown(reply)
                    st.download_button("📥 تحميل البحث (Word)", create_docx_download(reply, topic), file_name="Research.docx")
                except Exception as err:
                    st.error(f"خطأ: {err}")
        else:
            st.warning("يرجى إدخال الموضوع أو المرفق.")

# 2. التحرير والإعلام الصحفي
with tab2:
    st.header("التحرير والإعلام الصحفي الاحترافي")
    c_t, c_n = st.columns(2)
    with c_t:
        n_type = st.selectbox("القالب:", ["خبر صحفي (هرم مقلوب)", "بيان رسمي وتصريح صحفي", "منشور منصات التواصل", "تقرير إخباري موسع"])
    with c_n:
        n_tone = st.selectbox("النبرة:", ["رصين وجذاب", "رسمي ومؤسسي", "حماسي وملهم"])
    
    press_file = st.file_uploader("📎 صورة أو مستند للفعالية:", type=["pdf", "docx", "png", "jpg", "jpeg"], key="p_file")
    n_facts = st.text_area("الوقائع والبيانات:", height=90)
    
    if st.button("صياغة الخبر الصحفي"):
        if n_facts.strip() or press_file:
            with st.spinner("جاري التحرير الصحفي..."):
                try:
                    sys_inst = f"أنت رئيس تحرير صحفي محترف. القالب: {n_type} | النبرة: {n_tone}. المطلوب: 3 عناوين لافتة، متن خبر متماسك، وصيغة مخصصة للسوشيال ميديا مع الوسوم."
                    payload = prepare_multimodal_payload(sys_inst, n_facts, press_file)
                    res = generate_with_retry(payload)
                    reply = clean_text_output(res.text)
                    save_record("إعلام وصحافة", n_facts[:30] if n_facts else "خبر صحفي", n_facts, reply)
                    st.markdown(reply)
                    st.download_button("📥 تحميل المادة (Word)", create_docx_download(reply, "مادة صحفية"), file_name="News.docx")
                except Exception as err:
                    st.error(f"خطأ: {err}")

# 3. فحص ومقارنة الوثائق
with tab3:
    st.header("فحص ومقارنة الوثائق والصور")
    d_mode = st.radio("العملية:", ["تدقيق وثيقة واحدة", "مقارنة نسختين"], horizontal=True)
    if d_mode == "تدقيق وثيقة واحدة":
        doc_f = st.file_uploader("ارفع الوثيقة أو الصورة:", type=["pdf", "docx", "png", "jpg", "jpeg"], key="doc_single")
        q_doc = st.text_input("المطلوب تدقيقه:")
        if st.button("بدء التدقيق"):
            if doc_f and q_doc:
                with st.spinner("جاري الفحص..."):
                    try:
                        payload = prepare_multimodal_payload(f"خبير تدقيق وتحليل وثائق. المهمة: {q_doc}", q_doc, doc_f)
                        res = generate_with_retry(payload)
                        reply = clean_text_output(res.text)
                        save_record("فحص وثائق", doc_f.name, q_doc, reply)
                        st.markdown(reply)
                        st.download_button("📥 تحميل التقرير (Word)", create_docx_download(reply, "تقرير فحص"), file_name="Doc_Check.docx")
                    except Exception as err:
                        st.error(f"خطأ: {err}")
    else:
        c_a, c_b = st.columns(2)
        with c_a:
            fa = st.file_uploader("الوثيقة 1:", type=["pdf", "docx"], key="fa")
        with c_b:
            fb = st.file_uploader("الوثيقة 2:", type=["pdf", "docx"], key="fb")
        if st.button("مقارنة الوثيقتين"):
            if fa and fb:
                with st.spinner("جاري كشف الفروق والتعارضات..."):
                    try:
                        ta = extract_text_from_file(fa)
                        tb = extract_text_from_file(fb)
                        p = f"قارن بدقة بين النصين واستخرج جدول الفروق والتعديلات والتعارضات:\n[1]:\n{ta[:4000]}\n\n[2]:\n{tb[:4000]}"
                        res = generate_with_retry([p])
                        reply = clean_text_output(res.text)
                        save_record("مقارنة وثائق", f"{fa.name} VS {fb.name}", "مقارنة", reply)
                        st.markdown(reply)
                        st.download_button("📥 تحميل تقرير المقارنة (Word)", create_docx_download(reply, "مقارنة"), file_name="Comparison.docx")
                    except Exception as err:
                        st.error(f"خطأ: {err}")

# 4. القيادة والتخطيط والتقويم
with tab4:
    st.header("القيادة، التخطيط الاستراتيجي، والتقييم والتقويم")
    m_mode = st.radio("المجال:", ["بناء خطة استراتيجية ومؤشرات SMART", "تقييم وتقويم الأداء ومعالجة الانحرافات", "توجيه قيادي وحل أزمات"], horizontal=True)
    m_file = st.file_uploader("📎 أرفق تقارير سابقة (اختياري):", type=["pdf", "docx", "png", "jpg", "jpeg"], key="m_f")
    m_text = st.text_area("البيانات أو الأهداف أو التحدي الإداري:", height=90)
    if st.button("توليد التحليل الإداري"):
        if m_text.strip() or m_file:
            with st.spinner("جاري التحليل..."):
                try:
                    payload = prepare_multimodal_payload(f"خبير قيادة وتخطيط تنفيذي. المطلوب: {m_mode}", m_text, m_file)
                    res = generate_with_retry(payload)
                    reply = clean_text_output(res.text)
                    save_record("إدارة وقيادة", m_mode, m_text[:30], reply)
                    st.markdown(reply)
                    st.download_button("📥 تحميل الخطة (Word)", create_docx_download(reply, m_mode), file_name="Plan.docx")
                except Exception as err:
                    st.error(f"خطأ: {err}")

# 5. الاستشارات الحياتية والديكور
with tab5:
    st.header("الاستشارات التخصصية: ديكور، زراعة، صحة، واجتماع")
    c_kind = st.selectbox("المجال:", ["🏡 ديكور وتصميم المساحات", "🌱 استشارات زراعية ونباتات", "🩺 نمط حياة صحي وعافية", "🤝 علاقات وتطوير ذات"])
    c_f = st.file_uploader("📎 صورة للمساحة أو النبات أو تقرير:", type=["pdf", "docx", "png", "jpg", "jpeg"], key="c_f")
    c_t = st.text_area("تفاصيل السؤال أو الاستفسار:", height=90)
    if st.button("طلب الرأي الاستشاري"):
        if c_t.strip() or c_f:
            with st.spinner("المستشار يحلل الحالة..."):
                try:
                    payload = prepare_multimodal_payload(f"مستشار خبير في {c_kind}. قدم رأياً عملياً دقيقاً ومباشراً.", c_t, c_f)
                    res = generate_with_retry(payload)
                    reply = clean_text_output(res.text)
                    save_record(f"استشارة: {c_kind}", c_t[:30] if c_t else c_kind, c_t, reply)
                    st.markdown(reply)
                    st.download_button("📥 تحميل الاستشارة (Word)", create_docx_download(reply, c_kind), file_name="Advice.docx")
                except Exception as err:
                    st.error(f"خطأ: {err}")

# 6. اللوحة البيانية
with tab6:
    st.header("لوحة قياس الأداء والمتابعة البيانية")
    base_data = {
        "المسار": ["السكرتارية والمتابعة", "البحوث والتحقيق", "الإعلام والنشر", "التدقيق الإداري", "المشاريع الحياتية"],
        "المستهدف (%)": [100, 100, 100, 100, 100],
        "المتحقق (%)": [95, 90, 85, 92, 80]
    }
    df = st.data_editor(pd.DataFrame(base_data), num_rows="dynamic")
    if not df.empty:
        df["الفجوة (%)"] = df["المستهدف (%)"] - df["المتحقق (%)"]
        fig = px.bar(df, x="المسار", y=["المتحقق (%)", "الفجوة (%)"], barmode="stack", color_discrete_sequence=["#2ecc71", "#e74c3c"])
        st.plotly_chart(fig, use_container_width=True)

# 7. الأرشيف والذاكرة الدائمة
with tab_arch:
    st.header("🗄️ الأرشيف والذاكرة التراكمية (SQLite)")
    col_q, col_c = st.columns([3, 1])
    with col_q:
        q_s = st.text_input("بحث في الذاكرة:")
    with col_c:
        cat_f = st.selectbox("التصنيف:", ["الكل", "سكرتارية تنفيذية", "بحث علمي/حوزوي", "إعلام وصحافة", "فحص وثائق", "إدارة وقيادة"])
    records = get_records(q_s, cat_f)
    if records:
        for r in records:
            rid, rtime, rcat, rtitle, rprompt, rresponse = r
            with st.expander(f"📌 [{rcat}] {rtitle} | 🕒 {rtime}"):
                st.markdown(f"**المدخلات:**\n{rprompt}")
                st.markdown("---")
                st.markdown(f"**القرار/المخرج:**\n{rresponse}")
                col_d, col_x = st.columns([2, 1])
                with col_d:
                    st.download_button("📥 تحميل Word", create_docx_download(rresponse, rtitle), file_name=f"{rtitle[:15]}.docx", key=f"d_{rid}")
                with col_x:
                    if st.button("🗑️ حذف", key=f"x_{rid}"):
                        delete_record(rid)
                        st.rerun()
    else:
        st.info("لا توجد سجلات محفوظة.")
