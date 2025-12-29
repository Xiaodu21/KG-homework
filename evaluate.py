import sys
import os
import re

# Add the current directory to sys.path so we can import back_end modules
sys.path.append(os.path.join(os.getcwd(), 'back_end'))

from two_stage import two_stage_qa

# Golden Dataset: (Question, Expected Answer Keywords, Expected Triples)
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
        "keywords": ["七里香", "青花瓷", "双截棍"], # Just check for some common ones
        "expected_triples": [] # Hard to define all, maybe skip triple eval for this type
    },
    {
        "question": "夜曲的作曲是谁？",
        "keywords": ["周杰伦"],
        "expected_triples": [("夜曲", "作曲", "周杰伦")]
    },
    {
        "question": "发如雪收录在哪张专辑？",
        "keywords": ["十一月的肖邦"],
        "expected_triples": [("发如雪", "所属专辑", "十一月的肖邦")] # System only handles singer/composer/lyricist currently?
    }
]

def calculate_metrics(results):
    total = len(results)
    correct_count = 0
    hallucination_detected_count = 0
    kg_correction_count = 0
    
    tp_triples = 0
    fp_triples = 0
    fn_triples = 0

    print(f"\n{'='*20} EVALUATION REPORT {'='*20}")
    
    for res in results:
        q = res['question']
        final_ans = res['result']['final_answer']
        is_hallucination = res['result']['is_hallucination']
        extracted_triples = set(tuple(t) for t in res['result']['stage_2_extracted_triples'])
        
        # Check correctness
        is_correct = any(k in final_ans for k in res['keywords'])
        if is_correct:
            correct_count += 1
            
        # Check stats
        if is_hallucination:
            hallucination_detected_count += 1
        if res['result']['source'] in ['corrected_by_kg', 'verified_by_kg_triple']:
            kg_correction_count += 1 # Actually verified is also good usage of KG

        # Check triples
        expected = set(res['expected_triples'])
        
        # Only evaluate triples for supported relation types
        supported_rels = {"歌手", "作词", "作曲"}
        expected = {t for t in expected if t[1] in supported_rels}
        
        if expected:
            tp = len(extracted_triples.intersection(expected))
            fp = len(extracted_triples - expected)
            fn = len(expected - extracted_triples)
            
            tp_triples += tp
            fp_triples += fp
            fn_triples += fn

        print(f"Q: {q}")
        print(f"  Ans: {final_ans} | Correct: {is_correct}")
        print(f"  Extracted: {extracted_triples}")
        print(f"  Expected: {expected}")
        print(f"  Source: {res['result']['source']}")
        print("-" * 30)

    precision = tp_triples / (tp_triples + fp_triples) if (tp_triples + fp_triples) > 0 else 0
    recall = tp_triples / (tp_triples + fn_triples) if (tp_triples + fn_triples) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print(f"\nTotal Questions: {total}")
    print(f"Accuracy (Keyword Match): {correct_count/total:.2%}")
    print(f"Hallucination Detection Rate: {hallucination_detected_count/total:.2%}")
    print(f"KG Usage Rate: {kg_correction_count/total:.2%}")
    print(f"\nTriple Extraction Metrics (Supported Relations Only):")
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
