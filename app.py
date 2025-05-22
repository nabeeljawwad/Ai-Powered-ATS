from dotenv import load_dotenv
import base64
import streamlit as st
import os
import io
from PIL import Image
import pdf2image
import google.generativeai as genai
import json
import matplotlib.pyplot as plt
import re
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO



def extract_json_block(text):
    try:
        json_block = re.search(r'\{.*\}', text, re.DOTALL).group()
        return json.loads(json_block)
    except Exception:
        return None

# Load API key from .env file
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize analytics data dictionary
analytics_data = {
    'resume_score': 0,
    'match_percentage': 0,
    'missing_keywords': 0,
    'matching_keywords': 0,
    'recommended_skills': 0
}

# ✅ Gemini Response Handler
def get_gemini_response(input_prompt, pdf_content, job_desc):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([input_prompt, pdf_content[0], job_desc])
    return response.text

# ✅ Convert PDF to image
def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        images = pdf2image.convert_from_bytes(uploaded_file.read())
        first_page = images[0]
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        return [
            {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode()
            }
        ]
    else:
        raise FileNotFoundError("No file uploaded")

# ✅ Streamlit App UI
st.set_page_config(page_title="ATS Resume Checker for YBI by Nabeel Jawwad")
st.header("📄 *ATS Resume Checker for YBI by Nabeel Jawwad*")

input_text = st.text_area("📌 *Job Description*:")
uploaded_file = st.file_uploader("📤 *Upload your resume (PDF)*...", type=["pdf"])

if uploaded_file:
    st.success("✅ *PDF Uploaded Successfully!*")

# ✅ Prompts
input_prompt1 = """
You are an intelligent resume analysis engine. Given a resume and a job description, analyze the resume and ONLY return a JSON object like below. DO NOT add any explanation or text before or after it. Use only double quotes for all keys and string values.

{
  "resume_score": 0 to 100 (integer),
  "match_percentage": 0 to 100 (integer),
  "missing_keywords": integer,
  "matching_keywords": integer,
  "recommended_skills": integer
}
"""

input_prompt3 = "Evaluate the resume vs job description. Return % match, keywords missing, and final thoughts, Keep it breif and to the point"
input_prompt4 = "List important keywords from job description missing in the resume, Keep it breif and to the point."
input_prompt5 = "Suggest how the candidate can improve their skills to match the job description, Keep it breif and to the point."
input_prompt6 = "List job description skills not found in the resume, Keep it breif and to the point."
input_prompt7 = "Score the resume from 0-100 based on relevance, keywords, format, and professionalism, Keep it breif and to the point."
input_prompt8 = "Suggest 3 job roles matching the resume. Explain why each fits, Keep it breif and to the point."

# ✅ Buttons
submit1 = st.button("📊 Resume Evaluation")
submit3 = st.button("✅ Percentage Match")
submit4 = st.button("🔍 Missing Keywords")
submit5 = st.button("📌 How to Improve My Skills?")
submit6 = st.button("🛠 What Skills Are Missing?")
submit7 = st.button("⭐ Resume Score")
submit8 = st.button("💼 Job Role Suggestions")
show_dashboard = st.checkbox("📈 Show Analytics Dashboard", value=False)

# ✅ Handle clicks
def handle_prompt(prompt, title):
    if uploaded_file and input_text.strip():
        try:
            pdf_content = input_pdf_setup(uploaded_file)
            response = get_gemini_response(prompt, pdf_content, input_text)
            st.subheader(title)
            st.write(response)
        except Exception as e:
            st.error(f"⚠ Error: {e}")
    else:
        st.warning("⚠ Please upload a resume and provide job description.")

# ✅ Resume Evaluation (and analytics capture)
if submit1:
    if uploaded_file and input_text.strip():
        try:
            pdf_content = input_pdf_setup(uploaded_file)
            response = get_gemini_response(input_prompt1, pdf_content, input_text)
            parsed = extract_json_block(response)

            st.subheader("📊 Resume Evaluation Summary")

            if parsed:
                analytics_data.update(parsed)

                # Show metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Resume Score", f"{parsed['resume_score']} / 100")
                col2.metric("Match %", f"{parsed['match_percentage']}%")
                col3.metric("Missing Keywords", parsed['missing_keywords'])

                col4, col5 = st.columns(2)
                col4.metric("Matching Keywords", parsed['matching_keywords'])
                col5.metric("Recommended Skills", parsed['recommended_skills'])

                # Show gauge + paragraph insights
                percentage_match = parsed['match_percentage']
                colg1, colg2 = st.columns([1, 2])

                with colg1:
                    gauge = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=percentage_match,
                        title={'text': "Resume Match %"},
                        gauge={
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 75], 'color': "lightyellow"},
                                {'range': [75, 100], 'color': "lightgreen"}
                            ]
                        }
                    ))
                    st.plotly_chart(gauge, use_container_width=True)

                with colg2:
                    feedback_paragraph = f"""
                    ### Resume vs. Job Description Evaluation

                    **Percentage Match:** {percentage_match}%

                    **Keywords Missing from Resume:**  
                    - **Data models**  
                    - **Strategic goals/operational efficiency**  
                    - **Cross-functional collaboration**  
                    - **Actionable insights (business impact)**  
                    - **"Detail-oriented"**

                    **Final Thoughts:**  
                    Your resume demonstrates strong skills in data analysis, Python, SQL, and BI tools.  
                    To improve:
                    - Quantify results
                    - Highlight data modeling
                    - Emphasize business impact
                    - Use missing keywords
                    """
                    st.markdown(feedback_paragraph)

                st.success("✅ Resume Evaluation Successful!")

            else:
                st.warning("⚠ Could not extract valid JSON from Gemini response.")

        except Exception as e:
            st.error(f"⚠ Error: {e}")
    else:
        st.warning("⚠ Please upload resume and job description.")

st.subheader("💬 Resume Chatbot (Q&A)")

question = st.text_input("Ask something about your resume or job match:")
ask_button = st.button("Ask Chatbot")

# This function now uses your existing get_gemini_response properly
def get_chatbot_response(pdf_text, job_desc, question):
    prompt = f"""
    You are a professional AI assistant specializing in resume reviews and job matching. Your role is to provide clear, accurate, and visually appealing answers that are easy to read and understand. Please structure your answers in a friendly and concise manner, highlighting key insights with bullet points or numbered lists when appropriate.

    Resume Content:
    {pdf_text}

    Job Description:
    {job_desc}

    Question:
    {question}

    Based on the above, provide a helpful and concise answer.
    """
    
    return get_gemini_response(prompt, pdf_text, job_desc)  # Calling the function correctly

# Handling the button click to ask the chatbot
if ask_button and question:
    with st.spinner("Analyzing your resume... 🕵️‍♂️"):
        # Ensure both PDF content and job description are loaded
        resume_text = input_pdf_setup(uploaded_file)
        job_desc = input_text.strip()  # Assuming job description comes from input_text field

        # Get the chatbot response
        response = get_chatbot_response(resume_text, job_desc, question)

        # Display the response
        st.markdown(f"**💡 Chatbot Response:** {response}")


elif submit3: handle_prompt(input_prompt3, "✅ Percentage Match")
elif submit4: handle_prompt(input_prompt4, "🔍 Missing Keywords")
elif submit5: handle_prompt(input_prompt5, "📌 Skill Improvement Suggestions")
elif submit6: handle_prompt(input_prompt6, "🛠 Missing Skills Analysis")
elif submit7: handle_prompt(input_prompt7, "⭐ Resume Score")
elif submit8: handle_prompt(input_prompt8, "💼 Job Role Suggestions")

# ✅ Show Dashboard
if show_dashboard and any(analytics_data.values()):
    st.subheader("📊 Resume Analytics Dashboard")

    labels = ['Resume Score', 'Match %', 'Missing Keywords', 'Matching Keywords', 'Recommended Skills']
    values = [
        analytics_data.get('resume_score', 0),
        analytics_data.get('match_percentage', 0),
        analytics_data.get('missing_keywords', 0),
        analytics_data.get('matching_keywords', 0),
        analytics_data.get('recommended_skills', 0)
    ]

    # Create bar chart using matplotlib
    fig, ax = plt.subplots()
    bars = ax.bar(labels, values, color=['orange', 'green', 'red', 'blue', 'purple'])

    # Adding value labels above bars
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, yval + 1, f'{yval}', ha='center')

    ax.set_ylim(0, 110)  # Adjust the y-axis for better visualization
    ax.set_ylabel("Score / Count")
    ax.set_title("Resume Analytics Summary")

    # Display the plot in Streamlit
    st.pyplot(fig)

# Function to generate the PDF
def generate_pdf(resume_score, match_percentage, missing_keywords, matching_keywords, recommended_skills, feedback):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    c.setFont("Helvetica", 12)
    
    # Title
    c.drawString(100, 750, "Resume Evaluation Report")
    
    # Add the evaluation metrics
    c.drawString(100, 730, f"Resume Score: {resume_score} / 100")
    c.drawString(100, 710, f"Match Percentage: {match_percentage}%")
    c.drawString(100, 690, f"Missing Keywords: {missing_keywords}")
    c.drawString(100, 670, f"Matching Keywords: {matching_keywords}")
    c.drawString(100, 650, f"Recommended Skills: {recommended_skills}")

    # Add the feedback
    c.drawString(100, 630, "Feedback:")
    text_object = c.beginText(100, 610)
    text_object.setFont("Helvetica", 10)
    text_object.setTextOrigin(100, 610)
    for line in feedback.split("\n"):
        text_object.textLine(line)
    
    c.drawText(text_object)

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer

# Add a button to generate and download the PDF
if st.button("Download Report"):
    # Here, you will get the values from the Gemini evaluation
    resume_score = 85  # Replace with actual value from the response
    match_percentage = 75  # Replace with actual value
    missing_keywords = 2  # Replace with actual value
    matching_keywords = 15  # Replace with actual value
    recommended_skills = 3  # Replace with actual value
    feedback = """
    Resume vs. Job Description Evaluation:

    Percentage Match: 75%

    Keywords Missing from Resume:
    - Data models
    - Strategic goals/operational efficiency
    - Cross-functional collaboration

    Final Thoughts:
    Your resume demonstrates strong skills in data analysis, Python, SQL, and BI tools.
    To improve:
    - Quantify results
    - Highlight data modeling
    - Emphasize business impact
    - Use missing keywords
    """

    # Generate PDF
    pdf_buffer = generate_pdf(resume_score, match_percentage, missing_keywords, matching_keywords, recommended_skills, feedback)
    
    # Create a downloadable link
    st.download_button(
        label="Download Evaluation Report",
        data=pdf_buffer,
        file_name="resume_evaluation_report.pdf",
        mime="application/pdf"
    )
