import re
import io
from sklearn.feature_extraction import text as sktext
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem import PorterStemmer

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

STOP_WORDS = set(sktext.ENGLISH_STOP_WORDS)
STEMMER = PorterStemmer()


def preprocess_text(raw_text: str) -> str:
    cleaned = raw_text.lower()
    cleaned = re.sub(r'[^a-z0-9\s]', ' ', cleaned)
    tokens = [token for token in cleaned.split() if token and token not in STOP_WORDS]
    stems = [STEMMER.stem(token) for token in tokens]
    return ' '.join(stems)


def compute_relevance(job_description: str, resume_text: str, corpus_texts=None) -> tuple:
    """
    Compute relevance score and top contributing keywords between job description and resume.
    Returns tuple of (score, top_keywords_list).
    """
    documents = [preprocess_text(job_description)]
    if corpus_texts:
        documents.extend(preprocess_text(text) for text in corpus_texts)
    documents.append(preprocess_text(resume_text))

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(documents)
    similarity = cosine_similarity(vectors[0], vectors[-1])[0][0]
    
    # Extract top contributing keywords from job description
    feature_names = vectorizer.get_feature_names_out()
    job_vector = vectors[0].toarray().flatten()
    
    # Get indices of top 5 terms with highest TF-IDF scores in job description
    top_indices = job_vector.argsort()[-5:][::-1]
    top_keywords = [feature_names[i] for i in top_indices if job_vector[i] > 0]
    
    return float(similarity), top_keywords[:3]  # Return score and top 3 keywords


def extract_text_from_file(uploaded_file) -> str:
    filename = uploaded_file.name.lower()
    uploaded_file.seek(0)
    if filename.endswith('.pdf') and PdfReader is not None:
        try:
            reader = PdfReader(uploaded_file)
            pages = [page.extract_text() or '' for page in reader.pages]
            return '\n'.join(pages)
        except Exception:
            uploaded_file.seek(0)

    raw_bytes = uploaded_file.read()
    try:
        return raw_bytes.decode('utf-8', errors='ignore')
    except Exception:
        return ''
