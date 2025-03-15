from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class PriceHistory:
    price: float
    date: datetime
    store: str

@dataclass
class CompetitorProduct:
    url: str
    price: float
    store: str
    last_updated: datetime
    availability: bool

class ProductTracker:
    def __init__(self, mysql):
        self.mysql = mysql

    def add_product(self, user_id: int, product_url: str, target_price: float, name: str) -> bool:
        cursor = self.mysql.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO product_tracking 
                (user_id, product_url, target_price, name, created_at) 
                VALUES (%s, %s, %s, %s, NOW())
            """, (user_id, product_url, target_price, name))
            self.mysql.connection.commit()
            return True
        except Exception as e:
            print(f"Error adding product: {e}")
            return False
        finally:
            cursor.close()

    def get_price_history(self, product_id: int) -> List[PriceHistory]:
        cursor = self.mysql.connection.cursor()
        try:
            cursor.execute("""
                SELECT price, date, store 
                FROM price_history 
                WHERE product_id = %s 
                ORDER BY date DESC
            """, (product_id,))
            results = cursor.fetchall()
            return [PriceHistory(price=r[0], date=r[1], store=r[2]) for r in results]
        finally:
            cursor.close()

    def get_competitor_products(self, product_id: int) -> List[CompetitorProduct]:
        cursor = self.mysql.connection.cursor()
        try:
            cursor.execute("""
                SELECT url, price, store, last_updated, availability 
                FROM competitor_products 
                WHERE product_id = %s
            """, (product_id,))
            results = cursor.fetchall()
            return [CompetitorProduct(
                url=r[0], price=r[1], store=r[2], 
                last_updated=r[3], availability=r[4]
            ) for r in results]
        finally:
            cursor.close()