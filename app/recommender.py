import uuid
import redis
from django.conf import settings
from .models import Pic

r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)

class PhotoRecommender:
    def is_valid_uuid(self, val):
        try:
            uuid.UUID(str(val))
            return True
        except ValueError:
            return False

    def photos_viewed(self, photos):
        photo_ids = [p.id for p in photos if self.is_valid_uuid(p.id)]
        # print(f"Photos viewed: {photo_ids}")
        for photo_id in photo_ids:
            for with_id in photo_ids:
                if photo_id != with_id:
                    r.zincrby(self.get_photo_key(photo_id), 1, str(with_id))

    def suggest_photos_for(self, photos, max_results=5):
        photo_ids = [p.id for p in photos if self.is_valid_uuid(p.id)]
        if len(photo_ids) == 1:
            suggestions = r.zrange(self.get_photo_key(photo_ids[0]), 0, -1, desc=True)[:max_results]
        else:
            temp_key = f'tmp:{"".join(str(id) for id in photo_ids)}'
            keys = [self.get_photo_key(id) for id in photo_ids]
            r.zunionstore(temp_key, keys)
            r.zrem(temp_key, *photo_ids)
            suggestions = r.zrange(temp_key, 0, -1, desc=True)[:max_results]
            r.delete(temp_key)

        suggested_photo_ids = [
            uuid.UUID(id.decode('utf-8')) for id in suggestions if self.is_valid_uuid(id.decode('utf-8'))
        ]
        suggested_photos = list(Pic.objects.filter(id__in=suggested_photo_ids))
        suggested_photos.sort(key=lambda x: suggested_photo_ids.index(x.id))
        return suggested_photos

    def get_photo_key(self, id):
        return f'photo:{id}:viewed_with'
