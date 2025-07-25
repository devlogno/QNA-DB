# news.py
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, NewsArticle, NewsVote

news_bp = Blueprint('news', __name__)

@news_bp.route('/news')
@login_required
def news_feed():
    """Displays the news feed tailored to the user's level."""
    
    # Get the names of the levels the user is subscribed to
    user_level_names = [level.name for level in current_user.levels]

    # Build a filter based on the user's level names
    level_filter = []
    if 'SSC' in user_level_names:
        level_filter.append(NewsArticle.for_ssc == True)
    if 'HSC' in user_level_names:
        level_filter.append(NewsArticle.for_hsc == True)
    
    if not level_filter:
        articles = [] # Or show some default news
    else:
        from sqlalchemy import or_
        articles = NewsArticle.query.filter(or_(*level_filter)).order_by(NewsArticle.timestamp.desc()).all()

    user_votes = {vote.article_id: vote.vote_type for vote in current_user.news_votes}
    
    return render_template('news.html', articles=articles, user_votes=user_votes)


@news_bp.route('/news/vote/<int:article_id>', methods=['POST'])
@login_required
def vote_on_news(article_id):
    """Handles upvoting and downvoting on a news article."""
    article = NewsArticle.query.get_or_404(article_id)
    vote_type = request.json.get('vote_type') # Expecting 1 for upvote, -1 for downvote

    if vote_type not in [1, -1]:
        return jsonify({'status': 'error', 'message': 'Invalid vote type.'}), 400

    existing_vote = NewsVote.query.filter_by(user_id=current_user.id, article_id=article.id).first()

    if existing_vote:
        # User is changing their vote or retracting it
        if existing_vote.vote_type == vote_type:
            # Retracting vote
            if vote_type == 1: article.upvotes -= 1
            else: article.downvotes -= 1
            db.session.delete(existing_vote)
        else:
            # Changing vote
            if vote_type == 1: # Was downvote, now upvote
                article.upvotes += 1
                article.downvotes -= 1
            else: # Was upvote, now downvote
                article.downvotes += 1
                article.upvotes -= 1
            existing_vote.vote_type = vote_type
    else:
        # New vote
        if vote_type == 1: article.upvotes += 1
        else: article.downvotes += 1
        new_vote = NewsVote(user_id=current_user.id, article_id=article.id, vote_type=vote_type)
        db.session.add(new_vote)

    db.session.commit()

    return jsonify({
        'status': 'success',
        'upvotes': article.upvotes,
        'downvotes': article.downvotes,
        'user_vote': vote_type if not existing_vote or existing_vote.vote_type != vote_type else 0 # 0 indicates retraction
    })
