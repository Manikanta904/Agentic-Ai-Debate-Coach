import sys
import os
import json
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.main import app

def test_live_api_endpoint():
    client = TestClient(app)
    url = "/api/v1/ai/analyze"
    payload = {
        "session_id": 1,
        "argument": (
            "Everyone knows that upgrading our firewall is completely useless because the IT manager is incompetent and irresponsible. "
            "Either we replace the entire network infrastructure immediately or our company will go bankrupt tomorrow. "
            "I talked to one employee yesterday who said his laptop was slow, which proves all computers across the entire company are infected with malware."
        ),
        "debate_format": "One-on-One",
        "difficulty": "Intermediate",
        "user_position": "Affirmative",
        "current_round": 1
    }

    print(f"Calling FastAPI POST {url} endpoint via TestClient...", flush=True)
    response = client.post(url, json=payload)
    print(f"Status Code: {response.status_code}", flush=True)
    
    res_json = response.json()
    print("\n=================== COMPLETE API JSON RESPONSE ===================", flush=True)
    print(json.dumps(res_json, indent=2), flush=True)
    print("==================================================================", flush=True)
    
    data = res_json.get("data", {})
    print("\n--- 8-AGENT PIPELINE VERIFICATION SUMMARY ---", flush=True)
    print(f"Success: {res_json.get('success')}", flush=True)
    print(f"Execution Status: {data.get('execution_status')}", flush=True)
    print(f"1. Argument Analysis: {'PRESENT' if data.get('argument_analysis') else 'MISSING'}", flush=True)
    print(f"2. Logical Fallacies: {'PRESENT' if data.get('logical_fallacy_analysis') else 'MISSING'}", flush=True)
    if data.get('logical_fallacy_analysis'):
        fallacies = data['logical_fallacy_analysis'].get('detected_fallacies', [])
        print(f"   Detected Fallacies Count: {len(fallacies)}", flush=True)
        for f in fallacies:
            print(f"     * [{f.get('severity')}] {f.get('fallacy_type')}: '{f.get('snippet') or f.get('excerpt')}'", flush=True)
    print(f"3. Counterargument: {'PRESENT' if data.get('counterargument_analysis') else 'MISSING'}", flush=True)
    print(f"4. AI Debate Simulation Opponent: {'PRESENT' if data.get('debate_simulation') else 'MISSING'}", flush=True)
    print(f"5. Judge Evaluation: {'PRESENT' if data.get('judge_evaluation') else 'MISSING'}", flush=True)
    print(f"6. Performance Score: {'PRESENT' if data.get('performance_score') else 'MISSING'}", flush=True)
    if data.get('performance_score'):
        print(f"   Overall Weighted Score: {data['performance_score'].get('overall_score')}%", flush=True)
    print(f"7. Coaching: {'PRESENT' if data.get('coaching') else 'MISSING'}", flush=True)
    print(f"8. Recommendations: {'PRESENT' if data.get('recommendations') else 'MISSING'}", flush=True)
    print(f"   Learning Path: {'PRESENT' if data.get('learning_path') else 'MISSING'}", flush=True)
    print(f"   Observability Metadata: {'PRESENT' if data.get('metadata') else 'MISSING'}", flush=True)

if __name__ == "__main__":
    test_live_api_endpoint()
