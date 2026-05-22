from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from config import Config
from datetime import datetime
import bcrypt


# =======================
# MongoDB Connection
# =======================

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None
        self.connected = False
        
        # Try primary URI from Config first, then fallback to local MongoDB if available
        uris_to_try = [Config.MONGO_URI, 'mongodb://127.0.0.1:27017']
        last_error = None
        for uri in uris_to_try:
            try:
                # Use TLS options only for SRV/Atlas URIs
                if uri.startswith('mongodb+srv://'):
                    self.client = MongoClient(
                        uri,
                        tls=True,
                        tlsAllowInvalidCertificates=True,
                        tlsAllowInvalidHostnames=True,
                        serverSelectionTimeoutMS=15000,
                        connectTimeoutMS=15000,
                        socketTimeoutMS=15000,
                        retryWrites=True,
                        w='majority',
                        readPreference='primary'
                    )
                else:
                    # Local/standard MongoDB URI (no TLS)
                    self.client = MongoClient(
                        uri,
                        serverSelectionTimeoutMS=8000,
                        connectTimeoutMS=8000,
                        socketTimeoutMS=8000
                    )
                
                self._verify_connection()
                self.db = self.client[Config.MONGO_DB_NAME]
                self.connected = True
                print(f"MongoDB connected successfully to: {uri} - Database persistence enabled")
                break
            except (ServerSelectionTimeoutError, Exception) as e:
                last_error = e
                print(f"MongoDB connection attempt failed for URI: {uri}")
                continue
        
        if not self.connected:
            print("MongoDB connection failed - Using in-memory storage")
            if last_error:
                print(f"Connection error: {str(last_error)}")
            print("Note: Data will be lost when server restarts")
            self.connected = False

    def _verify_connection(self):
        try:
            self.client.admin.command("ping")
        except ServerSelectionTimeoutError as e:
            raise RuntimeError("MongoDB connection failed") from e

    def get_db(self):
        return self.db
    
    def is_connected(self):
        return self.connected


# =======================
# Initialize Database
# =======================

mongo = MongoDB()
db = mongo.get_db()

print("Database initialized successfully")


# =======================
# Collections (MongoDB or In-Memory)
# =======================

if mongo.is_connected():
    # MongoDB collections
    users_collection = db.users
    images_collection = db.user_images
    analyses_collection = db.analyses
    recommendations_collection = db.recommendations
    contact_messages_collection = db.contact_messages
    print("Using MongoDB collections")
else:
    # In-memory collections (fallback)
    users_collection = []
    images_collection = []
    analyses_collection = []
    recommendations_collection = []
    contact_messages_collection = []

    # Simple in-memory ID counters
    _image_id_counter = 1
    _analysis_id_counter = 1
    _recommendation_id_counter = 1

    print("Using in-memory collections")


# =======================
# Indexes
# =======================

def create_indexes():
    if mongo.is_connected():
        try:
            users_collection.create_index("email", unique=True)
            images_collection.create_index([("user_id", 1), ("uploaded_at", -1)])
            analyses_collection.create_index([("user_id", 1), ("created_at", -1)])
            recommendations_collection.create_index([("user_id", 1), ("created_at", -1)])
            contact_messages_collection.create_index([("created_at", -1)])
            print("MongoDB indexes created successfully")
        except Exception as e:
            print(f"Warning: Could not create MongoDB indexes: {e}")
    else:
        print("Skipping index creation (in-memory mode)")


create_indexes()


# =======================
# Helper functions (In-Memory)
# =======================

def _mem_find_by_id(collection_list, id_value):
    for item in collection_list:
        if item.get('id') == id_value:
            return item
    return None


def _mem_delete_by_id(collection_list, id_value):
    idx = next((i for i, item in enumerate(collection_list) if item.get('id') == id_value), None)
    if idx is not None:
        collection_list.pop(idx)
        return True
    return False


def _mem_update_by_id(collection_list, id_value, updates):
    item = _mem_find_by_id(collection_list, id_value)
    if item:
        item.update(updates)
        item['updated_at'] = datetime.utcnow()
        return item
    return None


def _mem_find_by_user(collection_list, user_id):
    return [item for item in collection_list if item.get('user_id') == user_id]


# =======================
# Models
# =======================

class User:
    def __init__(self, data):
        self.id = str(data.get("_id", data.get("id", "")))
        self.email = data.get("email", "")
        self.password_hash = data.get("password_hash", "")
        self.first_name = data.get("first_name", "")
        self.last_name = data.get("last_name", "")
        self.created_at = data.get("created_at", datetime.utcnow())
        self.updated_at = data.get("updated_at", datetime.utcnow())

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    def save(self):
        if mongo.is_connected():
            from bson import ObjectId

            data = {
                "email": self.email,
                "password_hash": self.password_hash,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "updated_at": datetime.utcnow()
            }

            if self.id:
                users_collection.update_one(
                    {"_id": ObjectId(self.id)}, {"$set": data}
                )
            else:
                data["created_at"] = datetime.utcnow()
                result = users_collection.insert_one(data)
                self.id = str(result.inserted_id)
        else:
            # In-memory storage
            existing = next((u for u in users_collection if u.get('email') == self.email), None)
            if existing:
                existing.update({
                    "password_hash": self.password_hash,
                    "first_name": self.first_name,
                    "last_name": self.last_name,
                    "updated_at": datetime.utcnow()
                })
                self.id = existing.get('id')
            else:
                new_id = str(len(users_collection) + 1)
                data = {
                    "id": new_id,
                    "email": self.email,
                    "password_hash": self.password_hash,
                    "first_name": self.first_name,
                    "last_name": self.last_name,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                users_collection.append(data)
                self.id = new_id

        return self

    @staticmethod
    def find_by_email(email):
        if mongo.is_connected():
            data = users_collection.find_one({"email": email})
            return User(data) if data else None
        else:
            data = next((u for u in users_collection if u.get('email') == email), None)
            return User(data) if data else None

    @staticmethod
    def find_by_id(user_id):
        if mongo.is_connected():
            from bson import ObjectId
            try:
                data = users_collection.find_one({"_id": ObjectId(user_id)})
                return User(data) if data else None
            except Exception:
                return None
        else:
            data = next((u for u in users_collection if u.get('id') == str(user_id)), None)
            return User(data) if data else None

    @staticmethod
    def delete_by_id(user_id):
        if mongo.is_connected():
            from bson import ObjectId
            try:
                users_collection.delete_one({"_id": ObjectId(user_id)})
                return True
            except Exception:
                return False
        else:
            idx = next((i for i, u in enumerate(users_collection) if u.get('id') == str(user_id)), None)
            if idx is not None:
                users_collection.pop(idx)
                return True
            return False

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'created_at': (self.created_at.isoformat() + 'Z') if hasattr(self.created_at, 'isoformat') else str(self.created_at)
        }


class UserImage:
    def __init__(self, data):
        # For Mongo, _id is ObjectId; for in-memory, id is int
        self.id = data.get("id") if isinstance(data.get("id"), int) else None
        if self.id is None and data.get("_id") is not None:
            self.id = int(str(data.get("_id"))[-6:], 16)  # pseudo numeric id for display
        self.user_id = data.get("user_id", "")
        self.filename = data.get("filename", "")
        self.file_path = data.get("file_path", "")
        self.uploaded_at = data.get("uploaded_at", datetime.utcnow())

    def save(self):
        global _image_id_counter
        if mongo.is_connected():
            payload = {
                "user_id": self.user_id,
                "filename": self.filename,
                "file_path": self.file_path,
                "uploaded_at": self.uploaded_at
            }
            result = images_collection.insert_one(payload)
            self.id = int(str(result.inserted_id)[-6:], 16)
            # Store the pseudo numeric id back so find_by_id can look it up
            images_collection.update_one(
                {"_id": result.inserted_id},
                {"$set": {"id": self.id}}
            )
        else:
            self.id = _image_id_counter
            _image_id_counter += 1
            images_collection.append({
                "id": self.id,
                "user_id": self.user_id,
                "filename": self.filename,
                "file_path": self.file_path,
                "uploaded_at": self.uploaded_at
            })
        return self

    @staticmethod
    def find_by_id(image_id):
        if mongo.is_connected():
            # We store numeric surrogate id for responses; actual lookup is by file_path/metadata not needed here.
            # For simplicity, we cannot reverse map numeric to ObjectId here; prefer in-memory functionality for dev.
            # In production, routes should use ObjectId string.
            doc = images_collection.find_one({"id": image_id})
            return UserImage(doc) if doc else None
        else:
            data = _mem_find_by_id(images_collection, image_id)
            return UserImage(data) if data else None

    @staticmethod
    def find_by_user(user_id, page=1, per_page=10):
        if mongo.is_connected():
            cursor = images_collection.find({"user_id": user_id}).sort("uploaded_at", -1).skip((page-1)*per_page).limit(per_page)
            return [UserImage(doc) for doc in cursor]
        else:
            items = _mem_find_by_user(images_collection, user_id)
            items.sort(key=lambda x: x.get('uploaded_at') or datetime.min, reverse=True)
            start, end = (page - 1) * per_page, (page - 1) * per_page + per_page
            return [UserImage(item) for item in items[start:end]]

    @staticmethod
    def count_by_user(user_id):
        if mongo.is_connected():
            return images_collection.count_documents({"user_id": user_id})
        else:
            return len(_mem_find_by_user(images_collection, user_id))

    @staticmethod
    def delete_by_id(image_id):
        if mongo.is_connected():
            images_collection.delete_one({"id": image_id})
        else:
            _mem_delete_by_id(images_collection, image_id)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'uploaded_at': (self.uploaded_at.isoformat() + 'Z') if hasattr(self.uploaded_at, 'isoformat') else str(self.uploaded_at)
        }


class Analysis:
    def __init__(self, data):
        self.id = data.get("id") if isinstance(data.get("id"), int) else None
        if self.id is None and data.get("_id") is not None:
            self.id = int(str(data.get("_id"))[-6:], 16)
        self.user_id = data.get("user_id", "")
        self.image_id = data.get("image_id", 0)
        self.skin_tone = data.get("skin_tone")
        self.body_shape = data.get("body_shape")
        self.style_personality = data.get("style_personality")
        self.confidence_score = data.get("confidence_score")
        self.color_palette = data.get("color_palette", [])
        self.face_shape = data.get("face_shape")
        self.height_estimate = data.get("height_estimate")
        self.body_measurements = data.get("body_measurements", {})
        self.detected_gender = data.get("detected_gender")
        self.gender_confidence = data.get("gender_confidence")
        self.created_at = data.get("created_at", datetime.utcnow())
        self.updated_at = data.get("updated_at", datetime.utcnow())

    def save(self):
        global _analysis_id_counter
        payload = {
            "user_id": self.user_id,
            "image_id": self.image_id,
            "skin_tone": self.skin_tone,
            "body_shape": self.body_shape,
            "style_personality": self.style_personality,
            "confidence_score": self.confidence_score,
            "color_palette": self.color_palette,
            "face_shape": self.face_shape,
            "height_estimate": self.height_estimate,
            "body_measurements": self.body_measurements,
            "detected_gender": self.detected_gender,
            "gender_confidence": self.gender_confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        if mongo.is_connected():
            result = analyses_collection.insert_one(payload)
            self.id = int(str(result.inserted_id)[-6:], 16)
        else:
            self.id = _analysis_id_counter
            _analysis_id_counter += 1
            payload["id"] = self.id
            analyses_collection.append(payload)
        return self

    @staticmethod
    def find_by_id(analysis_id):
        if mongo.is_connected():
            doc = analyses_collection.find_one({"id": analysis_id})
            return Analysis(doc) if doc else None
        else:
            data = _mem_find_by_id(analyses_collection, analysis_id)
            return Analysis(data) if data else None

    @staticmethod
    def find_by_user(user_id, page=1, per_page=10):
        if mongo.is_connected():
            cursor = analyses_collection.find({"user_id": user_id}).sort("created_at", -1).skip((page-1)*per_page).limit(per_page)
            return [Analysis(doc) for doc in cursor]
        else:
            items = _mem_find_by_user(analyses_collection, user_id)
            items.sort(key=lambda x: x.get('created_at') or datetime.min, reverse=True)
            start, end = (page - 1) * per_page, (page - 1) * per_page + per_page
            return [Analysis(item) for item in items[start:end]]

    @staticmethod
    def count_by_user(user_id):
        if mongo.is_connected():
            return analyses_collection.count_documents({"user_id": user_id})
        else:
            return len(_mem_find_by_user(analyses_collection, user_id))

    @staticmethod
    def find_by_image(image_id):
        if mongo.is_connected():
            doc = analyses_collection.find_one({"image_id": image_id})
            return Analysis(doc) if doc else None
        else:
            data = next((a for a in analyses_collection if a.get('image_id') == image_id), None)
            return Analysis(data) if data else None

    @staticmethod
    def update_by_id(analysis_id, updates):
        if mongo.is_connected():
            updates['updated_at'] = datetime.utcnow()
            analyses_collection.update_one({"id": analysis_id}, {"$set": updates})
        else:
            _mem_update_by_id(analyses_collection, analysis_id, updates)

    @staticmethod
    def delete_by_id(analysis_id):
        if mongo.is_connected():
            analyses_collection.delete_one({"id": analysis_id})
        else:
            _mem_delete_by_id(analyses_collection, analysis_id)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'image_id': self.image_id,
            'skin_tone': self.skin_tone,
            'body_shape': self.body_shape,
            'style_personality': self.style_personality,
            'confidence_score': self.confidence_score,
            'color_palette': self.color_palette,
            'face_shape': self.face_shape,
            'height_estimate': self.height_estimate,
            'body_measurements': self.body_measurements,
            'detected_gender': self.detected_gender,
            'gender_confidence': self.gender_confidence,
            'created_at': (self.created_at.isoformat() + 'Z') if hasattr(self.created_at, 'isoformat') else str(self.created_at)
        }


class Recommendation:
    def __init__(self, data):
        self.id = data.get("id") if isinstance(data.get("id"), int) else None
        if self.id is None and data.get("_id") is not None:
            self.id = int(str(data.get("_id"))[-6:], 16)
        self.user_id = data.get("user_id", "")
        self.analysis_id = data.get("analysis_id", 0)
        self.category = data.get("category")
        self.title = data.get("title", "")
        self.description = data.get("description")
        self.recommendation_type = data.get("recommendation_type")
        self.tags = data.get("tags", [])
        self.priority = data.get("priority", 1)
        self.seasonal_relevance = data.get("seasonal_relevance", 'all')
        self.created_at = data.get("created_at", datetime.utcnow())
        self.updated_at = data.get("updated_at", datetime.utcnow())

    def save(self):
        global _recommendation_id_counter
        payload = {
            "user_id": self.user_id,
            "analysis_id": self.analysis_id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "recommendation_type": self.recommendation_type,
            "tags": self.tags,
            "priority": self.priority,
            "seasonal_relevance": self.seasonal_relevance,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        if mongo.is_connected():
            result = recommendations_collection.insert_one(payload)
            self.id = int(str(result.inserted_id)[-6:], 16)
        else:
            self.id = _recommendation_id_counter
            _recommendation_id_counter += 1
            payload["id"] = self.id
            recommendations_collection.append(payload)
        return self

    @staticmethod
    def find_by_id(recommendation_id):
        if mongo.is_connected():
            doc = recommendations_collection.find_one({"id": recommendation_id})
            return Recommendation(doc) if doc else None
        else:
            data = _mem_find_by_id(recommendations_collection, recommendation_id)
            return Recommendation(data) if data else None

    @staticmethod
    def find_by_user(user_id, page=1, per_page=10, filters=None):
        filters = filters or {}
        if mongo.is_connected():
            query = {"user_id": user_id}
            query.update(filters)
            cursor = recommendations_collection.find(query).sort("created_at", -1).skip((page-1)*per_page).limit(per_page)
            return [Recommendation(doc) for doc in cursor]
        else:
            items = _mem_find_by_user(recommendations_collection, user_id)
            # Apply filters
            for k, v in filters.items():
                items = [item for item in items if item.get(k) == v]
            items.sort(key=lambda x: x.get('created_at') or datetime.min, reverse=True)
            start, end = (page - 1) * per_page, (page - 1) * per_page + per_page
            return [Recommendation(item) for item in items[start:end]]

    @staticmethod
    def count_by_user(user_id, filters=None):
        filters = filters or {}
        if mongo.is_connected():
            query = {"user_id": user_id}
            query.update(filters)
            return recommendations_collection.count_documents(query)
        else:
            items = _mem_find_by_user(recommendations_collection, user_id)
            for k, v in filters.items():
                items = [item for item in items if item.get(k) == v]
            return len(items)

    @staticmethod
    def find_by_analysis(analysis_id):
        if mongo.is_connected():
            cursor = recommendations_collection.find({"analysis_id": analysis_id}).sort("created_at", -1)
            return [Recommendation(doc) for doc in cursor]
        else:
            items = [item for item in recommendations_collection if item.get('analysis_id') == analysis_id]
            items.sort(key=lambda x: x.get('created_at') or datetime.min, reverse=True)
            return [Recommendation(item) for item in items]

    @staticmethod
    def update_by_id(recommendation_id, updates):
        if mongo.is_connected():
            updates['updated_at'] = datetime.utcnow()
            recommendations_collection.update_one({"id": recommendation_id}, {"$set": updates})
        else:
            _mem_update_by_id(recommendations_collection, recommendation_id, updates)

    @staticmethod
    def delete_by_id(recommendation_id):
        if mongo.is_connected():
            recommendations_collection.delete_one({"id": recommendation_id})
        else:
            _mem_delete_by_id(recommendations_collection, recommendation_id)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'analysis_id': self.analysis_id,
            'category': self.category,
            'title': self.title,
            'description': self.description,
            'recommendation_type': self.recommendation_type,
            'tags': self.tags,
            'priority': self.priority,
            'seasonal_relevance': self.seasonal_relevance,
            'created_at': (self.created_at.isoformat() + 'Z') if hasattr(self.created_at, 'isoformat') else str(self.created_at)
        }
