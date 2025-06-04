import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import io
from openai import OpenAI

# 初始化 OpenAI
client = OpenAI(
    api_key="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"
)

st.set_page_config(page_title="AI PDF Redundancy Reviewer", layout="centered")
st.title("🧹 PDF Redundancy Reviewer for Admin Training")

st.markdown("Upload one or more **Old Training PDFs**, and AI will identify redundant content and suggest improvements for clarity and conciseness.")

pdf_files = st.file_uploader("📘 Upload Old Training PDFs (multiple allowed)", type=["pdf"], accept_multiple_files=True)

if pdf_files:
    st.success("✅ Files uploaded successfully.")
    
    # 提取 PDF 文本
    pdf_text = ""
    for pdf in pdf_files:
        doc = fitz.open(stream=pdf.read(), filetype="pdf")
        for page in doc:
            pdf_text += page.get_text()

    prompt = f"""
You are an expert Instructional Designer specializing in streamlining training content.

You are given a PDF export of a Rise Admin Training Course.

Your job is to help the course designer improve the training by identifying:

1. Any **redundant or repeated information**, especially when:
   - The same content appears across **multiple Lessons or Modules**
   - Different wording is used to explain the same process
   - The same user flow or feature explanation is shown in multiple places

2. Any **overly technical language** or content that:
   - Feels like it's from product documentation or help center
   - Is not written in an instructional tone for Admin learners
   - Can be simplified to be more learner-friendly

---

For each issue you find, return a row in the following **Markdown table** format:

| Location | Issue Type | Suggested Change (Revised Version if applicable) | RISE Update Action | Comment |
|----------|------------|--------------------------------------------------|---------------------|---------|

Where:
- **Location** is in the format: `Module > Lesson > Specific Area`  
  e.g., `Setting Up > Lesson 2 > Second Paragraph` or `Managing Users > Lesson 1 > Demo Hotspot`
- **Issue Type** is one of: `Redundant`, `Repeated Across Modules`, `Too Technical`, `Overly Verbose`
- **Suggested Change** must include a **full revised version** of any paragraph or suggest deletion/consolidation where appropriate
- **RISE Update Action** is one of: `Update/Modify Text`, `Consolidate Lessons`, `Remove Redundant Text`, `Simplify Wording`, `Merge Duplicate Content`, `New Header Section`
- **Comment** is optional, use it to explain why this change is helpful

Only return rows where meaningful improvement can be made — do **not** include "No change needed" rows.

The training content (excerpt) is below:
{pdf_text[:8000]}
"""




    with st.spinner("🤖 AI is analyzing content..."):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
    result_md = response.choices[0].message.content

    st.markdown("### 📝 AI Suggestions for Redundancy Cleanup")
    st.markdown(result_md)

    # Markdown 转 DataFrame
    try:
        rows = [r.strip() for r in result_md.strip().split("\n") if r.startswith("|")]
        header = [h.strip() for h in rows[0].split("|")[1:-1]]
        data = [[cell.strip() for cell in row.split("|")[1:-1]] for row in rows[2:]]
        result_df = pd.DataFrame(data, columns=header)
    except Exception as e:
        st.error(f"⚠️ Failed to parse AI response. Please verify table format.\n\n{str(e)}")
        st.stop()

    st.markdown("### 📥 Download Feedback")
    output = io.BytesIO()
    result_df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    st.download_button(
        label="⬇️ Download Feedback as Excel",
        data=output,
        file_name="Redundancy_Feedback.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
