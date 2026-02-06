#!/usr/bin/env python3

from flask import Flask, request, session
from flask_migrate import Migrate
from flask_restful import Api, Resource
from pathlib import Path

from models import db, Article, User, ArticlesSchema, UserSchema

app = Flask(__name__)
app.secret_key = b"super-secret-key"

BASE_DIR = Path(__file__).resolve().parent
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'app.db'}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)

article_schema = ArticlesSchema()
user_schema = UserSchema()


class ClearSession(Resource):
    def get(self):
        session.pop("page_views", None)
        session.pop("user_id", None)
        return {}, 204


class Articles(Resource):
    def get(self):
        articles = Article.query.all()
        return [article_schema.dump(a) for a in articles], 200


class ArticleByID(Resource):
    def get(self, id):
        page_views = session.get("page_views", 0) + 1
        session["page_views"] = page_views

        if page_views > 3:
            return {"message": "Maximum pageview limit reached"}, 401

        article = Article.query.filter(Article.id == id).first()
        if not article:
            return {"error": "Article not found"}, 404

        return article_schema.dump(article), 200


class Login(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        username = (data.get("username") or data.get("name") or "").strip()

        user = User.query.filter(User.username == username).first()
        if not user:
            return {}, 401

        session["user_id"] = user.id
        return user_schema.dump(user), 200


class Logout(Resource):
    def delete(self):
        session.pop("user_id", None)
        return {}, 204


class CheckSession(Resource):
    def get(self):
        user_id = session.get("user_id")

        if user_id:
            user = db.session.get(User, user_id)
            if user:
                return user_schema.dump(user), 200

        return {}, 401


api.add_resource(ClearSession, "/clear")
api.add_resource(Articles, "/articles")
api.add_resource(ArticleByID, "/articles/<int:id>")
api.add_resource(Login, "/login")
api.add_resource(Logout, "/logout")
api.add_resource(CheckSession, "/check_session")


if __name__ == "__main__":
    app.run(port=5555, debug=True)
