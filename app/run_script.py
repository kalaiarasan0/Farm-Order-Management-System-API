from app.db import tracking_engine
from app.models.tracking_tables import TrackingBase

TrackingBase.metadata.create_all(bind=tracking_engine)
