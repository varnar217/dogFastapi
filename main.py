from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime

# Настройка базы данных
DATABASE_URL = "sqlite:///./test.db"  # Используем SQLite для простоты
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модель заказа
class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, index=True)
    apartment_number = Column(Integer, nullable=False)
    pet_name = Column(String, nullable=False)
    pet_breed = Column(String, nullable=False)
    walk_time = Column(DateTime, nullable=False)

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Создание FastAPI приложения
app = FastAPI()

# Модель для создания заказа
class OrderCreate(BaseModel):
    apartment_number: int
    pet_name: str
    pet_breed: str
    walk_time: datetime

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Эндпоинт для оформления заказа
@app.post("/orders/")
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    # Проверка времени прогулки
    if order.walk_time.hour < 7 or order.walk_time.hour > 23:
        raise HTTPException(status_code=400, detail="Время прогулки должно быть между 7:00 и 23:00")
    
    if order.walk_time.minute not in [0, 30]:
        raise HTTPException(status_code=400, detail="Прогулка может начинаться только в начале часа или в половину")

    # Создание нового заказа
    db_order = Order(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

# Эндпоинт для получения заказов на указанную дату
@app.get("/orders/{date}")
async def read_orders(date: str, db: Session = Depends(get_db)):
    # Преобразование строки в дату
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    start_of_day = date_obj.replace(hour=0, minute=0, second=0)
    end_of_day = date_obj.replace(hour=23, minute=59, second=59)

    orders = db.query(Order).filter(Order.walk_time >= start_of_day, Order.walk_time <= end_of_day).all()
    return orders