"""Admin router — prefix /admin, all routes require superuser."""

from fastapi import APIRouter, Depends

from app.deps import get_current_superuser
from app.routers.admin.content import router as content_router
from app.routers.admin.users import router as users_router
from app.routers.admin.payments import router as payments_router
from app.routers.admin.uploads import router as uploads_router
from app.routers.admin.packages import router as packages_router
from app.routers.admin.products import router as products_router
from app.routers.admin.orders import router as orders_router
from app.routers.admin.dashboard import router as dashboard_router
from app.routers.admin.webhook_events import router as webhook_events_router
from app.routers.admin.banks import router as banks_router
from app.routers.admin.chatbot import router as chatbot_router
from app.routers.admin.news import router as news_router

admin_router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(get_current_superuser)],
)

admin_router.include_router(content_router)
admin_router.include_router(users_router)
admin_router.include_router(payments_router)
admin_router.include_router(uploads_router)
admin_router.include_router(packages_router)
admin_router.include_router(products_router)
admin_router.include_router(orders_router)
admin_router.include_router(dashboard_router)
admin_router.include_router(webhook_events_router)
admin_router.include_router(banks_router)
admin_router.include_router(news_router)
admin_router.include_router(chatbot_router)
