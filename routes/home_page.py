from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def home_page(request: Request):
    """
    Render the home page template.

    :param request: The FastAPI request object.
    :return: A TemplateResponse containing the rendered home page template.
    """

    return templates.TemplateResponse("home_page.html", {"request": request})
