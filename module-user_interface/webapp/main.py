from flask import Flask, Blueprint, jsonify, Response, current_app



bp = Blueprint('main', __name__)


@bp.route('/')
def home():
    return jsonify(message="Welcome to the new web app!")

