import json
import os
import pytest
from app.modules.agents.exit_advisor import ExitAdvisor

# Path to labeled data
DATA_PATH = os.path.join(os.path.dirname(__file__), '../resources/sms_conversations.json')

@pytest.mark.asyncio
async def test_exit_advisor_on_labeled_data():
    """Evaluate Exit Advisor accuracy on labeled real-world examples."""
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        conversations = json.load(f)

    # Collect (input, label) pairs
    examples = []
    for conv in conversations:
        for turn in conv.get('turns', []):
            if turn.get('speaker') == 'recruiter' and turn.get('label'):
                examples.append({
                    'text': turn['text'],
                    'label': turn['label'].strip().upper()  # e.g. END, CONTINUE, SCHEDULE
                })

    advisor = ExitAdvisor()
    correct = 0
    total = 0
    errors = []

    for ex in examples:
        # Only test END/CONTINUE (ignore SCHEDULE for Exit Advisor)
        if ex['label'] not in ('END', 'CONTINUE'):
            continue
        decision = await advisor.analyze_conversation(ex['text'], [])
        pred = 'END' if decision.should_exit else 'CONTINUE'
        if pred == ex['label']:
            correct += 1
        else:
            errors.append({'input': ex['text'], 'label': ex['label'], 'pred': pred, 'reason': decision.reason})
        total += 1

    accuracy = correct / total if total else 0
    print(f"Exit Advisor accuracy: {accuracy:.2%} ({correct}/{total})")
    if errors:
        print(f"\nMisclassified examples ({len(errors)}):")
        for err in errors[:10]:  # Show up to 10
            print(f"Input: {err['input']}\n  Label: {err['label']}  Pred: {err['pred']}  Reason: {err['reason']}\n")
    assert accuracy > 0.7  # Example threshold, adjust as needed

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_exit_advisor_on_labeled_data()) 