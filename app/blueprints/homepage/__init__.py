from flask import Blueprint, render_template
from sqlalchemy import func

bp = Blueprint("homepage", __name__)

from app.models import *
import flask_menu as menu
from sqlalchemy.orm import joinedload


@menu.register_menu(bp, ".", "Home")
@bp.route("/")
def home():
	def join(query):
		return query.options(
				joinedload(Package.license),
				joinedload(Package.media_license))

	query   = Package.query.filter_by(state=PackageState.APPROVED)
	count   = query.count()

	new     = join(query.order_by(db.desc(Package.approved_at))).limit(4).all()
	pop_mod = join(query.filter_by(type=PackageType.MOD).order_by(db.desc(Package.score))).limit(8).all()
	pop_gam = join(query.filter_by(type=PackageType.GAME).order_by(db.desc(Package.score))).limit(8).all()
	pop_txp = join(query.filter_by(type=PackageType.TXP).order_by(db.desc(Package.score))).limit(8).all()
	high_reviewed = join(query.order_by(db.desc(Package.score - Package.score_downloads))) \
			.filter(Package.reviews.any()).limit(4).all()

	updated = db.session.query(Package).select_from(PackageRelease).join(Package) \
			.filter_by(state=PackageState.APPROVED) \
			.order_by(db.desc(PackageRelease.releaseDate)) \
			.limit(20).all()
	updated = updated[:4]

	reviews = PackageReview.query.filter_by(recommends=True).order_by(db.desc(PackageReview.created_at)).limit(5).all()

	downloads_result = db.session.query(func.sum(Package.downloads)).one_or_none()
	downloads = 0 if not downloads_result or not downloads_result[0] else downloads_result[0]

	tags = db.session.query(func.count(Tags.c.tag_id), Tag) \
		.select_from(Tag).outerjoin(Tags).group_by(Tag.id).order_by(db.asc(Tag.title)).all()

	return render_template("index.html", count=count, downloads=downloads, tags=tags,
			new=new, updated=updated, pop_mod=pop_mod, pop_txp=pop_txp, pop_gam=pop_gam, high_reviewed=high_reviewed, reviews=reviews)


@menu.register_menu(bp, ".mods", "Mods", order=11, endpoint_arguments_constructor=lambda: { 'type': 'mod' })
@menu.register_menu(bp, ".games", "Games", order=12, endpoint_arguments_constructor=lambda: { 'type': 'game' })
@menu.register_menu(bp, ".txp", "Texture Packs", order=13, endpoint_arguments_constructor=lambda: { 'type': 'txp' })
@bp.route("/games/", defaults={ "type": "GAME" })
@bp.route("/mods/", defaults={ "type": "MOD" })
@bp.route("/texture_packs/", defaults={ "type": "TXP" })
def type_page(type_name):
	return type_name
