# Resume Keyword Optimizer

## Overview

The **Resume Keyword Optimizer** is an intelligent tool designed to help job seekers optimize their resumes by comparing them to job descriptions. This application uses a robust keyword matching system (no large language models) that analyzes the job description and resume to identify missing, present, and extra skills. It offers personalized feedback on how to improve resumes and increase job match scores. The tool integrates a chat interface for a seamless user experience.

---

## Features

### 1. **Job Description & Resume Comparison**

* Compares job descriptions with resumes based on keywords and skills.
* Provides a comprehensive breakdown of **missing**, **present**, and **extra** skills in the resume.

### 2. **Skill Matching**

* Uses an extensive, pre-defined catalog of **skills** and **tools** (e.g., programming languages, libraries, cloud services, etc.).
* Identifies **missing skills** and suggests ways to incorporate them into the resume.

### 3. **Personalized Chatbot**

* The chatbot provides friendly, personalized responses by addressing the user by name.
* It guides users with suggestions for adding specific skills to their resumes.
* The bot responds with customized messages such as **"You're missing these skills"** or **"Here are some suggestions"**.

### 4. **Historical Analysis**

* Keeps track of all previous analyses, allowing users to load and view past results.
* Displays the most recent saved analysis with detailed insights.

### 5. **No Large Language Models**

* The tool uses a **context-weighted n-gram TF-IDF model** to perform semantic keyword matching.
* No LLMs are used, making the tool lightweight and easily deployable.

---

## Tech Stack

* **Frontend**: [Streamlit](https://streamlit.io/)
* **Backend**: SQLite (for storing user data, analyses, and chat history)
* **Python Libraries**:

  * `streamlit` – for the interactive user interface.
  * `sqlite3` – for handling database operations.
  * `hashlib` – for password hashing.
  * `math` – for computing IDF values in the TF-IDF algorithm.
  * `re` – for text preprocessing and tokenization.

---

## Project Structure

```
/resume_optimizer/
│
├── app.py               # Main Streamlit application
├── db.py                # Database helper functions (users, analyses, chat history)
├── nlp_engine.py        # NLP keyword extraction, TF-IDF model, and synonym mapping
├── chat_ui.py           # Chat interface renderer (scrollable iframe)
├── chatbot.py           # Chatbot logic and response generation
├── README.md            # Project documentation
│
└── data.db              # SQLite database (generated on app first run)
```

---

## How It Works

1. **User Login/Signup**:

   * Users can sign up or log in to the application using their username and password. This creates or retrieves user data from an SQLite database.

2. **Analyze Job Description & Resume**:

   * The user pastes a job description and their resume text into the provided fields.
   * The app compares the resume with the job description, identifies relevant skills using a catalog, and outputs a list of **missing**, **present**, and **extra** skills.

3. **Chatbot**:

   * The chatbot, based on the user’s job description and resume analysis, provides feedback and suggestions.
   * It engages users in a friendly manner, addressing them by their name and offering personalized suggestions for resume improvements.

4. **Historical Data**:

   * Past analyses are saved, and users can load previous analyses to compare changes or improvements.

---

## Installation & Usage

### Prerequisites

Make sure you have the following installed:

* Python 3.x
* `pip` (Python package installer)

### Installation Steps

1. **Clone the repository**:

   ```bash
   git clone https://github.com/your-repo-url.git
   cd resume_optimizer
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

   If you don’t have `requirements.txt`, you can manually install the required libraries:

   ```bash
   pip install streamlit sqlite3
   ```

3. **Run the app**:

   To start the Streamlit app:

   ```bash
   streamlit run app.py
   ```

   The app should now be accessible on your local machine at `http://localhost:8501`.

### Configuration

* **Database**: The app will automatically create a SQLite database (`data.db`) to store user details, analyses, and chat history.

* **Login/Signup**: Users can create an account or log in directly within the app’s sidebar. No additional configuration is required.

---

## Features to Add

* **File Upload Support**: Support for uploading resumes in PDF or DOCX format and extracting text from them.
* **Cloud Deployment**: Option to deploy the app on cloud platforms like Heroku or Streamlit Sharing.
* **User Profile**: Users can edit their profile information (e.g., name, password).
* **Custom Keyword Catalog**: Allow users to add custom skills to the catalog.

---

## Contributing

We welcome contributions to improve the tool. If you have any suggestions or bugs to report, please feel free to:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new pull request.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

