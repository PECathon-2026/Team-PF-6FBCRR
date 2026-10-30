"""Central AI Egress Gateway with Deny-By-Default Security."""
from typing import List, Tuple
from app.models import SanitizedObservation, ActionProposal, AuditEventType
from app.privacy.validator import EgressGateway, EgressBlockedException
from app.audit.logger import audit_logger
from .base import BaseAgent

class ModelEgressGateway:
    def __init__(self, validator: EgressGateway):
        self.validator = validator

    async def execute_model_step(
        self,
        agent: BaseAgent,
        task: str,
        observation: SanitizedObservation,
        history: List[ActionProposal],
    ) -> Tuple[bool, ActionProposal, str]:
        """
        Gated entry point for all AI model reasoning.
        Enforces:
        1. Local payload inspection and canary scanning.
        2. Immediate blocking on any leak attempt or unverified screenshot provenance.
        3. Model action generation only on verified sanitized data.
        Returns:
            (success: bool, proposal: ActionProposal, message: str)
        """
        # Step 1: Enforce strict egress gateway validation
        try:
            self.validator.validate_and_gate(observation)
            audit_logger.log(
                AuditEventType.GATEWAY_INSPECTED,
                observation.run_id,
                {"status": "PASSED", "redactions_count": sum(observation.redactions_summary.values())}
            )
        except EgressBlockedException as block_err:
            audit_logger.log(
                AuditEventType.GATEWAY_BLOCKED,
                observation.run_id,
                {"reason": block_err.reason, "category": block_err.detected_category}
            )
            raise block_err

        # Step 2: Invoke agent with allowlisted sanitized observation
        action = await agent.propose_action(task, observation, history)
        audit_logger.log(
            AuditEventType.ACTION_PROPOSED,
            observation.run_id,
            {"action_type": action.action_type.value, "element_id": action.element_id, "reason": action.reason}
        )

        return True, action, "Model step proposed successfully via egress gateway"
