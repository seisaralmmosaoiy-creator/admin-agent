import os
import io
import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from google.genai import types
from PIL import Image
from pypdf import PdfReader
import docx

st.set_page_config(page_title="المساعد الإداري الذكي المتكامل", layout="wide", page_icon="💼")

# إعداد مفتاح API
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ يرجى ضبط مفتاح GEMINI_API_KEY في إعدادات Secrets.")
    st.stop()

client = genai.Client(api_key=api_key.strip())
MODEL_NAME = "gemini-3.6-flash"

# تهيئة سجل المحفوظات
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

def create_docx_download(content_text, title="التقرير الإداري"):
    doc = docx.Document()
    doc.add_heading(title, level=0)
    for paragraph in content_text.split("\n"):
        if paragraph.strip():
            doc.add_paragraph(paragraph)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# القائمة الجانبية
with st.sidebar:
    st.header("⚙️ تخصيص الوكيل الإداري")
    persona = st.selectbox(
        "أسلوب ونبرة الصياغة:",
        [
            "تدقيق رقابي وقانوني صارم",
            "صياغة إدارية واستراتيجية متوازنة",
            "صياغة إعلامية وبيانات صحفية",
            "أسلوب تشغيلي وميداني مباشر"
        ]
    )
    st.markdown("---")
    st.subheader("🗂️ سجل العمليات السابقة")
    if st.session_state.history:
        for idx, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"{item['type']} - {item['time']}"):
                st.write(item["preview"][:150] + "...")
    else:
        st.caption("لا توجد تقارير محفوظة بعد.")

st.title("💼 المنظومة الإدارية والذكاء المؤسسي الشامل")

tab1, tab2, tab3, tab4 = st.tabs([
    "📄 فحص ومقارنة الوثائق",
    "📊 التخطيط الاستراتيجي ومؤشرات الأداء",
    "📈 المتابعة الميدانية وتحليل الفجوات",
    "📊 لوحة مؤشرات الأداء (Dashboard)"
])

# --- التبويب 1: فحص ومقارنة الوثائق ---
with tab1:
    st.header("فحص الوثائق والصور أو مقارنة مسودتين")
    doc_mode = st.radio("نوع العملية:", ["تحليل وتدقيق وثيقة واحدة (أو صورة)", "مقارنة وثيقتين لكشف الفروق والتعارضات"], horizontal=True)
    
    if doc_mode == "تحليل وتدقيق وثيقة واحدة (أو صورة)":
        uploaded_file = st.file_uploader("ارفع الوثيقة (PDF, Word, PNG, JPG):", type=["pdf", "docx", "png", "jpg", "jpeg"], key="doc1")
        query = st.text_input("المطلوب استخراجه أو تدقيقه:", placeholder="مثال: التدقيق اللغوي، كشف الثغرات، استخراج الميزانية...")
        
        if st.button("بدء التحليل", key="btn1"):
            if uploaded_file and query:
                with st.spinner("جاري المعالجة والتحليل..."):
                    try:
                        contents = []
                        if uploaded_file.type.startswith("image/"):
                            img = Image.open(uploaded_file)
                            contents = [img, f"النبرة المطلوبة: {persona}\nالمهمة: {query}\nحلل محتوى هذه الصورة بدقة إدارية."]
                        else:
                            text_data = extract_text_from_file(uploaded_file)
                            contents = [f"النبرة المطلوبة: {persona}\nمحتوى الوثيقة:\n{text_data[:10000]}\n\nالمهمة: {query}"]
                        
                        res = client.models.generate_content(model=MODEL_NAME, contents=contents)
                        st.markdown("### 📋 التقرير الصادر:")
                        st.markdown(res.text)
                        
                        st.session_state.history.append({"type": "تحليل وثيقة", "time": pd.Timestamp.now().strftime("%H:%M:%S"), "preview": res.text})
                        
                        docx_file = create_docx_download(res.text, "تقرير تحليل وثيقة")
                        st.download_button("📥 تحميل التقرير بصيغة Word", docx_file, file_name="Document_Analysis.docx")
                    except Exception as err:
                        st.error(f"حدث خطأ: {err}")
            else:
                st.warning("يرجى إرفاق الملف وتحديد المطلوب.")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            file_a = st.file_uploader("الوثيقة الأساسية / الأصلية:", type=["pdf", "docx"], key="fa")
        with col_b:
            file_b = st.file_uploader("الوثيقة المقابلة / المسودة المعدلة:", type=["pdf", "docx"], key="fb")
        
        if st.button("إجراء المقارنة الشاملة"):
            if file_a and file_b:
                with st.spinner("جاري استخراج وتحليل الفوارق والتعارضات..."):
                    try:
                        text_a = extract_text_from_file(file_a)
                        text_b = extract_text_from_file(file_b)
                        prompt = f"""النبرة: {persona}
أنت خبير تدقيق وثائق. قارن بين الوثيقتين التاليتين:
[الوثيقة 1]:
{text_a[:6000]}

[الوثيقة 2]:
{text_b[:6000]}

المطلوب:
1. جدول مقارنة دقيق بالتغييرات والإضافات والمحذوفات.
2. الثغرات القانونية أو الإدارية الناشئة عن التعديلات.
3. التوصيات النهائية."""
                        res = client.models.generate_content(model=MODEL_NAME, contents=prompt)
                        st.markdown("### 🔍 تقرير المقارنة:")
                        st.markdown(res.text)
                        
                        docx_file = create_docx_download(res.text, "تقرير مقارنة وثيقتين")
                        st.download_button("📥 تحميل تقرير المقارنة (Word)", docx_file, file_name="Comparison_Report.docx")
                    except Exception as err:
                        st.error(f"حدث خطأ: {err}")

# --- التبويب 2: التخطيط الاستراتيجي ---
with tab2:
    st.header("بناء الخطط التنفيذية ومصفوفة KPIs")
    goals = st.text_area("أدخل الأهداف والبيانات الأولية للمشروع:", height=130)
    col1, col2 = st.columns(2)
    with col1:
        timeframe = st.selectbox("المدى الزمني:", ["شهري", "فصلي (3 أشهر)", "نصف سنوي", "خطة سنوية (4 أرباع)"])
    with col2:
        budget = st.text_input("الميزانية التقديرية (اختياري):", placeholder="مثال: 50,000 دولار")
    
    if st.button("توليد الخطة المتكاملة"):
        if goals:
            with st.spinner("جاري صياغة الخطة التنفيذية..."):
                try:
                    prompt = f"""النبرة الإدارية: {persona}
الأهداف: {goals}
النطاق الزمني: {timeframe}
الميزانية: {budget}
المطلوب:
1. خطة عمل مجدولة زمنياً ومقسمة إلى مراحل تفصيلية.
2. مصفوفة تحديد المسؤوليات والموارد (RACI Matrix).
3. جدول مؤشرات قياس أداء ذكية (SMART KPIs) مع المستهدفات الرقمية."""
                    res = client.models.generate_content(model=MODEL_NAME, contents=prompt)
                    st.markdown("### 🗓️ الخطة التنفيذية المعتمدة:")
                    st.markdown(res.text)
                    
                    st.session_state.history.append({"type": "خطة استراتيجية", "time": pd.Timestamp.now().strftime("%H:%M:%S"), "preview": res.text})
                    docx_file = create_docx_download(res.text, "الخطة التنفيذية")
                    st.download_button("📥 تحميل الخطة (Word)", docx_file, file_name="Strategic_Plan.docx")
                except Exception as err:
                    st.error(f"حدث خطأ: {err}")

# --- التبويب 3: المتابعة والتقييم ---
with tab3:
    st.header("مقارنة المخطط بالمنجز وحساب الفجوات")
    planned = st.text_area("المستهدفات والمخطط له مسبقاً:", height=100)
    actual = st.text_area("المنجز الفعلي على أرض الواقع:", height=100)
    
    if st.button("إجراء التدقيق وحساب الانحرافات"):
        if planned and actual:
            with st.spinner("جاري تحليل الإنجاز والانحرافات..."):
                try:
                    prompt = f"""النبرة: {persona}
المخطط: {planned}
المنجز: {actual}
المطلوب:
1. جدول مقارنة تفصيلي بين المخطط والمنجز.
2. تحديد نسبة الإنجاز والقصور لكل محور.
3. إجراءات تصحيحية عاجلة لمعالجة الفجوات."""
                    res = client.models.generate_content(model=MODEL_NAME, contents=prompt)
                    st.markdown("### 📊 تقرير المتابعة والتقييم:")
                    st.markdown(res.text)
                    
                    docx_file = create_docx_download(res.text, "تقرير المتابعة والتقييم")
                    st.download_button("📥 تحميل تقرير التدقيق (Word)", docx_file, file_name="Evaluation_Report.docx")
                except Exception as err:
                    st.error(f"حدث خطأ: {err}")

# --- التبويب 4: لوحة مؤشرات الأداء البصرية ---
with tab4:
    st.header("📊 لوحة قياس الأداء البيانية التفاعلية")
    st.write("أدخل نسب الإنجاز للمشاريع/المسارات لمشاهدة التحليل البصري المباشر:")
    
    default_data = {
        "المسار / المشروع": ["الإعلام والتواصل", "التدقيق المالي", "تطوير الكوادر", "الخدمات الميدانية"],
        "المستهدف (%)": [100, 100, 100, 100],
        "المتحقق الفعلي (%)": [85, 92, 60, 78]
    }
    df = st.data_editor(pd.DataFrame(default_data), num_rows="dynamic")
    
    if not df.empty:
        df["الفجوة (%)"] = df["المستهدف (%)"] - df["المتحقق الفعلي (%)"]
        
        fig = px.bar(
            df, 
            x="المسار / المشروع", 
            y=["المتحقق الفعلي (%)", "الفجوة (%)"],
            title="مقارنة الإنجاز الفعلي مقابل الفجوة المتبقية",
            barmode="stack",
            color_discrete_sequence=["#2ecc71", "#e74c3c"]
        )
        st.plotly_chart(fig, use_container_width=True)
