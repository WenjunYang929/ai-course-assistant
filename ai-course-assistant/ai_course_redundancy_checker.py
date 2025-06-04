import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import io as iox
from openai import OpenAI

client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
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

🧩 Course Structure:
- The entire PDF represents **one Module**, and the Module name is the **file name without extension**. For example, if the file is named `DataGuide for Admins - DataGuide Basics.pdf`, then the Module name is `DataGuide Basics`.
- Within the Module, there are multiple **Lessons**, each beginning with a line like: `Lesson 2 of 5` followed by a title.
- Your task is to analyze the **lesson-level structure** and identify content issues.

Your job is to help improve the training by identifying:

1. Any **redundant or repeated information**, especially when:
   - The same content appears across multiple lessons
   - Different wording is used to explain the same process
   - Entire concepts are revisited unnecessarily

2. Any **overly technical, verbose, or documentation-style language** that:
   - Can be rewritten more clearly for Admin learners
   - Is better explained with an instructional tone
   - Is too long or detailed for this context

---

🧾 Output Format:

Return your suggestions in the following **Markdown table** format:

| Location | Issue Type | Suggested Change (Revised Version if applicable) | RISE Update Action | Comment |
|----------|------------|--------------------------------------------------|---------------------|---------|

Where:
- **Location** = `Module: [Module Name] > Lesson: [Lesson Title] > Specific Area`  
  Example: `Module: DataGuide Basics > Lesson: Key Capabilities > Second Paragraph`
- **Issue Type** = `Redundant`, `Repeated Across Lessons`, `Too Technical`, `Overly Verbose`
- **Suggested Change** = revised paragraph, merged version, or delete/consolidate suggestion
- **RISE Update Action** = `Update/Modify Text`, `Consolidate Lessons`, `Remove Redundant Text`, `Simplify Wording`, `Merge Duplicate Content`, `New Header Section`
- **Comment** = Optional reasoning why this change improves clarity

Only return rows where meaningful improvement can be made. Do not return "no change needed".

Training Content (excerpt):
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
    output = iox.BytesIO()
    result_df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    st.download_button(
        label="⬇️ Download Feedback as Excel",
        data=output,
        file_name="Redundancy_Feedback.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
