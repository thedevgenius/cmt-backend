from app.services.base import BaseService
from app.models.business import Business
from app.schemas.business import BizCreate, BizUpdate


class BizService(BaseService[Business, BizCreate, BizUpdate]):
    pass


biz_service = BizService(Business)