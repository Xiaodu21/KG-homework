import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from two_stage import two_stage_qa

SUPPORTED_RELS = {"歌手", "作词", "作曲"}

TEST_CASES = [
    {
        "question": "七里香是谁唱的？",
        "keywords": ["周杰伦"],
        "expected_triples": [("七里香", "歌手", "周杰伦")]
    },
    {
        "question": "青花瓷的作词人是谁？",
        "keywords": ["方文山"],
        "expected_triples": [("青花瓷", "作词", "方文山")]
    },
    {
        "question": "周杰伦演唱过什么歌曲？",
        "keywords": ["七里香", "青花瓷", "双截棍"],
        "expected_triples": []
    },
    {
        "question": "夜曲的作曲是谁？",
        "keywords": ["周杰伦"],
        "expected_triples": [("夜曲", "作曲", "周杰伦")]
    },
    {
        "question": "发如雪收录在哪张专辑？",
        "keywords": ["十一月的肖邦"],
        "expected_triples": [("发如雪", "所属专辑", "十一月的肖邦")]
    }
]


def normalize_text(text: str) -> str:
    if text is None:
        return ""
    text = str(text)
    text = re.sub(r"\s+", "", text)
    return text.strip(" ,，。.!！？?;；:：\"'“”‘’（）()[]【】《》")


def answer_contains_any(answer: str, keywords) -> bool:
    if not keywords:
        return False
    normalized_answer = normalize_text(answer)
    return any(normalize_text(k) in normalized_answer for k in keywords)


def normalize_triples(triples):
    normalized = set()
    for triple in triples:
        if len(triple) != 3:
            continue
        head, rel, tail = triple
        normalized.add((normalize_text(head), normalize_text(rel), normalize_text(tail)))
    return normalized


def calculate_metrics(results):
    total = len(results)
    correct_count = 0
    correct_total = 0
    hallucination_detected_count = 0
    kg_usage_count = 0

    tp_triples = 0
    fp_triples = 0
    fn_triples = 0
    triple_cases = 0

    print(f"\n{'='*20} EVALUATION REPORT {'='*20}")

    for res in results:
        q = res["question"]
        final_ans = res["result"].get("final_answer", "")
        is_hallucination = res["result"].get("is_hallucination")
        extracted_raw = res["result"].get("stage_2_extracted_triples", [])
        extracted_triples = normalize_triples([tuple(t) for t in extracted_raw])

        is_correct = answer_contains_any(final_ans, res["keywords"])
        if res["keywords"]:
            correct_total += 1
            if is_correct:
                correct_count += 1

        if is_hallucination:
            hallucination_detected_count += 1

        if res["result"].get("source") in ["corrected_by_kg", "verified_by_kg_triple"]:
            kg_usage_count += 1

        expected = [t for t in res["expected_triples"] if t[1] in SUPPORTED_RELS]
        expected_triples = normalize_triples(expected)

        if expected_triples:
            triple_cases += 1
            tp = len(extracted_triples & expected_triples)
            fp = len(extracted_triples - expected_triples)
            fn = len(expected_triples - extracted_triples)
            tp_triples += tp
            fp_triples += fp
            fn_triples += fn

        print(f"Q: {q}")
        print(f"  Ans: {final_ans}")
        print(f"  Correct: {is_correct}")
        print(f"  Extracted: {extracted_triples}")
        print(f"  Expected: {expected_triples}")
        print(f"  Source: {res['result'].get('source')}")
        print(f"  Match Result: {res['result'].get('stage_4_match_result')}")
        print("-" * 30)

    precision = tp_triples / (tp_triples + fp_triples) if (tp_triples + fp_triples) > 0 else 0
    recall = tp_triples / (tp_triples + fn_triples) if (tp_triples + fn_triples) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print(f"\nTotal Questions: {total}")
    if correct_total:
        print(f"Accuracy (Keyword Match): {correct_count/correct_total:.2%}")
    else:
        print("Accuracy (Keyword Match): N/A")
    print(f"Hallucination Detection Rate: {hallucination_detected_count/total:.2%}")
    print(f"KG Usage Rate: {kg_usage_count/total:.2%}")
    print(f"Triple Cases: {triple_cases}")
    print("Triple Extraction Metrics (Supported Relations Only):")
    print(f"  Precision: {precision:.2%}")
    print(f"  Recall: {recall:.2%}")
    print(f"  F1 Score: {f1:.2%}")


if __name__ == "__main__":
    results = []
    print("Starting evaluation...")
    for case in TEST_CASES:
        try:
            res = two_stage_qa(case["question"])
            results.append({
                "question": case["question"],
                "keywords": case["keywords"],
                "expected_triples": case["expected_triples"],
                "result": res
            })
        except Exception as e:
            print(f"Error processing {case['question']}: {e}")

    calculate_metrics(results)
