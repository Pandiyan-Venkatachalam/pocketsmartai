import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user_optional
from app.models.user import User
from app.services.recommendation_service import recommendation_service

router = APIRouter(include_in_schema=False)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

def _login_redirect_if_needed(user: Optional[User]):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return None

@router.get("/", response_class=HTMLResponse)
def index(request: Request, current_user: Optional[User] = Depends(get_current_user_optional)):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"user": current_user, "app_name": settings.APP_NAME}
    )

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, current_user: Optional[User] = Depends(get_current_user_optional)):
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="login.html", context={"user": None})

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, current_user: Optional[User] = Depends(get_current_user_optional)):
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="register.html", context={"user": None})

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    redirect = _login_redirect_if_needed(current_user)
    if redirect:
        return redirect

    stats = recommendation_service.get_dashboard_stats(db=db, user=current_user)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"user": current_user, "stats": stats}
    )

@router.get("/planners/home", response_class=HTMLResponse)
def home_planner_page(request: Request, current_user: Optional[User] = Depends(get_current_user_optional)):
    redirect = _login_redirect_if_needed(current_user)
    if redirect:
        return redirect
    return templates.TemplateResponse(request=request, name="home_planner.html", context={"user": current_user})

@router.get("/planners/party", response_class=HTMLResponse)
def party_planner_page(request: Request, current_user: Optional[User] = Depends(get_current_user_optional)):
    redirect = _login_redirect_if_needed(current_user)
    if redirect:
        return redirect
    return templates.TemplateResponse(request=request, name="party_planner.html", context={"user": current_user})

@router.get("/planners/jewelry", response_class=HTMLResponse)
def jewelry_planner_page(request: Request, current_user: Optional[User] = Depends(get_current_user_optional)):
    redirect = _login_redirect_if_needed(current_user)
    if redirect:
        return redirect
    return templates.TemplateResponse(request=request, name="jewelry_planner.html", context={"user": current_user})

@router.get("/planners/custom", response_class=HTMLResponse)
def custom_planner_page(request: Request, current_user: Optional[User] = Depends(get_current_user_optional)):
    redirect = _login_redirect_if_needed(current_user)
    if redirect:
        return redirect
    return templates.TemplateResponse(request=request, name="custom_planner.html", context={"user": current_user})

@router.get("/recommendations/{rec_id}", response_class=HTMLResponse)
def recommendation_results_page(
    rec_id: int,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    redirect = _login_redirect_if_needed(current_user)
    if redirect:
        return redirect

    rec = recommendation_service.get_recommendation_by_id(db=db, rec_id=rec_id, user_id=current_user.id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    try:
        inputs = json.loads(rec.input_data)
    except Exception:
        inputs = {}

    try:
        plan_data = json.loads(rec.plan_data) if rec.plan_data else {}
    except Exception:
        plan_data = {}

    return templates.TemplateResponse(
        request=request,
        name="recommendations.html",
        context={
            "user": current_user,
            "recommendation": rec,
            "inputs": inputs,
            "plan_data": plan_data,
            "items": rec.items
        }
    )

@router.get("/history", response_class=HTMLResponse)
def history_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    redirect = _login_redirect_if_needed(current_user)
    if redirect:
        return redirect

    history_items = recommendation_service.get_user_history(db=db, user_id=current_user.id, limit=50)
    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={"user": current_user, "history": history_items}
    )
