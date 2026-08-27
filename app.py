import os
import io
import time
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

# تهيئة المفتاح والعميل
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

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

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

# الشريط الجانبي
with st.sidebar:
    st.header("👤 السكرتير والمستشار الخاص")
    secretary_mode = st.selectbox(
        "شخصية وطبيعة الحوار:",
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
    st.caption("يعمل كعقلك المساعد لإدارة كافة المهام الفكرية، الإدارية، الحياتية، والتصميمية.")

st.title("🏛️ المنظومة الاستشارية والتنفيذية الشاملة")

tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🎙️ السكرتير الشخصي الصوتي",
    "📚 البحوث الحوزوية والعلمية",
    "📰 التحرير والإعلام الصحفي",
    "📄 فحص ومقارنة الوثائق",
    "🧭 القيادة والتخطيط والتقويم",
    "🌿 الاستشارات الحياتية والديكور",
    "📊 لوحة المؤشرات البيانية"
])

# --- التبويب 0: السكرتير الشخصي المباشر ---
with tab0:
    st.header("المحادثة والاستشارة الشخصية (صوت وكتابة)")
    audio_record = st.audio_input("🎙️ تحدث بصوتك مباشرة:")
    text_input_val = st.text_area("أو اكتب هنا تفاصيل ما تريده (شخصي، عام، أفكار، تنظيم وقت):", height=110)
    
    if st.button("إرسال للسكرتير", type="primary"):
        contents_list = []
        user_display = ""
        if audio_record is not None:
            audio_raw = audio_record.read()
            contents_list = [
                types.Part.from_bytes(data=audio_raw, mime_type="audio/wav"),
                f"أنت سكرتيري ومساعدي الشخصي الخاص في كل شؤون حياتي. أسلوبك: {secretary_mode}. استمع لما قلته وأجبني بحكمة ولباقة وحلول وافية."
            ]
            user_display = "🎤 [رسالة صوتية مسجلة]"
        elif text_input_val.strip():
            user_display = text_input_val
            contents_list = [
                f"""أنت سكرتيري ومساعدي الشخصي الشامل في كل شؤون حياتي وأفكاري وأعمالي.
الأسلوب: {secretary_mode}
الرسالة: {text_input_val}
أجبني بدقة، رتب الأولويات، وقدم المخرجات المطلوبة بأعلى جودة."""
            ]
        
        if contents_list:
            with st.spinner("السكرتير يجيب..."):
                try:
                    res = generate_with_retry(contents_list)
                    reply = res.text
                    st.session_state.chat_history.append({"user": user_display, "bot": reply})
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
            st.warning("يرجى إدخال رسالة صوتية أو نص.")

    if st.session_state.chat_history:
        st.markdown("---")
        st.subheader("📜 أرشيف المحادثة:")
        for ch in reversed(st.session_state.chat_history[-4:]):
            st.chat_message("user").write(ch["user"])
            st.chat_message("assistant").write(ch["bot"])

# --- التبويب 1: البحوث الحوزوية والعلمية ---
with tab1:
    st.header("كتابة وتحقيق الأبحاث الحوزوية والمقالات العلمية")
    c1, c2 = st.columns(2)
    with c1:
        r_type = st.selectbox("المجال:", ["بحث فقهي / أصولي استدلالي", "بحث كلامي وعقائدي", "دراسة قرآنية وحديثية", "تحقيق تراثي ورجالي", "مقال فكري فلسفي", "بحث علمي أكاديمي محكم"])
    with c2:
        r_meth = st.selectbox("المنهجية:", ["استدلالي حوزوي رصين (أقوال، أدلة، مناقشة، المختار)", "تحقيقي أكاديمي موثق بالمصادر", "مقال تحليلي فكري"])
    
    topic = st.text_input("عنوان البحث أو القضية:")
    r_notes = st.text_area("المحاور، الأدلة، أو النصوص المطلوبة (اختياري):", height=110)
    
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
                    st.markdown("### 📜 النص العلمي المحرر:")
                    st.markdown(res.text)
                    docx_res = create_docx_download(res.text, f"بحث: {topic}")
                    st.download_button("📥 تحميل البحث (Word)", docx_res, file_name=f"{topic[:20]}.docx")
                except Exception as err:
                    st.error(f"خطأ: {err}")
        else:
            st.warning("يرجى إدخال الموضوع.")

# --- التبويب 2: التحرير والإعلام الصحفي ---
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
                    st.markdown("### 📰 المادة الصحفية:")
                    st.markdown(res.text)
                    docx_res = create_docx_download(res.text, "المادة الإعلامية")
                    st.download_button("📥 تحميل المادة (Word)", docx_res, file_name="Press_Release.docx")
                except Exception as err:
                    st.error(f"خطأ: {err}")
        else:
            st.warning("يرجى إدخال الوقائع.")

# --- التبويب 3: فحص ومقارنة الوثائق ---
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
                        st.markdown("### 📋 التقرير:")
                        st.markdown(res.text)
                        docx_res = create_docx_download(res.text, "تقرير تدقيق وثيقة")
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
                        st.markdown("### 🔍 تقرير المقارنة:")
                        st.markdown(res.text)
                        docx_res = create_docx_download(res.text, "تقرير المقارنة")
                        st.download_button("📥 تحميل التقرير (Word)", docx_res, file_name="Comparison.docx")
                    except Exception as err:
                        st.error(f"خطأ: {err}")

# --- التبويب 4: القيادة والتخطيط والتقويم ---
with tab4:
    st.header("إدارة الأعمال، التخطيط الاستراتيجي، والتقييم والتقويم")
    mgmt_mode = st.radio("نوع المهمة:", ["بناء خطة استراتيجية ومؤشرات أداء", "تقييم وتقويم الأداء وكشف الانحرافات", "حلول قيادية وإدارة أزمات/فرق عمل"], horizontal=True)
    
    if mgmt_mode == "بناء خطة استراتيجية ومؤشرات أداء":
        g_text = st.text_area("الأهداف والموارد المتاحة:", height=110)
        t_frame = st.selectbox("النطاق الزمني:", ["شهري", "فصلي (3 أشهر)", "سنوي"])
        if st.button("توليد الخطة"):
            if g_text:
                with st.spinner("جاري بناء الخطة القيادية..."):
                    try:
                        p = f"الأهداف: {g_text} | المدى: {t_frame}\nالمطلوب: خطة مراحل تنفيذية، مصفوفة مسؤوليات (RACI)، وجدول مؤشرات أداء قيادية (SMART KPIs)."
                        res = generate_with_retry(p)
                        st.markdown(res.text)
                        docx_res = create_docx_download(res.text, "الخطة الاستراتيجية")
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
                        p = f"المخطط: {plan_in}\nالمنجز: {act_in}\nالمطلوب: تقييم تفصيلي، تحديد نسبة الإنجاز والقصور، وخطة تقويم وتصحيح عاجلة للمتعثرات."
                        res = generate_with_retry(p)
                        st.markdown(res.text)
                        docx_res = create_docx_download(res.text, "تقرير التقييم والتقويم")
                        st.download_button("📥 تحميل التقرير (Word)", docx_res, file_name="Evaluation.docx")
                    except Exception as err:
                        st.error(f"خطأ: {err}")
    else:
        crisis_in = st.text_area("التحدي الإداري، الأزمة، أو المشكلة القيادية:")
        if st.button("تقديم الحل القيادي"):
            if crisis_in:
                with st.spinner("جاري صياغة التوجيه القيادي..."):
                    try:
                        p = f"أنت خبير قيادة وإدارة مؤسسية. المشكلة/التحدي: {crisis_in}\nالمطلوب: تشخيص جذور المشكلة، استراتيجية قيادية للتعامل معها، خطوات عملية لتوجيه فريق العمل واحتواء الأزمة."
                        res = generate_with_retry(p)
                        st.markdown(res.text)
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
    consult_input = st.text_area("تفاصيل السؤال أو المساحة أو الحالة المراد استشارتها:", height=120)
    
    if st.button("طلب الاستشارة"):
        if consult_input.strip():
            with st.spinner("المستشار التخصصي يحلل ويقدم الحلول..."):
                try:
                    p = f"""أنت مستشار خبير في {consult_type}.
تفاصيل الاستفسار:
{consult_input}

المطلوب:
- تقديم نصيحة تفصيلية، دقيقة، وعملية قابلة للتطبيق فوراً.
- إذا كان ديكور: حدد توزيع المساحة، تناسق الألوان، الإضاءة، واختيار المواد.
- إذا كان زراعة: حدد نوع التربة، الري، التسميد، وحلول الآفات.
- إذا كانت صحية: قدم إرشادات نمط الحياة والعافية العامة مع التنبيه بضرورة مراجعة الطبيب المختص للحالات السريرية.
- إذا كانت اجتماعية: قدم حلولاً نفسية واجتماعية مبنية على الحكمة والاتزان."""
                    res = generate_with_retry(p)
                    st.markdown(res.text)
                    docx_res = create_docx_download(res.text, f"استشارة - {consult_type}")
                    st.download_button("📥 تحميل الاستشارة (Word)", docx_res, file_name="Consultation.docx")
                except Exception as err:
                    st.error(f"خطأ: {err}")
        else:
            st.warning("يرجى إدخال تفاصيل الاستشارة.")

# --- التبويب 6: لوحة المؤشرات البيانية ---
with tab6:
    st.header("📊 لوحة قياس الأداء والمتابعة البيانية")
    default_df = {
        "المسار / المهمة": ["الشؤون الشخصية والمتابعة", "البحوث والتحقيق", "الإعلام والنشر", "التدقيق الإداري", "المشاريع الحياتية والتطوير"],
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
