import json
import numpy as np
from pathlib import Path
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple
import asyncio

def load_test_data(jsonl_path: str) -> List[Dict]:
    """Load test data from JSONL file."""
    examples = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            examples.append(json.loads(line))
    return examples

async def evaluate_exit_decisions(
    test_data: List[Dict],
    exit_advisor,
    threshold: float = 0.85
) -> Tuple[np.ndarray, Dict]:
    """
    Evaluate Exit Advisor's decisions against ground truth.
    
    Args:
        test_data: List of test examples
        exit_advisor: Exit Advisor instance
        threshold: Confidence threshold for exit decisions
    
    Returns:
        Tuple of (confusion matrix, classification report)
    """
    y_true = []
    y_pred = []
    
    for example in test_data:
        # Get ground truth from the last assistant message
        true_action = example['messages'][-1]['content'].strip().upper()
        y_true.append(true_action)
        
        # Get model prediction
        user_message = example['messages'][1]['content']
        conversation_history = example['messages'][:-1]  # all except last (assistant label)
        decision = await exit_advisor.analyze_conversation(user_message, conversation_history)
        # Map decision to action label
        if decision.should_exit:
            pred_action = "END"
        elif "schedule" in user_message.lower():
            pred_action = "SCHEDULE"
        else:
            pred_action = "CONTINUE"
        y_pred.append(pred_action)
    
    # Calculate confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=['CONTINUE', 'SCHEDULE', 'END'])
    
    # Generate classification report
    report = classification_report(y_true, y_pred, output_dict=True)
    
    return cm, report

def plot_confusion_matrix(cm: np.ndarray, labels: List[str], title: str = "Exit Advisor Confusion Matrix"):
    """Plot confusion matrix with seaborn."""
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=labels, yticklabels=labels)
    plt.title(title)
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    
    # Save plot
    output_dir = Path(__file__).parent / "evaluation_results"
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / "confusion_matrix.png")
    plt.close()

def save_evaluation_results(report: Dict, output_path: str):
    """Save evaluation metrics to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

def compare_with_baseline(
    exit_advisor_results: Dict,
    baseline_results: Dict,
    output_path: str
):
    """Compare fine-tuned model with baseline model."""
    comparison = {
        'fine_tuned': exit_advisor_results,
        'baseline': baseline_results,
        'improvement': {}
    }
    
    # Calculate improvements for each metric
    for metric in ['precision', 'recall', 'f1-score']:
        for label in ['CONTINUE', 'SCHEDULE', 'END']:
            if label in exit_advisor_results and label in baseline_results:
                improvement = (
                    exit_advisor_results[label][metric] - 
                    baseline_results[label][metric]
                )
                comparison['improvement'][f"{label}_{metric}"] = improvement
    
    # Save comparison results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2)

if __name__ == "__main__":
    # Example usage
    from app.modules.agents.exit_advisor import ExitAdvisor
    
    # Initialize Exit Advisor
    exit_advisor = ExitAdvisor()
    
    # Load test data
    test_data_path = Path(__file__).parent.parent / "fine_tuning" / "data" / "exit_advisor_test.jsonl"
    test_data = load_test_data(str(test_data_path))
    
    # Run async evaluation
    cm, report = asyncio.run(evaluate_exit_decisions(test_data, exit_advisor))
    
    # Plot and save confusion matrix
    plot_confusion_matrix(cm, ['CONTINUE', 'SCHEDULE', 'END'])
    
    # Save evaluation results
    output_dir = Path(__file__).parent / "evaluation_results"
    output_dir.mkdir(exist_ok=True)
    save_evaluation_results(report, output_dir / "evaluation_metrics.json")
    
    # TODO: Add baseline model comparison when available
    # compare_with_baseline(report, baseline_report, output_dir / "model_comparison.json") 