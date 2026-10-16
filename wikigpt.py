#!/usr/bin/env python3
"""
Welcome To WikiGPT.
WikiGPT is based on Gemini instead of its own model.
Made with ❤️ By DanDevProjects. See more of my projects on Github!
"""

import os
import sys
import json
import ssl
import re
import urllib.request
import urllib.parse
from typing import List, Dict, Optional

# Fix proxy ipv6 parse quirk if present in environment
if "no_proxy" in os.environ:
    os.environ["no_proxy"] = os.environ["no_proxy"].replace("[::1]", "").replace("::1", "").replace(",,", ",")
if "NO_PROXY" in os.environ:
    os.environ["NO_PROXY"] = os.environ["NO_PROXY"].replace("[::1]", "").replace("::1", "").replace(",,", ",")

# ---------------------------------------------------------
# SSL Configuration (fixes SSL CERTIFICATE_VERIFY_FAILED)
# ---------------------------------------------------------
def get_ssl_context() -> ssl.SSLContext:
    """Creates a robust SSL context, falling back gracefully if local certs are missing."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass

    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = True
        return ctx
    except Exception:
        return ssl._create_unverified_context()

SSL_CONTEXT = get_ssl_context()
FALLBACK_UNVERIFIED_SSL = ssl._create_unverified_context()

# ---------------------------------------------------------
# Gemini Client Setup & Robust Generation
# ---------------------------------------------------------
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: The 'google-genai' package is required. Install it with: pip install google-genai", file=sys.stderr)
    sys.exit(1)

# Active, supported models with automatic fallback
CANDIDATE_MODELS = [
    os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    "gemini-3.5-flash",
    "gemini-3-flash-preview"
]

def generate_with_fallback(client: genai.Client, contents, config=None):
    """Attempts generation across candidate models with automatic failover."""
    last_err = None
    for model_name in CANDIDATE_MODELS:
        try:
            return client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            ), model_name
        except Exception as e:
            last_err = e
            continue
    raise last_err

# ---------------------------------------------------------
# Wikipedia Client
# ---------------------------------------------------------
WIKI_USER_AGENT = "WikiGPT/1.0 (https://github.com/wikigpt; contact@example.com)"

def wiki_api_request(params: dict) -> Optional[dict]:
    """Executes a GET request against the Wikipedia MediaWiki API with headers and SSL handling."""
    query_string = urllib.parse.urlencode(params)
    url = f"https://en.wikipedia.org/w/api.php?{query_string}"
    headers = {
        "User-Agent": WIKI_USER_AGENT,
        "Accept": "application/json"
    }
    req = urllib.request.Request(url, headers=headers)

    for ctx in (SSL_CONTEXT, FALLBACK_UNVERIFIED_SSL):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=8) as response:
                if response.status == 200:
                    data = response.read().decode("utf-8", errors="replace")
                    return json.loads(data)
        except Exception:
            continue
    return None

def search_wikipedia_titles(search_term: str, limit: int = 3) -> List[str]:
    """Searches Wikipedia and returns top matching article titles."""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": search_term,
        "srlimit": limit,
        "format": "json",
        "utf8": 1
    }
    data = wiki_api_request(params)
    if not data or "query" not in data or "search" not in data["query"]:
        return []
    
    titles = [item["title"] for item in data["query"]["search"] if "title" in item]
    return titles

def fetch_articles_content(titles: List[str]) -> Dict[str, str]:
    """Fetches clean text extracts for multiple Wikipedia article titles."""
    if not titles:
        return {}

    # Query multiple titles in a single API call separated by pipe
    params = {
        "action": "query",
        "prop": "extracts",
        "exintro": 1,        # Fetch introductory summary (rich, concise, high quality)
        "explaintext": 1,    # Plain text, no HTML tags
        "titles": "|".join(titles),
        "format": "json",
        "utf8": 1
    }
    data = wiki_api_request(params)
    if not data or "query" not in data or "pages" not in data["query"]:
        return {}

    articles = {}
    for page_id, page_info in data["query"]["pages"].items():
        if page_id == "-1" or "missing" in page_info:
            continue
        title = page_info.get("title", "")
        extract = page_info.get("extract", "").strip()
        if title and extract:
            articles[title] = extract
    return articles

# ---------------------------------------------------------
# Conversational Memory & Multi-turn Engine
# ---------------------------------------------------------
class WikiGPTEngine:
    def __init__(self, client: genai.Client):
        self.client = client
        self.history: List[Dict[str, str]] = []  # List of {"role": "user"|"model", "text": "..."}

    def format_history_for_prompt(self, max_turns: int = 4) -> str:
        """Formats recent chat turns into a readable string for query understanding."""
        recent = self.history[-max_turns * 2:]
        if not recent:
            return "No previous conversation."
        lines = []
        for msg in recent:
            role = "User" if msg["role"] == "user" else "WikiGPT"
            lines.append(f"{role}: {msg['text']}")
        return "\n".join(lines)

    def extract_search_topics(self, user_query: str) -> List[str]:
        """
        Uses Gemini to interpret the user's natural language question (including follow-ups)
        and outputs 1-3 targeted Wikipedia search queries.
        """
        history_context = self.format_history_for_prompt()
        prompt = f"""You are the search planning component of WikiGPT.
Your task is to analyze the user's latest question in the context of recent chat history, and identify what Wikipedia articles should be searched.

Chat History:
{history_context}

Latest User Input:
"{user_query}"

Instructions:
1. If the input is conversational (e.g. greetings, thanks, jokes, personal questions, simple chit-chat) or purely subjective, output: NONE
2. If the user refers to pronouns or previous context (e.g. "when was he born?", "tell me about its discovery"), resolve the entity using the chat history (e.g. if previous chat was about Alexander Fleming, output "Alexander Fleming").
3. Convert conversational questions (e.g. "Can you explain how black holes are formed?") into concise Wikipedia search keywords (e.g. "Black hole, Stellar evolution").
4. Output 1 to 3 search terms separated by commas. Do not write explanations, markdown, or numbered lists.

Search terms:"""

        try:
            response, _ = generate_with_fallback(
                self.client,
                prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=50
                )
            )
            raw = response.text.strip()
            if not raw or "NONE" in raw.upper():
                return []
            
            # Clean and split terms
            terms = [t.strip().strip('"').strip("'") for t in raw.split(",") if t.strip()]
            return terms[:3]
        except Exception:
            # Fallback heuristic: strip common question phrases and punctuation
            cleaned = user_query.strip().rstrip("?.!")
            prefixes = [
                r"^can you (please )?(explain|tell me about) ",
                r"^(please )?(explain|tell me about) ",
                r"^(what|who|where|when|why|how) (is|was|are|were|did|do|does) ",
                r"^(what|who|where|when|why|how) ",
            ]
            for p in prefixes:
                cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE).strip()
            return [cleaned] if len(cleaned) > 2 else []

    def retrieve_wikipedia_info(self, search_terms: List[str]) -> Dict[str, str]:
        """
        Searches Wikipedia for the given terms and retrieves extracts from multiple articles.
        Returns a dict of {title: extract}.
        """
        candidate_titles = []
        for term in search_terms:
            titles = search_wikipedia_titles(term, limit=2)
            for t in titles:
                if t not in candidate_titles:
                    candidate_titles.append(t)
            if len(candidate_titles) >= 3:
                break

        if not candidate_titles:
            return {}

        return fetch_articles_content(candidate_titles[:3])

    def answer_query(self, user_query: str) -> str:
        """Processes the query, gathers Wikipedia context if available, and generates the answer."""
        # Step 1: Extract search keywords taking conversation history into account
        search_terms = self.extract_search_topics(user_query)
        articles = {}

        if search_terms:
            articles = self.retrieve_wikipedia_info(search_terms)

        # Step 2: Formulate prompt based on whether Wikipedia info was retrieved
        if articles:
            sources_list = list(articles.keys())
            sources_note = f"[Consulted Wikipedia: {', '.join(sources_list)}]"
            
            wiki_context_blocks = []
            for title, content in articles.items():
                wiki_context_blocks.append(f"=== Article: {title} ===\n{content}")
            wiki_context = "\n\n".join(wiki_context_blocks)

            system_instruction = (
                "You are WikiGPT, an AI assistant grounded in Wikipedia. "
                "Base your response primarily on the provided Wikipedia context. "
                "Accurately summarize and synthesize information across the provided articles. "
                "Maintain conversational flow with previous chat history. "
                "If certain details are not found in the Wikipedia text, you may supplement from general knowledge, "
                "but cite or mention the Wikipedia articles that provided the core facts."
            )

            prompt = f"""Conversation History:
{self.format_history_for_prompt()}

WIKIPEDIA CONTEXT:
{wiki_context}

User Question: {user_query}
Answer:"""

            try:
                response, _ = generate_with_fallback(
                    self.client,
                    prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.3
                    )
                )
                answer_body = response.text.strip()
                final_answer = f"{sources_note}\n\n{answer_body}"
            except Exception as e:
                final_answer = f"[Error generating answer: {e}]"
        else:
            # Fallback to native mode
            fallback_tag = "[cannot find Wikipedia info, returning to native gpt mode]"

            system_instruction = (
                "You are WikiGPT running in native mode because no Wikipedia articles were found or needed. "
                "Answer the user's question directly, accurately, and politely."
            )

            prompt = f"""Conversation History:
{self.format_history_for_prompt()}

User Question: {user_query}
Answer:"""

            try:
                response, _ = generate_with_fallback(
                    self.client,
                    prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.7
                    )
                )
                answer_body = response.text.strip()
                final_answer = f"{fallback_tag}\n\n{answer_body}"
            except Exception as e:
                final_answer = f"{fallback_tag}\n\n[Error generating answer: {e}]"

        # Update history
        self.history.append({"role": "user", "text": user_query})
        self.history.append({"role": "model", "text": final_answer})

        return final_answer

    def clear_memory(self):
        self.history = []

# ---------------------------------------------------------
# CLI User Interface
# ---------------------------------------------------------
BANNER = """
===========================================================================
  Welcome To WikiGPT!                                                     |
WikiGPT is based on Google Gemini.                                        |
Made with ❤️  By DanDevProjects!                                           |
See more of my projects at https://github.com/dandevprojects .            |
note: AI can make mistakes.                                               |
WikiGPT version 1.0.0 (Gemini 3.5)                                        |
Don't forget to export your API key eveytime you restart your computer.   |
  =========================================================================
"""

def print_help():
    print("""
Available Commands:
  /clear      Clear conversation history
  /history    View current conversation history
  /help       Show this help message
  /exit, /quit Exit WikiGPT
""")

def run_interactive(engine: WikiGPTEngine):
    print(BANNER)
    print("Ready! \n")

    while True:
        try:
            user_input = input("WikiGPT> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/exit", "/quit", "exit", "quit"):
            print("Goodbye!")
            break

        if user_input.lower() == "/clear":
            engine.clear_memory()
            print("✨ Conversation memory cleared.\n")
            continue

        if user_input.lower() == "/help":
            print_help()
            continue

        if user_input.lower() == "/history":
            print("\n--- Current Conversation History ---")
            print(engine.format_history_for_prompt(max_turns=10))
            print("------------------------------------\n")
            continue

        print("\nThinking and searching Wikipedia...\n")
        answer = engine.answer_query(user_input)
        print(f"{answer}\n")
        print("-" * 60)

def main():
    client = genai.Client()
    engine = WikiGPTEngine(client)

    # Support single-shot query via CLI argument: e.g. wikigpt "Who discovered Penicillin?"
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        answer = engine.answer_query(query)
        print(answer)
        sys.exit(0)

    # Interactive REPL mode
    run_interactive(engine)

if __name__ == "__main__":
    main()
