import requests
from typing import Dict, List, Optional
from datetime import datetime

class SERPScraper:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search"

    async def search_google(self, query: str, **params) -> Dict:
        """
        Perform Google search using SERP API
        """
        default_params = {
            'api_key': self.api_key,
            'engine': 'google',
            'q': query,
            'num': 100  # results per page
        }
        params = {**default_params, **params}
        
        response = requests.get(self.base_url, params=params)
        return response.json()

    async def get_shopping_results(self, product: str, location: Optional[str] = None) -> List[Dict]:
        """
        Get shopping results for a product
        """
        params = {
            'engine': 'google_shopping',
            'location': location
        }
        return await self.search_google(product, **params)

    async def get_news_results(self, keyword: str, date_range: Optional[str] = None) -> List[Dict]:
        """
        Get news results for a keyword
        """
        params = {
            'engine': 'google_news',
            'tbm': 'nws'
        }
        if date_range:
            params['tbs'] = f'qdr:{date_range}'
        return await self.search_google(keyword, **params)

    async def get_local_results(self, query: str, location: str, radius: Optional[int] = None) -> List[Dict]:
        """
        Get local business results
        """
        params = {
            'engine': 'google_maps',
            'location': location,
            'radius': radius or 5000
        }
        return await self.search_google(query, **params)