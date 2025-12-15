"""Keyboard builders for reply and inline layouts."""

from .reply import main_menu_kb, phone_request_kb, location_request_kb  # noqa: F401
from .inline import (  # noqa: F401
    categories_kb,
    products_navigation_kb,
    product_action_kb,
    back_to_categories_kb,
    order_date_kb,
    order_time_kb,
    card_text_kb,
    support_menu_kb,
    support_faq_kb,
    admin_main_menu_kb,
    admin_categories_kb,
    admin_edit_product_kb,
    orders_list_nav_kb,
)

