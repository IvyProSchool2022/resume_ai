import streamlit as st
import openai
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import io
import re
import os
from openai import OpenAI

# Load OpenAI API key from Streamlit secrets
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
)

def generate_refined_resume(chatgpt_prompt, job_profile):
    system_prompt = f"""
    You are a highly skilled resume assistant. Your task is to help users create resumes tailored 
    to specific job descriptions. The job profile provided is: {job_profile}.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
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

def generate_resume_with_reportlab(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name="Title", fontSize=18, textColor=colors.darkblue, alignment=1)
    normal_style = ParagraphStyle(name="Normal", fontSize=11, alignment=0)

    content = []
    content.append(Paragraph(f"<b>{data['name']}</b>", title_style))
    content.append(Paragraph(f"<b>{data['job_title']}</b>", title_style))
    content.append(Spacer(1, 12))
    if data.get("email") or data.get("phone"):
        content.append(Paragraph(f"Email: {data.get('email', '')}, Phone: {data.get('phone', '')}", normal_style))
        content.append(Spacer(1, 12))
    if data.get("summary"):
        content.append(Paragraph(data["summary"], normal_style))
        content.append(Spacer(1, 20))

    # Add Skills
    if data.get("skills"):
        content.append(Paragraph("<b>Skills</b>", title_style))
        for skill, level in data["skills"].items():
            content.append(Paragraph(f"{skill}: {'★' * level}", normal_style))
        content.append(Spacer(1, 20))

    # Add Education
    if data.get("education"):
        content.append(Paragraph("<b>Education</b>", title_style))
        for edu in data["education"]:
            content.append(Paragraph(f"{edu['degree']} - {edu['institution']} ({edu['year']})", normal_style))
        content.append(Spacer(1, 20))

    # Add Projects or Work Experience
    if data.get("projects"):
        content.append(Paragraph("<b>Projects</b>", title_style))
        for project in data["projects"]:
            content.append(Paragraph(f"{project['name']}: {project['description']}", normal_style))
            content.append(Spacer(1, 12))
    elif data.get("work_experience"):
        content.append(Paragraph("<b>Work Experience</b>", title_style))
        for work in data["work_experience"]:
            content.append(Paragraph(f"{work['job_title']} at {work['company']} ({work['duration']}): {work['description']}", normal_style))
            content.append(Spacer(1, 12))

    doc.build(content)
    buffer.seek(0)
    return buffer.getvalue()

# Initialize Session State
if "skills" not in st.session_state:
    st.session_state["skills"] = []
if "education" not in st.session_state:
    st.session_state["education"] = [{}]
if "projects" not in st.session_state:
    st.session_state["projects"] = [{}]
if "work_experience" not in st.session_state:
    st.session_state["work_experience"] = [{}]

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
for i, skill in enumerate(st.session_state["skills"]):
    cols = st.columns([3, 1, 1])
    with cols[0]:
        st.session_state["skills"][i]["name"] = st.text_input(f"Skill {i+1} Name", value=skill.get("name", ""), key=f"skill_name_{i}")
    with cols[1]:
        st.session_state["skills"][i]["level"] = st.slider(f"Skill {i+1} Level", 1, 10, value=skill.get("level", 5), key=f"skill_level_{i}")
    with cols[2]:
        if st.button(f"Remove Skill {i+1}", key=f"remove_skill_{i}"):
            st.session_state["skills"].pop(i)
            break
if st.button("➕ Add Skill"):
    st.session_state["skills"].append({"name": "", "level": 5})

# Education Section
st.header("🎓 Education")
for i, edu in enumerate(st.session_state["education"]):
    with st.expander(f"Education {i+1}"):
        st.session_state["education"][i]["degree"] = st.text_input(f"Degree {i+1}", value=edu.get("degree", ""), key=f"edu_degree_{i}")
        st.session_state["education"][i]["institution"] = st.text_input(f"Institution {i+1}", value=edu.get("institution", ""), key=f"edu_institution_{i}")
        st.session_state["education"][i]["year"] = st.text_input(f"Year {i+1}", value=edu.get("year", ""), key=f"edu_year_{i}")
if st.button("➕ Add Education"):
    st.session_state["education"].append({})

# Selection: Projects or Work Experience
section_choice = st.radio("What would you like to include?", ["Projects", "Work Experience"])

if section_choice == "Projects":
    st.header("📂 Projects")
    for i, project in enumerate(st.session_state["projects"]):
        with st.expander(f"Project {i + 1}"):
            st.session_state["projects"][i]["name"] = st.text_input(f"Project {i+1} Name", key=f"proj_name_{i}")
            st.session_state["projects"][i]["description"] = st.text_area(f"Project {i+1} Description", key=f"proj_desc_{i}")
        if st.button(f"Remove Project {i+1}", key=f"remove_proj_{i}"):
            st.session_state["projects"].pop(i)
            break
    if st.button("➕ Add Project"):
        st.session_state["projects"].append({})

elif section_choice == "Work Experience":
    st.header("💼 Work Experience")
    for i, work in enumerate(st.session_state["work_experience"]):
        with st.expander(f"Work Experience {i + 1}"):
            st.session_state["work_experience"][i]["job_title"] = st.text_input(f"Job Title {i+1}", key=f"work_job_title_{i}")
            st.session_state["work_experience"][i]["company"] = st.text_input(f"Company {i+1}", key=f"work_company_{i}")
            st.session_state["work_experience"][i]["duration"] = st.text_input(f"Duration {i+1}", key=f"work_duration_{i}")
            st.session_state["work_experience"][i]["description"] = st.text_area(f"Description {i+1}", key=f"work_desc_{i}")
        if st.button(f"Remove Work Experience {i+1}", key=f"remove_work_{i}"):
            st.session_state["work_experience"].pop(i)
            break
    if st.button("➕ Add Work Experience"):
        st.session_state["work_experience"].append({})

# Generate Resume
if st.button("Generate Resume"):
    resume_data = {
        "name": name,
        "job_title": job_title,
        "email": email,
        "phone": phone,
        "summary": generate_refined_resume(summary, job_title),
        "skills": {skill["name"]: skill["level"] for skill in st.session_state["skills"] if skill["name"]},
        "education": st.session_state["education"],
        "projects": st.session_state["projects"] if section_choice == "Projects" else None,
        "work_experience": st.session_state["work_experience"] if section_choice == "Work Experience" else None,
    }
    pdf_content = generate_resume_with_reportlab(resume_data)
    st.download_button("Download Resume", data=pdf_content, file_name="resume.pdf", mime="application/pdf")
