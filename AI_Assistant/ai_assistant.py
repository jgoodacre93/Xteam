#!/usr/bin/env python3

import json
import os
import sys
import re
import subprocess
import math
from collections import Counter

DATABASE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools_database.json")
OLLAMA_URL = "http://localhost:11434/api/generate"

STOP_WORDS = {
    "i", "want", "to", "test", "for", "a", "an", "the", "and", "or", "on", "in", "at",
    "with", "using", "use", "can", "you", "me", "my", "please", "help", "find", "get",
    "looking", "something", "some", "tool", "tools", "is", "are", "what", "how", "do",
    "does", "should", "could", "would", "might", "may", "will", "shall", "been", "have",
    "has", "had", "was", "were", "be", "being", "been", "am", "not", "no", "yes", "it",
    "this", "that", "these", "those", "he", "she", "they", "them", "his", "her", "their",
    "its", "our", "your", "all", "each", "every", "both", "few", "more", "most", "other",
    "some", "such", "than", "too", "very", "just", "because", "but", "although", "however",
    "therefore", "yet", "still", "also", "even", "only", "own", "same", "so", "if", "then",
    "else", "when", "where", "why", "who", "whom", "whose", "which", "whether", "while",
    "about", "against", "between", "into", "through", "during", "before", "after", "above",
    "below", "from", "up", "down", "out", "off", "over", "under", "again", "further",
    "once", "here", "there", "now", "then", "today", "tomorrow", "yesterday"
}


def load_database():
    if not os.path.exists(DATABASE_FILE):
        return None, None
    with open(DATABASE_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("tools", []), data.get("fallback_tools", [])


def tokenize(text):
    text = text.lower()
    tokens = re.findall(r"[a-z0-9]+", text)
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 2]


def score_tool(tool, query_tokens):
    score = 0.0
    tool_text = " ".join([
        tool.get("tool_name", ""),
        tool.get("category", ""),
        tool.get("description", ""),
        " ".join(tool.get("keywords", [])),
    ]).lower()

    tool_tokens = tokenize(tool_text)

    if not tool_tokens:
        return 0.0

    tool_counter = Counter(tool_tokens)
    query_counter = Counter(query_tokens)

    for token, q_count in query_counter.items():
        if token in tool_counter:
            tf = tool_counter[token] / len(tool_tokens)
            idf = math.log(len(tool_tokens) / (1 + tool_counter[token]))
            score += tf * idf * q_count

    name = tool.get("tool_name", "").lower()
    for token in query_tokens:
        if token in name:
            score += 0.5

    return score


def recommend_tool(query, top_n=3):
    tools, fallback_tools = load_database()
    if not tools:
        return []

    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    scored = []
    for tool in tools:
        s = score_tool(tool, query_tokens)
        if s > 0:
            scored.append((s, tool))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = [tool for _, tool in scored[:top_n]]

    if not results and fallback_tools:
        results = fallback_tools[:top_n]

    return results


def query_ollama(query):
    try:
        payload = json.dumps({
            "model": "xteam-assistant",
            "prompt": (
                "You are Xteam AI, a helpful pentesting assistant. "
                "Given the user query, suggest 1-2 relevant security tools from this list: "
                "nmap, nikto, theHarvester, nuclei, secretsdump, psexec, wmiexec, "
                "airgeddon, wifite2, evilginx2, zphisher, Instagram OSINT, CiLocks. "
                "Reply in JSON with keys: tool_name, category, description, command. "
                f"User query: {query}"
            ),
            "stream": False,
        })
        proc = subprocess.run(
            ["curl", "-s", "-X", "POST", OLLAMA_URL,
             "-H", "Content-Type: application/json",
             "-d", payload],
            capture_output=True, text=True, timeout=30
        )
        if proc.returncode == 0:
            response = json.loads(proc.stdout)
            return response.get("response", "")
    except Exception:
        pass
    return None


def format_recommendation(tool, rank):
    lines = []
    lines.append(f"\033[1;36m#{rank} -> \033[1;37m{tool.get('tool_name', 'Unknown')}\033[0m")
    lines.append(f"    \033[1;33mCategory   :\033[0m {tool.get('category', 'N/A')}")
    lines.append(f"    \033[1;33mWhy use it:\033[0m {tool.get('description', 'No description available.')}")
    lines.append(f"    \033[1;32mCommand    :\033[0m {tool.get('command', 'N/A')}")
    return "\n".join(lines)


def chat_mode():
    print("\033[1;36m╔══════════════════════════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║\033[0m              \033[1;37mXteam AI Assistant - Chat Mode\033[1;36m              ║\033[0m")
    print("\033[1;36m╚══════════════════════════════════════════════════════════════╝\033[0m")
    print("\033[1;33mType 'exit' or 'quit' to return to the main menu.\033[0m\n")

    while True:
        try:
            query = input("\033[1;34mYou\033[0m: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\033[1;33m[!] Returning to menu...\033[0m")
            break

        if not query:
            continue
        if query.lower() in ("exit", "quit", "bye"):
            print("\033[1;36m[*] Goodbye! Stay authorized.\033[0m")
            break

        print("\033[1;35mAI\033[0m: ", end="")

        ollama_response = query_ollama(query)
        if ollama_response:
            print(ollama_response)
            continue

        results = recommend_tool(query, top_n=3)

        if not results:
            print(
                "\n\033[1;33mHmm, I couldn't find a perfect match for that.\033[0m\n"
                "\033[1;36mHere are some solid general-purpose tools that work for most scenarios:\033[0m\n"
            )
            results = recommend_tool("general recommendation", top_n=3)

        print()
        for idx, tool in enumerate(results, 1):
            print(format_recommendation(tool, idx))
            print()

        if results:
            print("\033[1;36mTip: Select a tool from the main menu to run it directly.\033[0m")


def single_query_mode(query):
    ollama_response = query_ollama(query)
    if ollama_response:
        print(f"\033[1;35mAI\033[0m: {ollama_response}")
        return

    results = recommend_tool(query, top_n=3)
    if not results:
        print("\033[1;33m[!] No specific match found. Here are general recommendations:\033[0m\n")
        results = recommend_tool("general recommendation", top_n=3)

    print("\033[1;35mAI\033[0m: Based on what you said, here are my top picks:\n")
    for idx, tool in enumerate(results, 1):
        print(format_recommendation(tool, idx))
        print()
    print("\033[1;36mTip: You can launch any of these from the Xteam main menu.\033[0m")


def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        single_query_mode(query)
    else:
        chat_mode()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n\033[1;33m[!] Interrupted. Returning to menu...\033[0m")
        sys.exit(0)
