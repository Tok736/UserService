from faststream import FastStream

from src.rabbit import broker
from src.user.router import router as user_router

broker.include_router(user_router)

app = FastStream(broker)
