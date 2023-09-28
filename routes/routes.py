from fastapi import APIRouter
from routes.home_page import router as home_router
from routes.submit_form import router as submit_form_router

router = APIRouter()

router.include_router(home_router, tags=["Home"])
router.include_router(submit_form_router, tags=["Flight Offers"])
