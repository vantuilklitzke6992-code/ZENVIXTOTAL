from flask import Blueprint, render_template
from services.provider_service import get_providers, enrich_provider

public_bp = Blueprint('public', __name__)


@public_bp.route('/', endpoint='home')
def home():
    providers = [enrich_provider(provider) for provider in get_providers()]

    featured_providers = sorted(
        (
            provider
            for provider in providers
            if provider["rating_count"] > 0
            or provider["completed_services"] > 0
        ),
        key=lambda provider: provider["recommendation_score"],
        reverse=True,
    )[:3]

    online_providers = [
        provider for provider in providers if provider["online"]
    ][:4]

    return render_template(
        'public/home.html',
        featured_providers=featured_providers,
        online_providers=online_providers,
    )
