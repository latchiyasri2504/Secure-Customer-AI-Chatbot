
from fastapi import FastAPI
from app.routers.customers import router as customers_router
from app.routers.auth import router as auth_router
from app.routers.conversations import router as conversations_router
from app.routers.messages import router as messages_router
from app.routers.invoices import router as invoices_router


app = FastAPI(
    title="Secure Customer AI Chatbot",
    description="Authenticated customer assistant API",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Secure Customer AI Chatbot API is running"
    }


app.include_router(auth_router)
app.include_router(customers_router)
app.include_router(conversations_router)
app.include_router(messages_router)
app.include_router(invoices_router)
