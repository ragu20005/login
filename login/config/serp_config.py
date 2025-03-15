SERP_PROVIDERS = {
    'google': {
        'endpoint': 'https://serpapi.com/search',
        'params': ['q', 'location', 'device', 'hl', 'gl', 'safe', 'num', 'start']
    },
    'bing': {
        'endpoint': 'https://api.bing.microsoft.com/v7.0/search',
        'params': ['q', 'count', 'offset', 'mkt', 'safesearch']
    }
}

SERP_TEMPLATES = {
    'product_search': {
        'type': 'shopping',
        'params': ['product_name', 'price_range', 'location']
    },
    'news_search': {
        'type': 'news',
        'params': ['keyword', 'date_range', 'language']
    },
    'local_business': {
        'type': 'local',
        'params': ['business_type', 'location', 'radius']
    }
}