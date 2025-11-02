import streamlit as st

def main():
    st.set_page_config(page_title="Resume Keyword Optimizer", page_icon="🤖")

    st.title("🤖 Resume Keyword Optimizer (MVP)")
    st.write("Paste a job description and your resume, and I'll tell you what's missing. (Login coming soon 👇)")

    st.subheader("1. Job Description")
    job_desc = st.text_area("Job Description", height=180, placeholder="Paste the job post here...")

    st.subheader("2. Your Resume (text)")
    resume_txt = st.text_area("Resume", height=180, placeholder="Paste your resume text here...")

    if st.button("Analyze (not working yet)"):
        st.info("In the next step, we'll add the real analysis logic.")

if __name__ == "__main__":
    main()
