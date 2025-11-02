import re
import math
import string

# ====================== NLP utils (Enhanced, No LLM) ======================

STOPWORDS = {
    "the","a","an","of","to","in","for","on","and","or","with","at","by",
    "is","it","this","that","from","as","are","be","we","you","your","our",
    "i","me","my","they","their","them","was","were","will","would","can",
    "could","should","has","have","had","do","does","did","not","no","yes",
    "but","so","if","then","than","into","over","under","about","across",
    "per","via","using"
}

# ---- Structured keyword catalog ----
PROGRAMMING = [
    "python","java","cpp","c","csharp","go","rust","scala","javascript","typescript","r","matlab",
]
WEB_UI = [
    "html","css","sass","less","react","nextjs","vue","angular","svelte","vite","webpack","babel",
    "jest","vitest","mocha","chai","storybook","cypress","playwright","tailwind","bootstrap","material ui",
    "responsive design","accessibility","aria","pwa"
]
BACKEND = [
    "node","express","fastapi","flask","django","spring","spring boot","graphql","rest api","grpc",
    "microservices","event driven","ddd","clean architecture","oauth","jwt","rbac"
]
DATA_SCIENCE = [
    "machine learning","deep learning","nlp","computer vision","data analysis","data visualization",
    "statistics","probability","feature engineering","time series","recommendation systems","ab testing",
    "optimization","linear algebra"
]
ML_LIBS = [
    "numpy","pandas","scikit-learn","tensorflow","pytorch","keras","xgboost","lightgbm","prophet",
    "opencv","nltk","spacy","transformers","hugging face","matplotlib","plotly","seaborn"
]
DATA_ENG = [
    "sql","mysql","postgresql","sqlite","oracle","sql server","mariadb","snowflake","redshift","bigquery",
    "hive","presto","spark","hadoop","dbt","airflow","etl","elt","data pipeline","orchestration","kafka",
    "rabbitmq","sqs","sns","kinesis","pubsub","pub/sub","flink","storm","dask","databricks","glue","emr"
]
NOSQL_SEARCH = [
    "mongodb","redis","dynamodb","cassandra","couchbase","elasticsearch","opensearch","solr","neo4j","graph database"
]
CLOUD = [
    "aws","azure","gcp","amazon web services","microsoft azure","google cloud platform"
]
AWS_SERVICES = [
    "ec2","s3","rds","lambda","ecr","ecs","eks","cloudformation","cloudwatch","athena","glue","emr",
    "redshift","api gateway","sagemaker","route 53","cloudfront","iam","sns","sqs","kinesis"
]
AZURE_SERVICES = [
    "aks","cosmos db","functions","app service","azure devops","synapse","databricks","event hubs","service bus"
]
GCP_SERVICES = [
    "gke","cloud run","bigquery","dataflow","dataproc","pub/sub","vertex ai","cloud functions","cloud storage","composer"
]
DEVOPS = [
    "docker","kubernetes","helm","istio","linkerd","terraform","ansible","packer","pulumi","jenkins","github actions",
    "gitlab ci","travis ci","argo","argo cd","tekton","nexus","artifactory","ci/cd","ci cd","cicd","git","github","gitlab"
]
TESTING_QA = [
    "pytest","unittest","junit","testng","selenium","cypress","playwright","robot framework","karate","postman","k6","locust"
]
SECURITY = [
    "owasp","threat modeling","sast","dast","sonarqube","vault","kms","secrets manager","iam","security+"
]
MONITORING = [
    "prometheus","grafana","datadog","new relic","sentry","elk","logstash","kibana","cloudwatch","stackdriver","opentelemetry"
]
BI_TOOLS = [
    "excel","power query","power bi","tableau","looker","qlik","google analytics"
]
METHODOLOGIES = [
    "agile","scrum","kanban","waterfall","tdd","bdd","pair programming","xp","design patterns","solid","sdlc"
]
SOFT_SKILLS = [
    "communication","teamwork","leadership","problem solving","stakeholder management","mentoring","presentation","collaboration","documentation"
]
CERTIFICATIONS = [
    "aws certified solutions architect","aws certified developer","azure fundamentals","gcp professional data engineer",
    "pmp","scrum master","csm","psm","pspo","cspo","six sigma","itil","cka","ckad","terraform associate","security+"
]

COMMON_SKILLS = (
    PROGRAMMING + WEB_UI + BACKEND + DATA_SCIENCE + ML_LIBS + DATA_ENG + NOSQL_SEARCH + CLOUD +
    AWS_SERVICES + AZURE_SERVICES + GCP_SERVICES + DEVOPS + TESTING_QA + SECURITY + MONITORING +
    BI_TOOLS + METHODOLOGIES + SOFT_SKILLS + CERTIFICATIONS
)

SKILL_SYNONYMS = {
    "c++": "cpp",
    "c plus plus": "cpp",
    "c#": "csharp",
    "c sharp": "csharp",
    "node.js": "node",
    "nodejs": "node",
    "next.js": "nextjs",
    "react.js": "react",
    "vue.js": "vue",
    "angular.js": "angular",
    "ci/cd": "ci/cd",
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "amazon web services": "aws",
    "aws cloud": "aws",
    "microsoft azure": "azure",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "sklearn": "scikit-learn",
    "sci-kit learn": "scikit-learn",
    "tf": "tensorflow",
    "tf2": "tensorflow",
    "torch": "pytorch",
    "hf": "hugging face",
    "postgres": "postgresql",
    "ms sql": "sql server",
    "mssql": "sql server",
    "pubsub": "pub/sub",
    "ms excel": "excel",
    "microsoft excel": "excel",
    "elasticsearch kibana logstash": "elk",
    "aws csa": "aws certified solutions architect",
    "aws developer associate": "aws certified developer",
    "cka kubernetes": "cka",
    "comptia security+": "security+",
}

CONTEXT_BOOSTS = [
    (r"\b(required|must have|qualifications|requirements)\b", 1.4),
    (r"\b(nice to have|preferred)\b", 1.15),
    (r"\b(responsibilities|you will|we are looking)\b", 1.1),
]

def preprocess_text(txt: str):
    txt = txt.lower()
    txt = txt.replace("/", " / ")
    txt = txt.translate(str.maketrans('', '', string.punctuation.replace("/", "")))
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()

def tokenize(txt: str):
    txt = preprocess_text(txt)
    return [t for t in txt.split() if t not in STOPWORDS]

def simple_stem(token: str):
    for suf in ["ing","ed","ly","ies","s"]:
        if token.endswith(suf) and len(token) > len(suf) + 2:
            return token[:-len(suf)]
    return token

def ngrams(tokens, n=2):
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

def split_docs(text: str):
    parts = re.split(r"[\n\r\u2022\-\•]+|\.", text)
    docs = [p.strip() for p in parts if p.strip()]
    return docs or [text.strip()]

def section_weight(sentence: str) -> float:
    s = sentence.lower()
    w = 1.0
    for pat, mul in CONTEXT_BOOSTS:
        if re.search(pat, s):
            w *= mul
    return w

def term_freq(doc_tokens):
    tf = {}
    total = len(doc_tokens)
    if total == 0:
        return tf
    for t in doc_tokens:
        tf[t] = tf.get(t, 0) + 1
    for t in tf:
        tf[t] /= total
    return tf

def inverse_doc_freq(all_docs_tokens):
    N = len(all_docs_tokens)
    df = {}
    for doc in all_docs_tokens:
        for t in set(doc):
            df[t] = df.get(t, 0) + 1
    return {t: (math.log((N + 1) / (d + 1)) + 1) for t, d in df.items()}

def build_token_space(text: str, use_ngrams=True):
    docs = split_docs(text)
    tokens_per_doc = []
    for d in docs:
        toks = tokenize(d)
        grams = toks + ngrams(toks,2) + ngrams(toks,3) if use_ngrams else toks
        tokens_per_doc.append((grams, section_weight(d)))
    return tokens_per_doc

def tfidf_keywords_weighted(text: str, top_k=30):
    docs_tokens_weighted = build_token_space(text, use_ngrams=True)
    idf = inverse_doc_freq([t for t,_ in docs_tokens_weighted])
    scores = {}
    for doc_tokens, w in docs_tokens_weighted:
        tf = term_freq(doc_tokens)
        for term, tf_val in tf.items():
            scores[term] = scores.get(term, 0.0) + (tf_val * idf.get(term, 0.0) * w)
    for term in list(scores.keys()):
        if len(term) <= 2:
            scores[term] *= 0.5
    sorted_terms = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [(t, s) for t, s in sorted_terms if t not in STOPWORDS][:top_k]

def normalize_skill(term: str):
    t = preprocess_text(term)
    return SKILL_SYNONYMS.get(t, t)

def skill_in_text(text_p: str, skill: str):
    skill = normalize_skill(skill)
    if skill in text_p:
        return True
    skill_tokens = [simple_stem(t) for t in skill.split()]
    text_tokens = [simple_stem(t) for t in text_p.split()]
    return all(s in text_tokens for s in skill_tokens)

def extract_skills_from_text(text: str):
    text_p = preprocess_text(text)
    found = set()
    for skill in COMMON_SKILLS:
        if skill_in_text(text_p, skill):
            found.add(normalize_skill(skill))
    for syn, canon in SKILL_SYNONYMS.items():
        if skill_in_text(text_p, syn):
            found.add(canon)
    return sorted(list(found))

def compare_job_and_resume(job_text, resume_text):
    job_skills = set(extract_skills_from_text(job_text))
    resume_skills = set(extract_skills_from_text(resume_text))

    jd_kw_scored = tfidf_keywords_weighted(job_text, top_k=48)
    jd_kw_map = {k: v for k, v in jd_kw_scored}

    heuristic_terms = {
        kw for kw, _ in jd_kw_scored
        if (any(sig in kw for sig in [
                "python","sql","api","ml","data","learning","cloud","docker","kuber",
                "pipeline","model","pandas","spark","aws","azure","gcp","react","java",
                "testing","deployment","analytics","analysis","visualization",
                "communication","leadership","etl","airflow","kafka","git","ci","cd",
                "security","monitoring","prometheus","grafana","selenium","cypress",
                "bigquery","redshift","snowflake","airflow","dbt","kubernetes","terraform",
                "ansible","helm","istio","vertex","sagemaker","lambda","gke","eks","ecs",
                "pub","sub","pub/sub"
            ]) or kw in COMMON_SKILLS)
    }

    job_all = job_skills.union(heuristic_terms)

    missing = job_all - resume_skills
    present = job_all & resume_skills
    extra = resume_skills - job_all

    ranked_missing = sorted(list(missing), key=lambda k: jd_kw_map.get(k, 0.0), reverse=True)

    return {
        "job_skills": sorted(list(job_all)),
        "resume_skills": sorted(list(resume_skills)),
        "missing_skills": sorted(list(missing)),
        "present_skills": sorted(list(present)),
        "extra_skills": sorted(list(extra)),
        "missing_ranked": ranked_missing,
    }

def suggestion_rules(missing_skills):
    suggestions = []
    for skill in missing_skills:
        if skill in ["python","java","sql","excel","power bi","tableau","pandas","numpy","dbt","airflow"]:
            suggestions.append(f"Add **{skill}** under a 'Technical Skills' section or inside a relevant experience bullet.")
        elif skill in ["tensorflow","pytorch","scikit-learn","mlops","docker","kubernetes","helm","terraform","ansible"]:
            suggestions.append(f"Include **{skill}** in a 'Tools' line for your ML/DevOps project, with outcomes (accuracy, latency, cost ↓).")
        elif skill in ["aws","azure","gcp","ec2","s3","lambda","bigquery","redshift","snowflake","gke","eks","ecs"]:
            suggestions.append(f"Show **{skill}** in a project (e.g., 'Deployed on {skill}; cut infra cost 20%').")
        elif skill in ["agile","scrum","kanban","tdd","bdd"]:
            suggestions.append(f"Add **{skill}** in a 'Methods' line under a project or experience, tied to a measurable result.")
        elif skill in ["prometheus","grafana","datadog","new relic","sentry","elk","cloudwatch"]:
            suggestions.append(f"Add **{skill}** under 'Monitoring/Observability' with a clear metric (MTTR ↓, uptime ↑).")
        elif "communication" in skill or "presentation" in skill or "leadership" in skill:
            suggestions.append("Add a soft-skills bullet: “Strong written and verbal communication; led cross-functional demos and stakeholder updates.”")
        else:
            suggestions.append(f"Mention **{skill}** in a project / coursework / experience bullet if you used it.")
    if not suggestions:
        suggestions.append("Your resume already covers the main keywords. You can still mirror the exact wording from the job post.")
    return suggestions
