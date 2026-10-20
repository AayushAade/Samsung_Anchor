from datetime import datetime

class ConfidenceManager:
    """
    Handles the mathematical growth and decay of memory confidence 
    based on meta-cognitive feedback.
    """
    
    @staticmethod
    def update_on_confirmation(node) -> None:
        """
        Increases confidence and tracks verification.
        """
        node.confirmation_count += 1
        node.last_confirmed = datetime.now().isoformat()
        
        # Confidence approaches 1.0 asymptotically
        # e.g., 0.5 -> 0.75 -> 0.875 -> 0.9375
        node.confidence = node.confidence + (1.0 - node.confidence) * 0.5
        node.verification_status = "Verified"
        
        # A confirmed memory is historically useful
        node.historical_usefulness = min(1.0, node.historical_usefulness + 0.1)

    @staticmethod
    def update_on_correction(node) -> None:
        """
        Severely penalizes confidence.
        """
        node.correction_count += 1
        node.last_corrected = datetime.now().isoformat()
        
        # Correction is a strong negative signal, cut confidence in half
        node.confidence = node.confidence * 0.5
        node.verification_status = "Corrected"
        
        # A corrected memory was likely annoying or wrong
        node.historical_usefulness = max(0.0, node.historical_usefulness - 0.3)

    @staticmethod
    def update_on_ignored(node) -> None:
        """
        Implicit feedback that the interaction was unnecessary.
        """
        # Slightly reduce usefulness, but leave confidence alone
        node.historical_usefulness = max(0.0, node.historical_usefulness - 0.1)

    @staticmethod
    def compute_composite_confidence(
        perception_confidence: float = 1.0,
        speech_confidence: float = 1.0,
        retrieval_confidence: float = 1.0,
        reasoning_confidence: float = 1.0,
    ) -> float:
        """
        Combine upstream subsystem confidences mathematically.
        Final = C_perception * C_speech * C_retrieval * C_reasoning
        """
        c_p = max(0.0, min(1.0, perception_confidence))
        c_s = max(0.0, min(1.0, speech_confidence))
        c_r = max(0.0, min(1.0, retrieval_confidence))
        c_re = max(0.0, min(1.0, reasoning_confidence))
        return round(c_p * c_s * c_r * c_re, 4)

