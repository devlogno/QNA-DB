# payments.py
from flask import Blueprint, render_template
from flask_login import login_required

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

@payments_bp.route('/pricing')
@login_required
def pricing_page():
    """
    Displays the subscription tiers. For now, this is a placeholder.
    Later, it will integrate with a payment gateway like Stripe.
    """
    return render_template('pricing.html')

