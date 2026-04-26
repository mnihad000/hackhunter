"""Service layer package for business logic."""

from backend.services.agent import build_user_context, decide_and_generate_nudge
from backend.services.feedback_service import save_feedback
from backend.services.message_classifier import MessageKind, classify_message
from backend.services.nudge_models import NudgeDecision, PolicyDecision, Prediction, ProviderResult, UserContext
from backend.services.nudge_policy import evaluate_nudge_eligibility
from backend.services.plaid import create_link_token, exchange_public_token, handle_plaid_webhook, sync_user_transactions
from backend.services.prediction import predict_for_user
from backend.services.scheduler import process_user_nudges, run_nudge_cycle
from backend.services.sms_replies import build_sms_reply
from backend.services.transaction_parser import ParsedTransaction, parse_transaction
from backend.services.transaction_service import save_transaction
from backend.services.twilio_auth import validate_twilio_request
from backend.services.twilio_sender import send_sms
from backend.services.user_service import get_or_create_user_by_phone

__all__ = [
    "MessageKind",
    "NudgeDecision",
    "ParsedTransaction",
    "PolicyDecision",
    "Prediction",
    "ProviderResult",
    "UserContext",
    "build_sms_reply",
    "build_user_context",
    "classify_message",
    "create_link_token",
    "decide_and_generate_nudge",
    "exchange_public_token",
    "evaluate_nudge_eligibility",
    "get_or_create_user_by_phone",
    "handle_plaid_webhook",
    "parse_transaction",
    "predict_for_user",
    "process_user_nudges",
    "run_nudge_cycle",
    "save_feedback",
    "save_transaction",
    "send_sms",
    "sync_user_transactions",
    "validate_twilio_request",
]
