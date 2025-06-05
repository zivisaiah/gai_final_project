import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import pytest
from app.modules.agents.core_agent import CoreAgent, AgentDecision

# Path to labeled data
DATA_PATH = os.path.join(os.path.dirname(__file__), '../resources/sms_conversations.json')

@pytest.mark.asyncio
async def test_core_agent_on_labeled_data():
    """Evaluate CoreAgent accuracy on labeled real-world recruiter turns."""
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

    agent = CoreAgent()
    correct = 0
    total = 0
    errors = []

    for idx, ex in enumerate(examples[:5]):  # Limit to first 5 for speed
        print(f"Running example {idx+1}/5...")
        conv_id = f"eval_test_{idx}"
        response, decision, reasoning = await agent.process_message_async(ex['text'], conversation_id=conv_id)
        pred = decision.value
        if pred == ex['label']:
            correct += 1
        else:
            errors.append({'input': ex['text'], 'label': ex['label'], 'pred': pred, 'reason': reasoning})
        total += 1

    accuracy = correct / total if total else 0
    print(f"CoreAgent accuracy: {accuracy:.2%} ({correct}/{total})")
    if errors:
        print(f"\nMisclassified examples ({len(errors)}):")
        for err in errors[:10]:  # Show up to 10
            print(f"Input: {err['input']}\n  Label: {err['label']}  Pred: {err['pred']}  Reason: {err['reason']}\n")
    assert accuracy > 0.7  # Example threshold, adjust as needed

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_core_agent_on_labeled_data()) 