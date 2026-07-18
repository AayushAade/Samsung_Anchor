from datetime import datetime
import json

class CognitiveInspector:
    """
    Developer tool for transparency and debuggability.
    Renders the internal state, context fusion, and reasoning of Samsung Anchor.
    """
    
    @staticmethod
    def print_pipeline_run(
        cognitive_context, 
        attention_decision, 
        goal_hypotheses=None,
        prompt: str = "",
        generated_response: str = "",
        final_action: str = ""
    ) -> None:
        print("\n================================================================")
        print("  SAMSUNG ANCHOR : COGNITIVE TRACE")
        print("================================================================\n")
        
        print("--- Context Fusion ---")
        print(f"Providers Executed : {len(cognitive_context.provider_latencies)}")
        for provider, latency in cognitive_context.provider_latencies.items():
            print(f"  -> {provider}: {latency:.1f}ms")
        
        if cognitive_context.dropped_providers:
            print(f"Dropped Providers  : {', '.join(cognitive_context.dropped_providers)}")
            
        print(f"\nIdentity Context   : {cognitive_context.identity.name if cognitive_context.identity and cognitive_context.identity.name else 'Unknown'}")
        print(f"Temporal Context   : {cognitive_context.temporal.time_of_day if cognitive_context.temporal else 'Unknown'}")
        
        mem_count = len(cognitive_context.memory.memories) if cognitive_context.memory else 0
        print(f"Memory Context     : {mem_count} items retrieved")

        print("\n--- Goal Reasoning ---")
        if goal_hypotheses:
            for i, g in enumerate(goal_hypotheses, 1):
                print(f"  [{i}] {g.name:30s} : {g.confidence:.2f}  ({g.state.value})")
                if g.supporting_evidence:
                    evidence_str = ", ".join(
                        f"{e.signal} (+{e.weight:.2f})" for e in g.supporting_evidence[-3:]
                    )
                    print(f"      Supporting : {evidence_str}")
                if g.contradicting_evidence:
                    evidence_str = ", ".join(
                        f"{e.signal} (-{e.weight:.2f})" for e in g.contradicting_evidence[-3:]
                    )
                    print(f"      Contradicting: {evidence_str}")
        else:
            print("  (No goal hypotheses generated)")

        print("\n--- Executive Function (Attention Engine) ---")
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
