# openvpn_plugin/models.py
from CTFd.models import db

class OpenVPNProfile(db.Model):
    __tablename__ = "openvpn_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True, nullable=False, unique=True)
    agreed_at = db.Column(db.DateTime, server_default=db.func.now())
    ovpn_base64 = db.Column(db.Text, nullable=False)
