from datetime import datetime
import json

class CognitiveInspector:
    """
    Developer tool for transparency and debuggability.
    Dumps the internal state of the Cognitive Pipeline to the console.
    """
    
    @staticmethod
    def log_interaction(
        face_id: str, 
        name: str,
        retrieved_count: int,
        attention_decision, # AttentionDecision
        prompt: str,
        generated_response: str,
        final_action: str
    ):
        print("\n" + "="*50)
        print("🧠 COGNITIVE INSPECTOR: INTERACTION LOG")
        print("="*50)
        print(f"Time           : {datetime.now().strftime('%H:%M:%S')}")
        print(f"Detected Person: {name} (ID: {face_id})")
        print(f"Memories Found : {retrieved_count} relevant episodes/semantic nodes")
        
        print("\n--- Attention Engine ---")
        print(f"Decision       : {'INTERRUPT' if attention_decision.should_interrupt else 'SILENCE'}")
        if attention_decision.should_interrupt:
            print(f"Selected       : {len(attention_decision.selected_memories)} memories")
            for m in attention_decision.selected_memories:
                meta = f"[Conf: {getattr(m, 'confidence', 1.0):.2f} | Usefulness: {getattr(m, 'historical_usefulness', 0.5):.2f}]"
                print(f"  -> {m.summary} {meta}")
                
        print("\n--- Language Generation ---")
        if not attention_decision.should_interrupt:
            print("Prompt         : (Skipped)")
            print("Output         : (Skipped)")
        else:
            # Truncate prompt for readability
            print("Prompt Sent    : " + prompt.split("Task:")[0].replace('\n', ' ')[:100] + "...")
            print(f"LLM Output     : {generated_response}")
            
        print("\n--- Final Action ---")
        print(f"Action         : {final_action}")
        print("="*50 + "\n")
