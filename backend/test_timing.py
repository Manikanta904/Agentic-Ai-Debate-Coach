import sys, os
sys.path.insert(0, os.path.abspath('.'))

import time
from time import perf_counter
from app.ai.orchestrator.debate_graph import debate_orchestrator

def measure():
    test_argument = """I strongly believe governments should subsidize the development of biodegradable electronic devices because electronic waste is one of the biggest environmental problems in the world. If governments do not provide subsidies immediately, electronic waste will continue increasing until our environment becomes impossible to recover and future generations will suffer from permanent pollution.

Everyone knows that biodegradable electronics are better for the environment than traditional electronics. Since biodegradable materials can break down naturally, these devices will automatically solve the electronic-waste problem. Therefore, governments should provide large subsidies to every company developing biodegradable electronics."""

    print("=== STARTING PIPELINE TIMING TEST ===", flush=True)
    print(f"| {'Node Name':30s} | {'Time (ms)':10s} |", flush=True)
    print("-" * 47, flush=True)
    t0 = perf_counter()
    result = debate_orchestrator.invoke(
        session_id=101,
        argument=test_argument,
        user_id=1,
        debate_format="Public Forum Debate",
        difficulty="Intermediate",
        user_position="Affirmative",
        current_round=1
    )
    t1 = perf_counter()

    total_time = t1 - t0
    print("-" * 47, flush=True)
    print(f"\n==========================================")
    print(f"TOTAL PIPELINE EXECUTION TIME: {total_time:.2f} seconds ({int(total_time*1000)} ms)")
    print(f"STATUS: {result.get('execution_status')}")
    print(f"ERRORS: {result.get('errors')}")
    print(f"==========================================")

if __name__ == "__main__":
    measure()
