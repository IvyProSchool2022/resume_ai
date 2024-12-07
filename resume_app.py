import streamlit as st
import openai
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import io
import re
import os

# Load OpenAI API key securely
openai.api_key = os.getenv("OPENAI_API_KEY", st.secrets.get("OPENAI_API_KEY"))

# Helper Function: Generate Refined Resume Content
def generate_refined_resume(chatgpt_prompt, job_profile):
    system_prompt = f"""
    You are a highly skilled resume assistant. Your task is to help users create resumes tailored 
    to specific job descriptions. The job profile provided is: {job_profile}.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": chatgpt_prompt},
            ],
            max_tokens=1000,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating resume content: {e}")
        return ""

# Helper Function: Render Markdown Text for PDFs
def render_markdown_text(text):
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)  # Bold formatting
    text = text.replace("\n", "<br/>")  # Line breaks
    return text

# Helper Function: Add a Section to PDF
def add_section(title, content_list, content, style, spacer_height=10, title_color=colors.darkblue):
    if content_list:
        content.append(Paragraph(f"<font color='{title_color}'>{title}</font>", style))
        for item in content_list:
            content.append(Paragraph(item, style))
            content.append(Spacer(1, spacer_height))

# Helper Function: Generate PDF Resume
def generate_resume_with_reportlab(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name="Title", fontSize=18, textColor=colors.darkblue, alignment=1)
    heading_style = ParagraphStyle(name="Heading", fontSize=14, textColor=colors.darkblue, alignment=0)
    normal_style = ParagraphStyle(name="Normal", fontSize=11, alignment=0)

    content = []

    # Name and Job Title
    content.append(Paragraph(f"<b>{data['name']}</b>", title_style))
    content.append(Paragraph(f"<b>{data['job_title']}</b>", title_style))
    content.append(Spacer(1, 12))

    # Contact Information
    if data.get("email") or data.get("phone"):
        contact_info_data = [[f"E-mail: {data.get('email', '')}", f"Phone: {data.get('phone', '')}"]]
        contact_table = Table(contact_info_data, colWidths=[250, 250])
        contact_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "LEFT"), ("TEXTCOLOR", (0, 0), (-1, -1), colors.blue)]))
        content.append(contact_table)
        content.append(Spacer(1, 12))

    # Professional Summary
    if data.get("summary"):
        content.append(Paragraph(render_markdown_text(data["summary"]), normal_style))
        content.append(Spacer(1, 20))

    # Skills
    if data.get("skills"):
        content.append(Paragraph("<b>Skills</b>", heading_style))
        skills_data = [[Paragraph(f"<b>{skill}</b>", normal_style), f"{'★' * level}"] for skill, level in data["skills"].items()]
        skills_table = Table(skills_data, colWidths=[200, 150])
        content.append(skills_table)
        content.append(Spacer(1, 20))

    # Education
    if data.get("education"):
        education = [f"{edu['degree']} - {edu['institution']} ({edu['year']})" for edu in data["education"]]
        add_section("Education", education, content, normal_style)

    # Work Experience
    if data.get("work_experience"):
        work_exp = [
            f"<b>{exp['job_title']}</b> at <font color='darkblue'>{exp['company']}</font> ({exp['duration']})<br/>{render_markdown_text(exp['description'])}"
            for exp in data["work_experience"]
        ]
        add_section("Work Experience", work_exp, content, normal_style)

    # Projects
    if data.get("projects"):
        for project in data["projects"]:
            content.append(Paragraph(f"<b>{project['name']}</b>", heading_style))
            content.append(Paragraph(render_markdown_text(project["description"]), normal_style))
            content.append(Spacer(1, 10))

    # Generate PDF
    doc.build(content)
    buffer.seek(0)
    return buffer.getvalue()

# Initialize Session State
if "skills" not in st.session_state:
    st.session_state["skills"] = []
if "educations" not in st.session_state:
    st.session_state["educations"] = [{}]
if "work_experiences" not in st.session_state:
    st.session_state["work_experiences"] = [{}]
if "projects" not in st.session_state:
    st.session_state["projects"] = [{}]

# Build Streamlit UI
st.title("📄 ResumeAI - Build Your Resume")

# Personal Information
st.header("👤 Personal Information")
name = st.text_input("Full Name")
job_title = st.text_input("Target Job Title")
email = st.text_input("Email")
phone = st.text_input("Phone")
summary = st.text_area("Professional Summary")

# Skills Section
st.header("💡 Skills")
for i, skill in enumerate(st.session_state.skills):
    cols = st.columns([3, 1, 1])
    with cols[0]:
        skill_name = st.text_input(f"Skill {i+1}", value=skill.get("name", ""), key=f"skill_name_{i}")
    with cols[1]:
        skill_level = st.slider(f"Skill Level {i+1}", min_value=1, max_value=10, value=skill.get("level", 5), key=f"skill_level_{i}")
    with cols[2]:
        if st.button("Remove", key=f"remove_skill_{i}"):
            st.session_state.skills.pop(i)
            break
if st.button("➕ Add Skill"):
    st.session_state.skills.append({"name": "", "level": 5})

# Education Section
st.header("🎓 Education")
for i, education in enumerate(st.session_state.educations):
    with st.expander(f"Education {i+1}"):
        st.text_input("Degree", key=f"edu_degree_{i}")
        st.text_input("Institution", key=f"edu_institution_{i}")
        st.text_input("Year", key=f"edu_year_{i}")
if st.button("➕ Add Education"):
    st.session_state.educations.append({})

# Work Experience Section
st.header("💼 Work Experience")
for i, experience in enumerate(st.session_state.work_experiences):
    with st.expander(f"Work Experience {i+1}"):
        st.text_input("Job Title", key=f"work_job_title_{i}")
        st.text_input("Company", key=f"work_company_{i}")
        st.text_input("Duration", key=f"work_duration_{i}")
        st.text_area("Description", key=f"work_description_{i}")
if st.button("➕ Add Work Experience"):
    st.session_state.work_experiences.append({})

# Projects Section
st.header("📂 Projects")
for i, project in enumerate(st.session_state.projects):
    with st.expander(f"Project {i+1}"):
        st.text_input("Project Name", key=f"proj_name_{i}")
        st.text_area("Description", key=f"proj_desc_{i}")
        st.text_input("Technologies Used", key=f"proj_tech_{i}")
        st.text_input("Project Link", key=f"proj_link_{i}")
if st.button("➕ Add Project"):
    st.session_state.projects.append({})

# Generate Resume Button
if st.button("Generate Resume"):
    resume_data = {
        "name": name,
        "job_title": job_title,
        "email": email,
        "phone": phone,
        "summary": generate_refined_resume(summary, job_title),
        "skills": {skill.get("name", ""): skill.get("level", 5) for skill in st.session_state.skills if skill.get("name")},
        "education": st.session_state.educations,
        "work_experience": st.session_state.work_experiences,
        "projects": st.session_state.projects,
    }
    pdf_content = generate_resume_with_reportlab(resume_data)
    st.download_button("Download Resume", data=pdf_content, file_name="resume.pdf", mime="application/pdf")
