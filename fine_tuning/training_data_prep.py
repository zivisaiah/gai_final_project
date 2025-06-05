import json
import os
from pathlib import Path

def extract_exit_examples(json_path, output_path):
    """Extract representative examples for fine-tuning Exit Advisor (recruiter turns only, OpenAI messages format)."""
    SYSTEM_PROMPT = (
        "You are an exit advisor for a recruitment chatbot. "
        "Only decide to END the conversation if the candidate clearly says they are not interested or wants to stop. "
        "Otherwise, CONTINUE or SCHEDULE as appropriate."
    )
    with open(json_path, 'r', encoding='utf-8') as f:
        conversations = json.load(f)
    
    examples = []
    for conv in conversations:
        for turn in conv.get('turns', []):
            # Only use recruiter turns with a labeled action
            if turn.get('speaker') == 'recruiter' and turn.get('label'):
                action = turn['label'].capitalize()
                prompt = turn.get('text')
                if prompt:
                    example = {
                        'messages': [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt.strip()},
                            {"role": "assistant", "content": action.strip()}
                        ]
                    }
                    examples.append(example)
    print(f"Extracted {len(examples)} labeled recruiter examples.")
    # Save as JSONL for OpenAI fine-tuning (messages format)
    with open(output_path, 'w', encoding='utf-8') as out:
        for ex in examples:
            out.write(json.dumps(ex, ensure_ascii=False) + '\n')
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    json_path = Path(__file__).parent.parent / "resources" / "sms_conversations.json"
    output_path = data_dir / "exit_advisor_finetune.jsonl"
    extract_exit_examples(json_path, output_path) 