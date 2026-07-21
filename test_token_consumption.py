"""
test_token_consumption.py  –  Automated token consumption benchmark script.

Fires test prompts across representative GoodScore flows for both:
  1. Lean Mode (/chat)
  2. Agentic Mode (/agent-chat)

Measures and logs prompt tokens, completion tokens, total tokens, and latency.
"""

import asyncio
import json
import time
import httpx

AI_BACKEND_URL = "http://localhost:8000"

TEST_PROMPTS = [
    {
        "flow": "score_analysis & score_improvement",
        "customer_id": "C001",
        "prompt": "What is my current credit score across bureaus and how can I improve it?"
    },
    {
        "flow": "score_trend_summary",
        "customer_id": "C001",
        "prompt": "Summarize my 12-month credit score trend history."
    },
    {
        "flow": "bill_payment",
        "customer_id": "C001",
        "prompt": "Show my pending utility bills and pay my Tata Power bill."
    },
    {
        "flow": "enquiry_removal",
        "customer_id": "C001",
        "prompt": "Check my credit enquiries and request removal of any unauthorized hard pull."
    },
    {
        "flow": "loan_eligibility",
        "customer_id": "C001",
        "prompt": "Am I eligible for a personal or home loan based on my score?"
    },
    {
        "flow": "noc_mail_draft",
        "customer_id": "C001",
        "prompt": "Draft an NOC request letter for my closed loan account #LN9981 with HDFC Bank."
    }
]


async def run_prompt_test(client: httpx.AsyncClient, endpoint: str, mode_name: str, test_item: dict):
    url = f"{AI_BACKEND_URL}{endpoint}"
    payload = {
        "customer_id": test_item["customer_id"],
        "message": test_item["prompt"],
        "conversation_history": []
    }

    start_time = time.time()
    token_usage = None
    response_text = ""

    try:
        async with client.stream("POST", url, json=payload, timeout=60.0) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    if "content" in data:
                        response_text += data["content"]
                    if "token_usage" in data:
                        token_usage = data["token_usage"]
                except Exception:
                    continue

        latency = time.time() - start_time
        return {
            "flow": test_item["flow"],
            "prompt": test_item["prompt"],
            "mode": mode_name,
            "latency_sec": round(latency, 2),
            "prompt_tokens": token_usage.get("prompt_tokens", 0) if token_usage else 0,
            "completion_tokens": token_usage.get("completion_tokens", 0) if token_usage else 0,
            "total_tokens": token_usage.get("total_tokens", 0) if token_usage else 0,
            "response_snippet": response_text[:80].replace("\n", " ") + "..."
        }
    except Exception as e:
        return {
            "flow": test_item["flow"],
            "prompt": test_item["prompt"],
            "mode": mode_name,
            "error": str(e)
        }


async def main():
    async with httpx.AsyncClient() as client:
        print("\n========================================================")
        print("Running GoodScore AI Token Consumption Benchmark")
        print("========================================================\n")

        results = []

        # 1. Test Lean Mode
        print("--- Testing Lean Mode (/chat) ---")
        for item in TEST_PROMPTS:
            res = await run_prompt_test(client, "/chat", "Lean", item)
            results.append(res)
            print(f"  [Lean] {item['flow']} -> {res.get('total_tokens', 0)} tokens ({res.get('latency_sec', 0)}s)")

        print("\n--- Testing Agentic Mode (/agent-chat) ---")
        for item in TEST_PROMPTS:
            res = await run_prompt_test(client, "/agent-chat", "Agentic", item)
            results.append(res)
            print(f"  [Agentic] {item['flow']} -> {res.get('total_tokens', 0)} tokens ({res.get('latency_sec', 0)}s)")

        print("\n" + "="*85)
        print(f"{'Mode':<10} | {'Flow Category':<35} | {'Prompt Tkn':<10} | {'Comp Tkn':<10} | {'Total Tkn':<10} | {'Latency':<8}")
        print("="*85)
        for r in results:
            if "error" in r:
                print(f"{r['mode']:<10} | {r['flow']:<35} | ERROR: {r['error']}")
            else:
                print(f"{r['mode']:<10} | {r['flow']:<35} | {r['prompt_tokens']:<10} | {r['completion_tokens']:<10} | {r['total_tokens']:<10} | {r['latency_sec']:<7}s")
        print("="*85)

        # Save JSON output artifact
        with open("token_benchmark_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
