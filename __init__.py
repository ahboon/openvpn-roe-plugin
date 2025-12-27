from flask import Blueprint, render_template, jsonify, request
from CTFd.utils.decorators import authed_only
from CTFd.utils.user import get_current_user
from CTFd.models import db
import requests

from .models import OpenVPNProfile

BACKEND_URL = "ip_address:5000"
PRE_SHARED_KEY = "REPLACE_WITH_SHARED_KEY"
def load(app):
    app.db.create_all()

    bp = Blueprint("openvpn", __name__, template_folder="templates")

    @bp.route("/openvpn")
    @authed_only
    def openvpn_page():
        return render_template("openvpn.html")

    @bp.route("/api/openvpn/create", methods=["POST"])
    @authed_only
    def create_openvpn():
        user = get_current_user()

        existing = OpenVPNProfile.query.filter_by(user_id=user.id).first()
        if existing:
            return jsonify({"status": "ok", "message": "Returning stored profile", "ovpn_base64": existing.ovpn_base64})

        # create via backend
        r = requests.get(
            f"http://{BACKEND_URL}/create",
            params={"client": user.id},
            headers={"X-Pre-Shared-Key": PRE_SHARED_KEY},
            timeout=10,
        )
        if r.status_code != 200:
            return jsonify({"status": "error", "error": r.text}), r.status_code

        data = r.json()
        ovpn_b64 = data.get("ovpn_base64")
        if not ovpn_b64:
            return jsonify({"status": "error", "error": "No profile returned"}), 500

        rec = OpenVPNProfile(user_id=user.id, ovpn_base64=ovpn_b64)
        db.session.add(rec)
        db.session.commit()

        return jsonify({"status": "ok", "message": "Profile created and stored", "ovpn_base64": ovpn_b64})

    @bp.route("/api/openvpn/delete", methods=["POST"])
    @authed_only
    def delete_openvpn():
        user = get_current_user()

        # call backend revoke
        r = requests.post(
            f"http://{BACKEND_URL}/delete",
            json={"client": str(user.id)},
            headers={"X-Pre-Shared-Key": PRE_SHARED_KEY},
            timeout=10,
        )

        if r.status_code != 200:
            return jsonify({"error": r.json().get("error", "Unknown error")}), r.status_code

        OpenVPNProfile.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        return jsonify({"message": f"Profile for user {user.id} deleted."})

    @bp.route("/api/openvpn/current", methods=["GET"])
    @authed_only
    def get_current_openvpn():
        user = get_current_user()
        existing = OpenVPNProfile.query.filter_by(user_id=user.id).first()
        if not existing:
            return jsonify({"status": "empty"})
        return jsonify({
            "status": "ok",
            "ovpn_base64": existing.ovpn_base64,
            "agreed_at": existing.agreed_at.isoformat()
        })
        
    app.register_blueprint(bp)
