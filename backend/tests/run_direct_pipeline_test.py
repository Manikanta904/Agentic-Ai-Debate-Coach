import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.ai.orchestrator.debate_graph import debate_orchestrator

def main():
    cybersecurity_argument = (
        "Everyone knows that upgrading our firewall is completely useless because the IT manager is incompetent and irresponsible. "
        "Either we replace the entire network infrastructure immediately or our company will go bankrupt tomorrow. "
        "I talked to one employee yesterday who said his laptop was slow, which proves all computers across the entire company are infected with malware."
    )

    print("Executing full 8-agent LangGraph debate pipeline directly...", flush=True)
    res = debate_orchestrator.invoke(
        session_id=1,
        argument=cybersecurity_argument,
        debate_format="One-on-One",
        difficulty="Intermediate",
        user_position="Affirmative",
        current_round=1
    )

    print(f"\nRes Keys ({len(res.keys())}): {list(res.keys())}", flush=True)
    for k, v in res.items():
        print(f"Key: '{k}' -> Type: {type(v).__name__} -> Value snippet: {str(v)[:120]}", flush=True)

if __name__ == "__main__":
    main()
