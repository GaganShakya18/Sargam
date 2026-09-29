import uuid

from sqlalchemy import func

from models.history import ListeningHistory, SearchHistory, UserPreference, UserPrivacy, UserSession
from models.user import User


class UserRepository:
    def __init__(self, database_session):
        self.db = database_session

    @staticmethod
    def normalize_email(email: str | None) -> str | None:
        if email is None:
            return None
        return email.strip().lower()

    @staticmethod
    def normalize_username(username: str | None) -> str | None:
        if username is None:
            return None
        return username.strip().lower()

    def get_by_email(self, email: str):
        normalized_email = self.normalize_email(email)
        if not normalized_email:
            return None
        return self.db.query(User).filter(func.lower(User.email) == normalized_email).first()

    def get_by_username(self, username: str):
        normalized_username = self.normalize_username(username)
        if not normalized_username:
            return None
        return self.db.query(User).filter(func.lower(User.username) == normalized_username).first()

    def create(self, payload: dict):
        raw_password = payload.get("password") or payload.get("password_hash")
        if not raw_password:
            raise ValueError("A password or password_hash is required")

        email = self.normalize_email(payload["email"])
        username = self.normalize_username(payload["username"])
        if not email or not username:
            raise ValueError("Email and username are required")

        full_name = payload.get("full_name")
        if full_name is not None:
            full_name = full_name.strip()
            if not full_name:
                full_name = None

        bio = payload.get("bio")
        if bio is not None:
            bio = bio.strip()
            if not bio:
                bio = None

        password_hash = payload.get("password_hash")
        if password_hash and password_hash.startswith("$2b$"):
            stored_hash = password_hash
        else:
            stored_hash = payload.get("password_hash") or raw_password
            if not stored_hash.startswith("$2b$"):
                from utils.hashing import hash_password

                stored_hash = hash_password(stored_hash)

        user = User(
            id=payload.get("id") or str(uuid.uuid4()),
            email=email,
            username=username,
            password_hash=stored_hash,
            full_name=full_name,
            bio=bio,
            profile_image=payload.get("profile_image"),
            account_type=payload.get("account_type", "Free"),
            is_active=payload.get("is_active", True),
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        self._ensure_preferences(user.email)
        self._ensure_privacy(user.email)
        return user

    def update_password(self, email: str, new_password: str):
        if not new_password or not new_password.strip():
            raise ValueError("A new password is required")

        user = self.get_by_email(email)
        if not user:
            raise ValueError("User not found")

        from utils.hashing import hash_password

        user.password_hash = hash_password(new_password)
        self.db.commit()
        self.db.refresh(user)
        return user

    def change_password(self, email: str, current_password: str, new_password: str):
        if not new_password or not new_password.strip():
            raise ValueError("A new password is required")

        user = self.get_by_email(email)
        if not user:
            raise ValueError("User not found")

        from utils.hashing import verify_password, hash_password

        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        user.password_hash = hash_password(new_password)
        self.db.commit()
        self.db.refresh(user)
        return True

    def update_profile(self, email: str, payload: dict):
        user = self.get_by_email(email)
        if not user:
            raise ValueError("User not found")

        if "email" in payload and payload["email"] is not None:
            normalized_email = self.normalize_email(payload["email"])
            if not normalized_email:
                raise ValueError("Email is required")
            user.email = normalized_email

        if "username" in payload and payload["username"] is not None:
            normalized_username = self.normalize_username(payload["username"])
            if not normalized_username:
                raise ValueError("Username is required")
            if normalized_username != user.username:
                existing = self.get_by_username(normalized_username)
                if existing and existing.id != user.id:
                    raise ValueError("Username already taken")
            user.username = normalized_username

        if "full_name" in payload and payload["full_name"] is not None:
            full_name = payload["full_name"].strip()
            user.full_name = full_name or None

        if "bio" in payload and payload["bio"] is not None:
            bio = payload["bio"].strip()
            user.bio = bio or None

        if "profile_image" in payload and payload["profile_image"] is not None:
            profile_image = payload["profile_image"].strip()
            user.profile_image = profile_image or None

        if "account_type" in payload and payload["account_type"] is not None:
            user.account_type = payload["account_type"].strip() or "Free"

        self.db.commit()
        self.db.refresh(user)
        return user

    def _ensure_preferences(self, email: str):
        user = self.get_by_email(email)
        if not user:
            return None
        preference = self.db.query(UserPreference).filter_by(user_id=user.id).first()
        if preference is None:
            preference = UserPreference(
                id=str(uuid.uuid4()),
                user_id=user.id,
                audio_quality='standard',
                streaming_quality='standard',
                autoplay=True,
                crossfade=0,
                explicit_content=True,
                downloads_enabled=False,
                theme='midnight-violet',
                dark_mode=True,
            )
            self.db.add(preference)
            self.db.commit()
        return preference

    def get_preferences(self, email: str):
        user = self.get_by_email(email)
        if not user:
            raise ValueError("User not found")
        preference = self.db.query(UserPreference).filter_by(user_id=user.id).first()
        return self._ensure_preferences(email) if preference is None else preference

    def save_preferences(self, email: str, payload: dict):
        preference = self.get_preferences(email)
        for field in [
            "audio_quality",
            "streaming_quality",
            "autoplay",
            "crossfade",
            "explicit_content",
            "downloads_enabled",
            "theme",
            "dark_mode",
        ]:
            if field in payload and payload[field] is not None:
                setattr(preference, field, payload[field])
        self.db.commit()
        self.db.refresh(preference)
        return preference

    def _ensure_privacy(self, email: str):
        user = self.get_by_email(email)
        if not user:
            return None
        privacy = self.db.query(UserPrivacy).filter_by(user_id=user.id).first()
        if privacy is None:
            privacy = UserPrivacy(
                id=str(uuid.uuid4()),
                user_id=user.id,
                listening_history_enabled=True,
                search_history_enabled=True,
                profile_visible=True,
                account_visibility='friends',
            )
            self.db.add(privacy)
            self.db.commit()
        return privacy

    def get_privacy(self, email: str):
        user = self.get_by_email(email)
        if not user:
            raise ValueError("User not found")
        privacy = self.db.query(UserPrivacy).filter_by(user_id=user.id).first()
        return self._ensure_privacy(email) if privacy is None else privacy

    def save_privacy(self, email: str, payload: dict):
        privacy = self.get_privacy(email)
        for field in [
            "listening_history_enabled",
            "search_history_enabled",
            "profile_visible",
            "account_visibility",
        ]:
            if field in payload and payload[field] is not None:
                setattr(privacy, field, payload[field])
        self.db.commit()
        self.db.refresh(privacy)
        return privacy

    def delete_listening_history(self, email: str):
        user = self.get_by_email(email)
        if not user:
            raise ValueError("User not found")
        deleted = self.db.query(ListeningHistory).filter_by(user_id=user.id).delete()
        self.db.commit()
        return deleted

    def delete_search_history(self, email: str):
        user = self.get_by_email(email)
        if not user:
            raise ValueError("User not found")
        deleted = self.db.query(SearchHistory).filter_by(user_id=user.id).delete()
        self.db.commit()
        return deleted

    def get_sessions(self, email: str):
        user = self.get_by_email(email)
        if not user:
            raise ValueError("User not found")
        return self.db.query(UserSession).filter_by(user_id=user.id).order_by(UserSession.created_at.desc()).all()

    def delete_session(self, email: str, session_id: str):
        user = self.get_by_email(email)
        if not user:
            raise ValueError("User not found")
        session = self.db.query(UserSession).filter_by(id=session_id, user_id=user.id).first()
        if not session:
            raise ValueError("Session not found")
        self.db.delete(session)
        self.db.commit()
        return True

    def create_session(self, email: str, session_id: str, device_name: str | None = None):
        user = self.get_by_email(email)
        if not user:
            raise ValueError("User not found")
        existing = self.db.query(UserSession).filter_by(user_id=user.id, id=session_id).first()
        if existing is None:
            session = UserSession(
                id=session_id,
                user_id=user.id,
                device_name=device_name,
                session_token=session_id,
            )
            self.db.add(session)
            self.db.commit()
        return True
