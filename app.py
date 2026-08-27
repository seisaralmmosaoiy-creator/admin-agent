import os
import streamlit as st
from google import genai
from pypdf import PdfReader
import docx

# ضبط إعدادات الصفحة
st.set_page_config(page_title="المساعد الإداري الذكي", layout="wide")

# استدعاء مفتاح API
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ يرجى ضبط مفتاح GEMINI_API_KEY في إعدادات Secrets.")
    st.stop()

# تهيئة العميل
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"خطأ في تهيئة العميل: {e}")
    st.stop()

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

st.title("💼 المساعد والوكيل الإداري الشامل")
st.write("نظام متعدد الوظائف لتحليل الوثائق، بناء الخطط، وتقييم الأداء.")

tab1, tab2, tab3 = st.tabs(["📄 وكيل تحليل الوثائق", "📊 وكيل التخطيط الإداري", "📈 وكيل المتابعة والتقييم"])

with tab1:
    st.header("استخراج وتحليل ومقارنة الوثائق")
    uploaded_file = st.file_uploader("ارفع وثيقة (PDF أو Word)", type=["pdf", "docx"])
    doc_query = st.text_input("ما التحليل المطلوب حول هذه الوثيقة؟", placeholder="مثال: لخص النقاط الأساسية واكتشف الثغرات...")
    
    if st.button("تحليل الوثيقة"):
        if uploaded_file and doc_query:
            with st.spinner("جاري تحليل الوثيقة..."):
                try:
                    content = extract_text_from_pdf(uploaded_file) if uploaded_file.name.endswith(".pdf") else extract_text_from_docx(uploaded_file)
                    prompt = f"""أنت وكيل متخصص في التدقيق الإداري وتحليل الوثائق الرسمية.
محتوى الوثيقة:
---
{content[:8000]}
---
المهمة: {doc_query}
قدّم تقريراً هيكلياً يتضمن ملخصاً تنفيذياً، الثغرات أو النواقص إن وجدت، والتوصيات التنفيذية."""
                    
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=prompt
                    )
                    st.markdown("### 📋 التقرير التحليلي:")
                    st.markdown(response.text)
                except Exception as err:
                    st.error(f"حدث خطأ أثناء معالجة الطلب: {err}")
        else:
            st.warning("يرجى رفع ملف وكتابة المهمة المطلوبة.")

with tab2:
    st.header("بناء الخطط التنفيذية ومؤشرات الأداء")
    goals = st.text_area("أدخل الأهداف والبيانات الأولية للمشروع/المؤسسة:", height=150)
    timeframe = st.selectbox("النطاق الزمني:", ["شهري", "فصلي (3 أشهر)", "سنوي (4 أرباع)"])
    
    if st.button("توليد الخطة التنفيذية"):
        if goals:
            with st.spinner("جاري بناء الخطة..."):
                try:
                    prompt = f"""أنت وكيل تخطيط إداري استراتيجي وعملياتي.
الأهداف والمدخلات: {goals}
المدى الزمني: {timeframe}
المطلوب:
1. خطة عمل تنفيذية مجدولة زمنياً ومقسمة إلى مراحل.
2. مصفوفة تحديد المسؤوليات والموارد المطلوبة.
3. جدول مؤشرات قياس أداء واضحة وقابلة للقياس (KPIs SMART) مع القيم المستهدفة."""
                    
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=prompt
                    )
                    st.markdown("### 🗓️ الخطة التنفيذية المقترحة:")
                    st.markdown(response.text)
                except Exception as err:
                    st.error(f"حدث خطأ أثناء معالجة الطلب: {err}")
        else:
            st.warning("يرجى إدخال الأهداف المراد تخطيطها.")

with tab3:
    st.header("مقارنة المخطط بالمنجز وحساب الانحرافات")
    planned = st.text_area("المخطط له (الأهداف أو المستهدفات السابقة):", height=100)
    actual = st.text_area("المنجز الفعلي على أرض الواقع:", height=100)
    
    if st.button("إجراء التدقيق والتقييم"):
        if planned and actual:
            with st.spinner("جاري التدقيق واحتساب الفجوات..."):
                try:
                    prompt = f"""أنت وكيل رقابة وتدقيق إداري (Monitoring & Evaluation Agent).
المخطط:
{planned}
المنجز الفعلي:
{actual}
المطلوب:
1. مقارنة تفصيلية بين المخطط والمنجز في جدول.
2. تحديد نسبة الإنجاز التقريبية وتحديد مواطن الخلل أو التأخير.
3. خطة إجراءات تصحيحية فورية وملموسة لمعالجة الفجوات."""
                    
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=prompt
                    )
                    st.markdown("### 📊 تقرير المتابعة والتقييم:")
                    st.markdown(response.text)
                except Exception as err:
                    st.error(f"حدث خطأ أثناء معالجة الطلب: {err}")
        else:
            st.warning("يرجى تزويد الوكيل ببيانات المخطط والمنجز معاً.")
