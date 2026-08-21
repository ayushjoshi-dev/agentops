"""
AgentOps — Product Search Tool
================================

Searches the product catalog by keyword, category, and price.

WHEN DOES THE AGENT USE THIS?
-------------------------------
- "Find laptops under 60000"
- "Show me Sony headphones"
- "What cameras do you have?"
- "Any phones between 20000 and 40000?"
"""

from typing import Optional
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.product import Product
from app.core.logging import get_logger

logger = get_logger(__name__)

_db_session: Optional[Session] = None


def set_db_session(db: Session):
    global _db_session
    _db_session = db


@tool
def search_products(
    query: str,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    min_price: Optional[float] = None,
) -> str:
    """
    Search the ShopEase product catalog.
    
    Use this tool when a user wants to find products, browse categories,
    or look for products within a price range.
    
    Available categories: Laptop, Mobile, Headphones, TV, Camera, Tablet, Smartwatch
    
    Args:
        query:     Search term (product name, brand, or description keyword)
        category:  Optional category filter (e.g., 'Laptop', 'Mobile')
        max_price: Optional maximum price in INR (Rupees)
        min_price: Optional minimum price in INR (Rupees)
    
    Returns:
        List of matching products with name, price, rating, and availability
    """
    if _db_session is None:
        return "Error: Database not connected."

    # Build query
    q = _db_session.query(Product).filter(Product.is_available == True)

    # Text search on name, brand, description
    if query and query.strip():
        search_term = f"%{query.strip()}%"
        q = q.filter(
            or_(
                Product.name.ilike(search_term),
                Product.brand.ilike(search_term),
                Product.description.ilike(search_term),
                Product.category.ilike(search_term),
            )
        )

    if category:
        q = q.filter(Product.category.ilike(f"%{category}%"))

    if max_price is not None:
        q = q.filter(Product.price <= max_price)

    if min_price is not None:
        q = q.filter(Product.price >= min_price)

    # Order by rating descending (best products first)
    products = q.order_by(Product.rating.desc()).limit(10).all()

    if not products:
        filters = []
        if category:
            filters.append(f"category='{category}'")
        if max_price:
            filters.append(f"max_price=Rs.{max_price:,.0f}")
        if min_price:
            filters.append(f"min_price=Rs.{min_price:,.0f}")
        filter_str = ", ".join(filters) if filters else "no filters"
        return f"No products found matching '{query}' ({filter_str})."

    result_parts = [f"Found {len(products)} products:"]
    for p in products:
        stock_label = f"In Stock ({p.stock_quantity})" if p.stock_quantity > 0 else "Out of Stock"
        result_parts.append(
            f"\n  Product: {p.name}"
            f"\n  Brand: {p.brand or 'N/A'} | Category: {p.category}"
            f"\n  Price: Rs. {p.price:,.2f} | Rating: {p.rating}/5 ({p.review_count} reviews)"
            f"\n  Stock: {stock_label}"
            f"\n  Description: {(p.description or '')[:100]}..."
        )

    logger.info(
        "product_search_complete",
        query=query,
        category=category,
        max_price=max_price,
        results=len(products),
    )
    return "\n".join(result_parts)
