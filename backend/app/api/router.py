from fastapi import APIRouter

from app.api.contracts import COMMON_ERROR_RESPONSES
from app.modules.classification.router import router as classification_router
from app.modules.consultation.router import router as consultation_router
from app.modules.historical_qa.router import router as historical_qa_router
from app.modules.iam.router import router as iam_router
from app.modules.policy.router import router as policy_router
from app.modules.policy_qa.router import router as policy_qa_router
from app.modules.system.router import router as system_router

api_router = APIRouter(responses=COMMON_ERROR_RESPONSES)
api_router.include_router(system_router)
api_router.include_router(iam_router)
api_router.include_router(policy_router)
api_router.include_router(historical_qa_router)
api_router.include_router(classification_router)
api_router.include_router(policy_qa_router)
api_router.include_router(consultation_router)
