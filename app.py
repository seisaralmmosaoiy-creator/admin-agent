import os
import io
import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from PIL import Image
from pypdf import PdfReader
import docx

st.set_page_config(page_title="المنظومة الإدارية والعلمية الشاملة", layout="wide", page_icon="📚")

api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ يرجى ضبط مفتاح GEMINI_API_KEY في إعدادات Secrets.")
    st.stop()

client = genai.Client(api_key=api_key.strip())
MODEL_NAME = "gemini-3.6-flash"

if "history" not in st.session_state:
    st.session_state.history = []

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

with st.sidebar:
    st.header("⚙️ خيارات التخصيص العام")
    persona = st.selectbox(
        "نبرة الصياغة الإدارية والعامة:",
        [
            "تدقيق رقابي وقانوني صارم",
            "صياغة إدارية واستراتيجية متوازنة",
            "صياغة إعلامية وبيانات صحفية",
            "أسلوب تشغيلي وميداني مباشر"
        ]
    )
    st.markdown("---")
    st.subheader("🗂️ سجل العمليات")
    if st.session_state.history:
        for idx, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"{item['type']} - {item['time']}"):
                st.write(item["preview"][:150] + "...")
    else:
        st.caption("لا توجد مخرجات محفوظة بعد.")

st.title("🏛️ المنظومة الإدارية والعلمية والإعلامية الشاملة")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📚 البحوث الحوزوية والمقالات",
    "📰 التحرير والإعلام الصحفي",
    "📄 فحص ومقارنة الوثائق",
    "📊 التخطيط ومؤشرات KPIs",
    "📈 المتابعة وتحليل الفجوات",
    "📊 لوحة المؤشرات البيانية"
])

# --- التبويب 1: البحوث الحوزوية والمقالات ---
with tab1:
    st.header("كتابة وتحقيق الأبحاث الحوزوية والمقالات الفكرية")
    
    col_field, col_style = st.columns(2)
    with col_field:
        research_type = st.selectbox(
            "المجال العلمي / التخصص:",
            [
                "بحث فقهي / أصولي استدلالي",
                "بحث كلامي / عقائدي مقارن",
                "دراسة قرآنية وحديثية (تفسير، دراية، رجال)",
                "بحث تاريخي وتحقيقي تراثي",
                "مقال فكري وفلسفي معاصر",
                "دراسة أخلاقية وتربوية تخصصية"
            ]
        )
    with col_style:
        methodology = st.selectbox(
            "المنهج والأسلوب التحريري:",
            [
                "استدلالي حوزوي رصين (تحرير محل النزاع، الأقوال، الأدلة، المناقشة، المختار)",
                "تحقيقي أكاديمي موثق بالمصادر والمراجع التراثية",
                "مقال تحليلي فكري يخاطب النخب المعاصرة",
                "صياغة منبرية وتوجيهية محكمة"
            ]
        )

    topic = st.text_input("عنوان البحث أو القضية المراد معالجتها:", placeholder="مثال: قاعدة نفي السبيل وتطبيقاتها المعاصرة / حجية الخبر الموثوق...")
    raw_points = st.text_area(
        "المحاور، الأدلة المقترحة، أو النصوص المراد تضمينها (اختياري):",
        placeholder="أدخل الآيات، الروايات، أقوال الأعلام (كالشيخ الأنصاري، المحقق الخوئي، السيد الصدر وغيرهم)، أو الفروع المراد إدراجها...",
        height=130
    )

    if st.button("كتابة وتأصيل البحث / المقال", type="primary"):
        if topic.strip():
            with st.spinner("جاري التحرير الاستدلالي والتأصيل العلمي..."):
                try:
                    prompt = f"""أنت باحث ومحقق حوزوي خبير بالعلوم العقلية والنقلية ومنهجيات الاستدلال والتحقيق التراثي والأكاديمي.
المجال التخصصي: {research_type}
المنهج المتبع: {methodology}
موضوع البحث: {topic}
المحاور والمدخلات الإضافية: {raw_points if raw_points else 'توليد الهيكلية الشاملة وتأصيل الأدلة استناداً للمصادر المعتمدة'}

المطلوب صياغته بأعلى درجات الرصانة والدقة اللغوية والاصطلاحية:
1. المقدمة: تحرير محل النزاع، بيان أهمية البحث، وتحديد السؤال المحوري.
2. الهيكلية الاستدلالية:
   - عرض الأقوال والآراء بدقة ونسبة كل رأي لصاحبه أو للمدرسة الفكرية.
   - استعراض الأدلة (الكتاب، السنة، العقل، الإجماع/السيرة) مع وجه الاستدلال.
   - الإيرادات والمناقشات العلمية (إن قيل... قلنا / والملاحظ عليه...).
3. النتيجة والتحقيق المختار بدقة وتجرد علمي.
4. ثبت المصادر والمراجع التراثية أو الفكرية المقترحة لمزيد من التحقيق."""

                    res = client.models.generate_content(model=MODEL_NAME, contents=prompt)
                    st.markdown("### 📜 النص العلمي المحرر:")
                    st.markdown(res.text)
                    
                    st.session_state.history.append({"type": "بحث حوزوي/علمي", "time": pd.Timestamp.now().strftime("%H:%M:%S"), "preview": res.text})
                    docx_file = create_docx_download(res.text, f"بحث: {topic}")
                    st.download_button("📥 تحميل البحث بصيغة Word", docx_file, file_name=f"{topic[:25]}.docx")
                except Exception as err:
                    st.error(f"حدث خطأ أثناء معالجة الطلب: {err}")
        else:
            st.warning("يرجى إدخال عنوان أو موضوع البحث.")

# --- التبويب 2: التحرير والإعلام الصحفي ---
with tab2:
    st.header("صياغة الأخبار والبيانات الصحفية باحترافية")
    col_type, col_tone = st.columns(2)
    with col_type:
        news_type = st.selectbox(
            "نوع القالب الإعلامي:",
            [
                "خبر صحفي قياسي (أسلوب الهرم المقلوب)",
                "منشور تفاعلي لمنصات التواصل الاجتماعي (Facebook & X)",
                "بيان صحفي وتصريح رسمي",
                "تقرير إخباري موسّع مع عناصر جذب",
                "تغطية مؤتمر / فعالية / نشاط ميداني"
            ]
        )
    with col_tone:
        news_tone = st.selectbox(
            "نبرة الخطاب الإعلامي:",
            ["احترافي رصين وجذاب", "حماسي وملهم للجمهور العام", "رسمي ومؤسسي دقيق", "تفاعلي ومختصر للسوشيال ميديا"]
        )

    raw_event = st.text_area("بيانات الفعالية أو تفاصيل الحدث (النقاط الأساسية):", height=120)
    col_quote, col_target = st.columns(2)
    with col_quote:
        official_quote = st.text_input("تصريح رسمي أو اقتباس خاص (اختياري):")
    with col_target:
        target_audience = st.text_input("الجمهور المستهدف (اختياري):")

    if st.button("صياغة المادة الإعلامية"):
        if raw_event.strip():
            with st.spinner("جاري صياغة الخبر باحترافية صحفية..."):
                try:
                    prompt = f"""أنت رئيس تحرير وصحفي محترف.
القالب: {news_type}
النبرة: {news_tone}
الجمهور: {target_audience if target_audience else 'الجمهور العام'}
الوقائع: {raw_event}
تصريح مرفق: {official_quote if official_quote else 'لا يوجد'}

المطلوب:
1. 3 مقترحات لعناوين جذابة.
2. متن الخبر وفق الهرم المقلوب وبصياغة صحفية رصينة.
3. صياغة مخصصة لمنصات التواصل الاجتماعي مع الوسوم (Hashtags)."""
                    
                    res = client.models.generate_content(model=MODEL_NAME, contents=prompt)
                    st.markdown("### 📰 المادة الصحفية الجاهزة:")
                    st.markdown(res.text)
                    
                    st.session_state.history.append({"type": "خبر صحفي", "time": pd.Timestamp.now().strftime("%H:%M:%S"), "preview": res.text})
                    docx_file = create_docx_download(res.text, "المادة الصحفية")
                    st.download_button("📥 تحميل المادة الصحفية (Word)", docx_file, file_name="Press_Release.docx")
                except Exception as err:
                    st.error(f"حدث خطأ: {err}")
        else:
            st.warning("يرجى إدخال تفاصيل الحدث.")

# --- التبويب 3: فحص ومقارنة الوثائق ---
with tab3:
    st.header("فحص الوثائق والصور أو مقارنة مسودتين")
    doc_mode = st.radio("نوع العملية:", ["تحليل وتدقيق وثيقة واحدة (أو صورة)", "مقارنة وثيقتين لكشف الفروق والتعارضات"], horizontal=True)
    
    if doc_mode == "تحليل وتدقيق وثيقة واحدة (أو صورة)":
        uploaded_file = st.file_uploader("ارفع الوثيقة (PDF, Word, PNG, JPG):", type=["pdf", "docx", "png", "jpg", "jpeg"], key="doc1")
        query = st.text_input("المطلوب استخراجه أو تدقيقه:", placeholder="مثال: التدقيق اللغوي، كشف الثغرات، التلخيص...")
        
        if st.button("بدء التحليل", key="btn1"):
            if uploaded_file and query:
                with st.spinner("جاري التحليل..."):
                    try:
                        if uploaded_file.type.startswith("image/"):
                            img = Image.open(uploaded_file)
                            contents = [img, f"النبرة: {persona}\nالمهمة: {query}\nحلل محتوى هذه الصورة بدقة."]
                        else:
                            text_data = extract_text_from_file(uploaded_file)
                            contents = [f"النبرة: {persona}\nمحتوى الوثيقة:\n{text_data[:10000]}\n\nالمهمة: {query}"]
                        
                        res = client.models.generate_content(model=MODEL_NAME, contents=contents)
                        st.markdown("### 📋 التقرير الصادر:")
                        st.markdown(res.text)
                        
                        st.session_state.history.append({"type": "تحليل وثيقة", "time": pd.Timestamp.now().strftime("%H:%M:%S"), "preview": res.text})
                        docx_file = create_docx_download(res.text, "تقرير فحص وثيقة")
                        st.download_button("📥 تحميل التقرير (Word)", docx_file, file_name="Document_Analysis.docx")
                    except Exception as err:
                        st.error(f"حدث خطأ: {err}")
            else:
                st.warning("يرجى إرفاق الملف وتحديد المطلوب.")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            file_a = st.file_uploader("الوثيقة الأولى:", type=["pdf", "docx"], key="fa")
        with col_b:
            file_b = st.file_uploader("الوثيقة الثانية:", type=["pdf", "docx"], key="fb")
        
        if st.button("إجراء المقارنة"):
            if file_a and file_b:
                with st.spinner("جاري مقارنة الوثائق..."):
                    try:
                        text_a = extract_text_from_file(file_a)
                        text_b = extract_text_from_file(file_b)
                        prompt = f"""النبرة: {persona}
قارن بدقة بين النصين:
[الوثيقة 1]: {text_a[:6000]}
[الوثيقة 2]: {text_b[:6000]}
المطلوب: جدول مقارنة بالفروق، التناقضات، والتوصيات النهائية."""
                        res = client.models.generate_content(model=MODEL_NAME, contents=prompt)
                        st.markdown("### 🔍 تقرير المقارنة:")
                        st.markdown(res.text)
                        docx_file = create_docx_download(res.text, "تقرير مقارنة وثيقتين")
                        st.download_button("📥 تحميل تقرير المقارنة (Word)", docx_file, file_name="Comparison_Report.docx")
                    except Exception as err:
                        st.error(f"حدث خطأ: {err}")

# --- التبويب 4: التخطيط الاستراتيجي ---
with tab4:
    st.header("بناء الخطط التنفيذية ومصفوفة KPIs")
    goals = st.text_area("أدخل الأهداف والبيانات الأولية:", height=120)
    col1, col2 = st.columns(2)
    with col1:
        timeframe = st.selectbox("المدى الزمني:", ["شهري", "فصلي (3 أشهر)", "نصف سنوي", "خطة سنوية (4 أرباع)"])
    with col2:
        budget = st.text_input("الميزانية التقديرية (اختياري):")
    
    if st.button("توليد الخطة"):
        if goals:
            with st.spinner("جاري إعداد الخطة..."):
                try:
                    prompt = f"""النبرة: {persona}
الأهداف: {goals}\nالمدى: {timeframe}\nالميزانية: {budget}
المطلوب: خطة مراحل مجدولة، مصفوفة مسؤوليات (RACI)، وجدول مؤشرات أداء (KPIs)."""
                    res = client.models.generate_content(model=MODEL_NAME, contents=prompt)
                    st.markdown("### 🗓️ الخطة التنفيذية:")
                    st.markdown(res.text)
                    docx_file = create_docx_download(res.text, "الخطة التنفيذية")
                    st.download_button("📥 تحميل الخطة (Word)", docx_file, file_name="Strategic_Plan.docx")
                except Exception as err:
                    st.error(f"حدث خطأ: {err}")
        else:
            st.warning("يرجى إدخال الأهداف.")

# --- التبويب 5: المتابعة والتقييم ---
with tab5:
    st.header("مقارنة المخطط بالمنجز وحساب الفجوات")
    planned = st.text_area("المخطط له مسبقاً:", height=90)
    actual = st.text_area("المنجز الفعلي:", height=90)
    
    if st.button("إجراء التدقيق"):
        if planned and actual:
            with st.spinner("جاري التحليل والتدقيق..."):
                try:
                    prompt = f"""النبرة: {persona}
المخطط: {planned}\nالمنجز: {actual}
المطلوب: جدول مقارنة، نسب الإنجاز، وإجراءات تصحيحية للمتعثرات."""
                    res = client.models.generate_content(model=MODEL_NAME, contents=prompt)
                    st.markdown("### 📊 تقرير المتابعة:")
                    st.markdown(res.text)
                    docx_file = create_docx_download(res.text, "تقرير المتابعة والتقييم")
                    st.download_button("📥 تحميل التقرير (Word)", docx_file, file_name="Evaluation_Report.docx")
                except Exception as err:
                    st.error(f"حدث خطأ: {err}")
        else:
            st.warning("يرجى تعبئة الحقلين معاً.")

# --- التبويب 6: لوحة المؤشرات البيانية ---
with tab6:
    st.header("📊 لوحة قياس الأداء البيانية التفاعلية")
    default_data = {
        "المسار / النشاط": ["البحوث والتحقيق", "الإعلام والنشر", "التدقيق الإداري", "التطوير والتدريب"],
        "المستهدف (%)": [100, 100, 100, 100],
        "المتحقق الفعلي (%)": [90, 85, 95, 70]
    }
    df = st.data_editor(pd.DataFrame(default_data), num_rows="dynamic")
    
    if not df.empty:
        df["الفجوة (%)"] = df["المستهدف (%)"] - df["المتحقق الفعلي (%)"]
        fig = px.bar(
            df, 
            x="المسار / النشاط", 
            y=["المتحقق الفعلي (%)", "الفجوة (%)"],
            title="مقارنة الإنجاز الفعلي مقابل الفجوة المتبقية",
            barmode="stack",
            color_discrete_sequence=["#2ecc71", "#e74c3c"]
        )
        st.plotly_chart(fig, use_container_width=True)
