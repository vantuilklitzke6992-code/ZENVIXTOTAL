from flask import Blueprint, render_template
from utils.presence import online_users
from services.provider_service import get_providers, enrich_provider, get_online_providers

public_bp = Blueprint('public', __name__)


@public_bp.route('/', endpoint='home')
def home():
    featured_providers = [enrich_provider(provider) for provider in get_providers()[:3]]
    online_providers = get_online_providers(limit=4)
    return render_template(
        'public/home.html',
        featured_providers=featured_providers,
        online_providers=online_providers,
    )
