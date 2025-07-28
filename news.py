# news.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import NewsArticle, NewsVote
from sqlalchemy import or_

news_bp = Blueprint('news', __name__)

@news_bp.route('/news')
@login_required
def news_feed():
    """Displays the news feed tailored to the user's level."""
    
    # Get level names from the user's selected streams
    user_level_names = {stream.level.name for stream in current_user.streams}

    level_filter = []
    if 'SSC' in user_level_names:
        level_filter.append(NewsArticle.for_ssc == True)
    if 'HSC' in user_level_names:
        level_filter.append(NewsArticle.for_hsc == True)
    
    if not level_filter:
        articles = []
    else:
        articles = NewsArticle.query.filter(or_(*level_filter)).order_by(NewsArticle.timestamp.desc()).all()

    user_votes = {vote.article_id: vote.vote_type for vote in current_user.news_votes}
    
    return render_template('news.html', articles=articles, user_votes=user_votes)


@news_bp.route('/news/vote/<int:article_id>', methods=['POST'])
@login_required
def vote_on_news(article_id):
    """Handles upvoting and downvoting on a news article."""
    article = NewsArticle.query.get_or_404(article_id)
    vote_type = request.json.get('vote_type')

    if vote_type not in [1, -1]:
        return jsonify({'status': 'error', 'message': 'Invalid vote type.'}), 400

    existing_vote = NewsVote.query.filter_by(user_id=current_user.id, article_id=article.id).first()

    if existing_vote:
        if existing_vote.vote_type == vote_type:
            if vote_type == 1: article.upvotes -= 1
            else: article.downvotes -= 1
            db.session.delete(existing_vote)
        else:
            if vote_type == 1:
                article.upvotes += 1
                article.downvotes -= 1
            else:
                article.downvotes += 1
                article.upvotes -= 1
            existing_vote.vote_type = vote_type
    else:
        if vote_type == 1: article.upvotes += 1
        else: article.downvotes += 1
        new_vote = NewsVote(user_id=current_user.id, article_id=article.id, vote_type=vote_type)
        db.session.add(new_vote)

    db.session.commit()

    return jsonify({
        'status': 'success',
        'upvotes': article.upvotes,
        'downvotes': article.downvotes,
        'user_vote': vote_type if not existing_vote or existing_vote.vote_type != vote_type else 0
    })
