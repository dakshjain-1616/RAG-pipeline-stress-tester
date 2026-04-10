#!/usr/bin/env python3
"""
Simple TF-IDF RAG Server for stress testing.

Corpus: Python programming language documentation snippets.
Accepts: POST /query {"query": "..."}
Returns: {"response": "...", "sources": [...], "retrieved_chunks": [...]}
"""

import math
import re
import time
from collections import defaultdict
from typing import List, Dict, Tuple

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# ── Corpus ────────────────────────────────────────────────────────────────────
CORPUS = [
    {
        "id": "py_basics_1",
        "text": "Python is a high-level, interpreted programming language known for its clear syntax "
                "and readability. Created by Guido van Rossum and first released in 1991, Python's "
                "design philosophy emphasizes code readability with the use of significant indentation. "
                "Python is dynamically typed and garbage-collected, and supports multiple programming "
                "paradigms including structured, object-oriented, and functional programming.",
    },
    {
        "id": "py_basics_2",
        "text": "Python variables do not need explicit type declarations. You can assign any value "
                "to a variable directly: x = 10, name = 'Alice', is_valid = True. Python uses duck "
                "typing — if it walks like a duck and quacks like a duck, it is a duck. The built-in "
                "types include int, float, str, bool, list, tuple, dict, and set.",
    },
    {
        "id": "py_functions",
        "text": "Functions in Python are defined with the 'def' keyword. A function can accept "
                "positional arguments, keyword arguments, *args (variable positional), and **kwargs "
                "(variable keyword). Python supports first-class functions — functions are objects "
                "that can be passed to other functions, returned from functions, and stored in "
                "variables. Lambda functions are anonymous one-line functions: lambda x: x * 2.",
    },
    {
        "id": "py_lists",
        "text": "Python lists are ordered, mutable sequences that can hold items of any type. "
                "Lists are created with square brackets: my_list = [1, 2, 3]. List comprehensions "
                "provide a concise way to create lists: [x**2 for x in range(10)]. Common list "
                "methods include append(), extend(), insert(), remove(), pop(), sort(), and reverse(). "
                "Lists support slicing: my_list[1:3] returns elements at indices 1 and 2.",
    },
    {
        "id": "py_dicts",
        "text": "Python dictionaries are key-value stores. Created with curly braces: "
                "d = {'key': 'value'}. Access values with d['key'] or d.get('key', default). "
                "Dictionary methods: keys(), values(), items(), update(), pop(). "
                "Dictionary comprehensions: {k: v for k, v in pairs}. As of Python 3.7+ dicts "
                "maintain insertion order.",
    },
    {
        "id": "py_classes",
        "text": "Python classes are defined with the 'class' keyword. The __init__ method is the "
                "constructor. self refers to the instance. Python supports single and multiple "
                "inheritance. Special (dunder) methods like __str__, __repr__, __len__, __eq__ "
                "allow objects to integrate with Python built-ins. Decorators like @property, "
                "@classmethod, and @staticmethod modify method behaviour.",
    },
    {
        "id": "py_exceptions",
        "text": "Python exceptions are handled with try/except/else/finally blocks. Raise exceptions "
                "with: raise ValueError('message'). Custom exceptions inherit from Exception. "
                "Common built-in exceptions: TypeError, ValueError, KeyError, IndexError, "
                "AttributeError, FileNotFoundError, ImportError, RuntimeError. The 'else' clause "
                "in a try block runs only when no exception is raised.",
    },
    {
        "id": "py_modules",
        "text": "Python code is organized into modules (files) and packages (directories with "
                "__init__.py). Import a module with: import math. Import specific names: "
                "from math import sqrt, pi. The standard library includes os, sys, re, json, "
                "datetime, collections, itertools, functools, pathlib, and many more. "
                "Third-party packages are installed with pip.",
    },
    {
        "id": "py_files",
        "text": "Reading and writing files in Python uses the built-in open() function. "
                "Best practice is to use a context manager: with open('file.txt', 'r') as f: "
                "content = f.read(). Modes: 'r' (read), 'w' (write), 'a' (append), 'b' (binary). "
                "The pathlib module provides an object-oriented interface for file system paths.",
    },
    {
        "id": "py_decorators",
        "text": "Decorators are a Python feature that allows you to modify or enhance functions "
                "without changing their code. A decorator is a callable that takes a function and "
                "returns a modified function. The @functools.wraps decorator preserves the original "
                "function's metadata. Common use cases: logging, authentication, caching (functools.lru_cache), "
                "input validation, and timing.",
    },
    {
        "id": "py_generators",
        "text": "Python generators are functions that yield values one at a time using the 'yield' "
                "keyword, enabling lazy evaluation. Generator expressions use parentheses: "
                "(x**2 for x in range(100)). Generators are memory-efficient for large datasets. "
                "The itertools module provides generator-based utilities: chain(), islice(), "
                "product(), combinations(), permutations().",
    },
    {
        "id": "py_async",
        "text": "Python's asyncio library provides infrastructure for writing asynchronous code "
                "using async/await syntax. Define an async function with 'async def'. Await "
                "coroutines with 'await'. asyncio.run() runs the event loop. Use asyncio.gather() "
                "to run coroutines concurrently. aiohttp is a popular async HTTP client library. "
                "Async is ideal for I/O-bound tasks like network calls and file operations.",
    },
    {
        "id": "py_typing",
        "text": "Python's typing module provides support for type hints. Annotate variables and "
                "function signatures: def greet(name: str) -> str. Common types: List[int], "
                "Dict[str, Any], Optional[str], Union[int, str], Tuple[int, ...]. "
                "mypy is the standard type checker. Type hints improve readability and enable "
                "IDE auto-completion but are not enforced at runtime.",
    },
    {
        "id": "py_testing",
        "text": "Python's standard testing framework is unittest. pytest is the most popular "
                "third-party testing framework — it supports fixtures, parametrize, and plugins. "
                "Write a test as a function starting with 'test_'. Use assert statements for "
                "assertions. Coverage.py measures test coverage. Mock objects are created with "
                "unittest.mock.patch or pytest-mock's mocker fixture.",
    },
    {
        "id": "py_comprehensions",
        "text": "Python comprehensions provide a concise syntax for building collections. "
                "List comprehension: [x for x in iterable if condition]. "
                "Set comprehension: {x for x in iterable}. "
                "Dict comprehension: {k: v for k, v in iterable}. "
                "Nested comprehensions: [row[i] for row in matrix for i in range(len(row))]. "
                "Prefer comprehensions over map/filter for clarity.",
    },
]

SCOPE_PHRASES = [
    "I don't have information about that in my knowledge base.",
    "That topic is outside the scope of my Python programming knowledge base.",
    "I cannot find relevant information about this in my documentation.",
    "This question appears to be outside my area of expertise (Python programming).",
]

REFUSAL_TRIGGERS = [
    "ignore", "override", "forget", "disregard", "jailbreak", "bypass",
    "pretend", "you are now", "act as", "roleplay", "sudo", "admin",
    "reveal your prompt", "system prompt", "instructions",
]

# ── TF-IDF Engine ─────────────────────────────────────────────────────────────
STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "in", "on", "at", "to",
    "for", "of", "and", "or", "but", "with", "by", "from", "this", "that",
    "it", "its", "not", "as", "if", "so", "than", "then", "there", "their",
    "they", "we", "you", "i", "my", "your", "our", "what", "how", "when",
    "where", "why", "who", "which",
}


def tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[a-z0-9']+", text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def build_tfidf_index(corpus: List[Dict]) -> Tuple[Dict, Dict]:
    """Build TF-IDF index from corpus."""
    tf_scores = {}  # doc_id -> {term -> tf}
    df = defaultdict(int)  # term -> document frequency
    N = len(corpus)

    for doc in corpus:
        tokens = tokenize(doc["text"])
        total = len(tokens) or 1
        counts = defaultdict(int)
        for t in tokens:
            counts[t] += 1
        tf_scores[doc["id"]] = {t: c / total for t, c in counts.items()}
        for t in counts:
            df[t] += 1

    idf = {t: math.log((N + 1) / (freq + 1)) + 1 for t, freq in df.items()}
    tfidf = {}
    for doc_id, tfs in tf_scores.items():
        tfidf[doc_id] = {t: tf * idf.get(t, 1) for t, tf in tfs.items()}

    return tfidf, idf


def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    common = set(vec_a) & set(vec_b)
    dot = sum(vec_a[t] * vec_b[t] for t in common)
    norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def query_to_vec(query: str, idf: Dict[str, float]) -> Dict[str, float]:
    tokens = tokenize(query)
    total = len(tokens) or 1
    counts: Dict[str, int] = defaultdict(int)
    for t in tokens:
        counts[t] += 1
    return {t: (c / total) * idf.get(t, 1.0) for t, c in counts.items()}


# ── Build index at startup ─────────────────────────────────────────────────────
TFIDF_INDEX, IDF = build_tfidf_index(CORPUS)
ID_TO_DOC = {doc["id"]: doc for doc in CORPUS}


def retrieve(query: str, top_k: int = 3) -> List[Dict]:
    q_vec = query_to_vec(query, IDF)
    scores = []
    for doc_id, doc_vec in TFIDF_INDEX.items():
        score = cosine_similarity(q_vec, doc_vec)
        scores.append((score, doc_id))
    scores.sort(reverse=True)
    return [{"id": doc_id, "score": round(score, 4), "text": ID_TO_DOC[doc_id]["text"]}
            for score, doc_id in scores[:top_k] if score > 0]


def generate_response(query: str, retrieved: List[Dict]) -> str:
    """Synthesize an answer from retrieved chunks."""
    if not retrieved or retrieved[0]["score"] < 0.05:
        return SCOPE_PHRASES[hash(query) % len(SCOPE_PHRASES)]

    # Simple extractive answer: pick the best chunk and prepend a brief intro
    best = retrieved[0]["text"]
    # Trim to a readable length
    sentences = re.split(r"(?<=[.!?])\s+", best)
    answer = " ".join(sentences[:3])
    return answer


def is_adversarial(query: str) -> bool:
    q_lower = query.lower()
    return any(trigger in q_lower for trigger in REFUSAL_TRIGGERS)


# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(title="Python RAG Server", version="1.0.0")


@app.post("/query")
async def query_endpoint(request: Request):
    t0 = time.perf_counter()
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    query = body.get("query", "").strip()
    if not query:
        return JSONResponse(status_code=400, content={"error": "Missing 'query' field"})

    # Adversarial / injection detection
    if is_adversarial(query):
        return JSONResponse(content={
            "response": "I cannot comply with that request. Please ask a question about Python programming.",
            "sources": [],
            "retrieved_chunks": [],
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
            "flagged": True,
        })

    retrieved = retrieve(query, top_k=3)
    response_text = generate_response(query, retrieved)

    return JSONResponse(content={
        "response": response_text,
        "sources": [r["id"] for r in retrieved],
        "retrieved_chunks": [{"id": r["id"], "score": r["score"], "snippet": r["text"][:120] + "..."} for r in retrieved],
        "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        "flagged": False,
    })


@app.get("/health")
async def health():
    return {"status": "ok", "corpus_size": len(CORPUS)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="warning")
