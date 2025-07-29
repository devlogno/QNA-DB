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
    """Displays the news feed tailored to the user's level and stream."""
    
    # Get level and stream IDs from the user's selected streams
    user_level_ids = {stream.level_id for stream in current_user.streams}
    user_stream_ids = {stream.id for stream in current_user.streams}

    # Build the filter conditions
    filters = []
    
    # 1. News for everyone (both level_id and stream_id are NULL)
    filters.append(db.and_(NewsArticle.level_id.is_(None), NewsArticle.stream_id.is_(None)))
    
    # 2. News for the user's specific levels (and not for a more specific stream)
    if user_level_ids:
        filters.append(db.and_(NewsArticle.level_id.in_(user_level_ids), NewsArticle.stream_id.is_(None)))
        
    # 3. News for the user's specific streams
    if user_stream_ids:
        filters.append(NewsArticle.stream_id.in_(user_stream_ids))

    # Combine all filters with an OR condition
    articles = NewsArticle.query.filter(or_(*filters)).order_by(NewsArticle.timestamp.desc()).all()

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
            # User is clicking the same button again to remove their vote
            if vote_type == 1: article.upvotes -= 1
            else: article.downvotes -= 1
            db.session.delete(existing_vote)
            vote_type = 0 # Signifies no vote
        else:
            # User is changing their vote
            if vote_type == 1: # Was downvote, now upvote
                article.upvotes += 1
                article.downvotes -= 1
            else: # Was upvote, now downvote
                article.downvotes += 1
                article.upvotes -= 1
            existing_vote.vote_type = vote_type
    else:
        # This is a new vote
        if vote_type == 1: article.upvotes += 1
        else: article.downvotes += 1
        new_vote = NewsVote(user_id=current_user.id, article_id=article.id, vote_type=vote_type)
        db.session.add(new_vote)

    db.session.commit()

    return jsonify({
        'status': 'success',
        'upvotes': article.upvotes,
        'downvotes': article.downvotes,
        'user_vote': vote_type
    })
