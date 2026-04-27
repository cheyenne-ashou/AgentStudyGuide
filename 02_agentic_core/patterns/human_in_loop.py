"""
Human-in-the-Loop Pattern
Demonstrates two human oversight mechanisms:
  1. Approval gate — agent pauses and asks human before taking a risky action
  2. Feedback injection — human reviews draft output and agent incorporates changes

When to require human approval:
  - Irreversible actions (delete, send email, deploy)
  - Low-confidence outputs (score < threshold)
  - High-stakes decisions (financial, medical, legal)
  - First time an agent takes a new action type

Run: python 02_agentic_core/patterns/human_in_loop.py
"""
import sys
from pathlib import Path

_root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
sys.path.insert(0, str(_root))

from core.client import get_client, MODEL, cached_system


def simulate_human_input(prompt: str, auto_response: str = "") -> str:
    """In real usage this would be input(). Here we auto-respond for demo."""
    print(f"\n  [HUMAN PROMPT]: {prompt}")
    if auto_response:
        print(f"  [AUTO-RESPONSE]: {auto_response}")
        return auto_response
    return input("  > ")


class HumanInLoopAgent:
    """
    Agent that pauses for human approval on risky actions and
    incorporates human feedback on draft outputs.
    """

    RISKY_ACTIONS = {"send_email", "delete_file", "execute_code", "deploy", "payment"}

    def __init__(self, auto_approve: bool = False, auto_feedback: str = ""):
        self.client = get_client()
        self.auto_approve = auto_approve
        self.auto_feedback = auto_feedback
        self.approved_count = 0
        self.rejected_count = 0

    def _request_approval(self, action: str, details: str) -> bool:
        """Ask human for approval before executing a risky action."""
        print(f"\n  ⚠️  APPROVAL REQUIRED")
        print(f"  Action: {action}")
        print(f"  Details: {details}")

        if self.auto_approve:
            print(f"  [AUTO-APPROVED for demo]")
            self.approved_count += 1
            return True

        response = simulate_human_input("Approve? (y/n)", "y")
        approved = response.lower().strip() in ("y", "yes", "1", "")
        if approved:
            self.approved_count += 1
            print("  ✓ Approved")
        else:
            self.rejected_count += 1
            print("  ✗ Rejected")
        return approved

    def _get_feedback(self, draft: str) -> str:
        """Ask human to review a draft and return feedback."""
        print(f"\n  📝 DRAFT FOR REVIEW:")
        print(f"  {draft[:300]}")

        if self.auto_feedback:
            print(f"  [AUTO-FEEDBACK]: {self.auto_feedback}")
            return self.auto_feedback

        feedback = simulate_human_input(
            "Any changes needed? (press Enter to approve as-is)",
            ""
        )
        return feedback.strip()

    def execute_task_with_approval(self, task: str) -> str:
        """Run task, pausing for approval on risky actions."""
        print(f"\nTask: {task}")
        print("─" * 50)

        # Simulate agent deciding it needs to send an email
        risky_action = "send_email"
        email_draft = (
            "To: team@company.com\n"
            "Subject: Weekly Status Update\n"
            "Body: This week we completed the RAG implementation and started testing."
        )

        approved = self._request_approval(risky_action, email_draft)
        if not approved:
            return "Task aborted — user rejected the email action."

        print("\n  [Executing approved action: send_email]")
        return "Email sent successfully. Task complete."

    def execute_with_feedback_loop(self, task: str, max_revisions: int = 3) -> str:
        """Generate output, get human feedback, revise until approved."""
        print(f"\nTask: {task}")
        print("─" * 50)

        messages = [{"role": "user", "content": task}]
        system = cached_system(
            "You are a helpful writing assistant. Produce clear, concise output."
        )

        for revision in range(1, max_revisions + 1):
            print(f"\n  [Revision {revision}] Generating...")
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=512,
                system=system,
                messages=messages,
            )
            draft = response.content[0].text.strip()

            feedback = self._get_feedback(draft)

            if not feedback:
                print("  ✓ Human approved the output.")
                return draft

            print(f"\n  [Incorporating feedback: '{feedback[:60]}']")
            messages.append({"role": "assistant", "content": draft})
            messages.append({
                "role": "user",
                "content": f"Please revise based on this feedback: {feedback}"
            })

        print("  ⚠️  Max revisions reached. Returning last draft.")
        return draft


if __name__ == "__main__":
    print("=== HUMAN-IN-THE-LOOP DEMO ===")

    # ── Part 1: Approval Gate ─────────────────────────────────────────────────
    print("\n=== Part 1: Approval Gate (auto-approve for demo) ===")
    agent = HumanInLoopAgent(auto_approve=True)
    result = agent.execute_task_with_approval(
        "Summarize this week's engineering work and send an update email to the team."
    )
    print(f"\nResult: {result}")
    print(f"Approved: {agent.approved_count}, Rejected: {agent.rejected_count}")

    # ── Part 2: Feedback Loop ─────────────────────────────────────────────────
    print("\n\n=== Part 2: Feedback Loop (auto-feedback for demo) ===")
    agent2 = HumanInLoopAgent(
        auto_feedback="Make it more concise and add bullet points."
    )
    final = agent2.execute_with_feedback_loop(
        "Write a brief summary of what RAG (Retrieval-Augmented Generation) is."
    )
    print(f"\nFinal Output:\n{final}")

    print("\n--- When to use Human-in-the-Loop ---")
    approval_triggers = [
        ("Irreversible actions", "delete, send, deploy, payment"),
        ("Low confidence", "agent confidence score < threshold"),
        ("High stakes", "financial, medical, legal decisions"),
        ("New action type", "first time agent tries something new"),
        ("Policy violation", "output flagged by guardrails"),
    ]
    for trigger, example in approval_triggers:
        print(f"  {trigger:<25} → {example}")

    print("\n--- Tradeoffs ---")
    print("  Human-in-loop improves safety but adds latency and reduces autonomy.")
    print("  Good systems progressively reduce approval requirements as agent builds trust.")
