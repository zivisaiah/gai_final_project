"""
Quick Test Runner
Simple script to run a basic simulation test
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def quick_test():
    """Run a quick test with one conversation per persona"""
    print(">> QUICK SIMULATION TEST")
    print("=" * 50)
    
    try:
        from simulation_testing.simulation_engine import ConversationSimulator
        from simulation_testing.config.test_config import config
        
        # Validate configuration
        issues = config.validate_config()
        if issues:
            print("X Configuration issues:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        
        print("OK Configuration validated")
        
        # Initialize simulator
        simulator = ConversationSimulator()
        
        # Run quick test with 2 personas
        test_personas = ['eager_junior', 'experienced_senior']
        
        print(f"\n>> Testing personas: {test_personas}")
        print("   (1 conversation each)\n")
        
        results = simulator.run_simulation_batch(test_personas, conversations_per_persona=1)
        
        print("\n>> QUICK TEST COMPLETED!")
        print(f"   Total conversations: {results['total_conversations']}")
        print(f"   Results file: {results['results_file']}")
        
        return True
        
    except ImportError as e:
        print(f"X Import error: {e}")
        print("   Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"X Error: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)