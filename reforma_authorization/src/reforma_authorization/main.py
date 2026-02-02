from fastapi import FastAPI
from contextlib import asynccontextmanager
from reforma_authorization.presentation.api.auth import router as auth_router
from reforma_authorization.presentation.api.user import router as user_router
from reforma_authorization.infrastructure.rabbitmq.publisher import MailPublisher

mail_publisher = MailPublisher()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await mail_publisher.connect()
    yield
    await mail_publisher.close()

app = FastAPI(title="Auth Service", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(user_router)
