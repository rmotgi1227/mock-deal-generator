"""
Substitute names, vendor, customer, industry, deal_size in a source deal.
Used by the pool-serving path so one pool deal can be re-served as many
distinct-looking deals without hitting Claude.
"""

import json
import random
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Generic fictional customer company names by rough industry flavor.
# When `customer_company` override is not provided, one is picked at random.
FICTIONAL_CUSTOMERS = [
    "Acme Logistics", "Globex Health", "Initech Solutions", "Umbrella Retail",
    "Vandelay Industries", "Hooli Systems", "Pied Piper Networks", "Massive Dynamic",
    "Soylent Foods", "Wayne Enterprises", "Stark Industries", "Cyberdyne Software",
    "Tyrell Biotech", "Weyland Manufacturing", "Aperture Labs", "Wonka Confections",
    "Oscorp Pharmaceuticals", "Lexcorp Energy", "Nakatomi Trading", "Spacely Sprockets",
    "Cogswell Cogs", "Planet Express", "Bluth Construction", "Dunder Mifflin",
    "Vandalay Imports", "Pendant Publishing", "Kramerica Industries", "Costanza Marine",
    "Newman Postal Tech", "Hartman Tax Group", "Pearson Specter Legal", "Goliath National",
    "Sterling Cooper Media", "Pawnee Co-op", "Greendale Studios", "Springfield Mills",
    "Sweetwater Energy", "Northwind Traders", "Contoso Manufacturing", "Fabrikam Robotics",
    "Litware Analytics", "Adventure Works Travel", "Tailwind Aviation", "Proseware Audio",
    "Margie's Travel", "Wide World Importers", "Lucerne Publishing", "Trey Research",
    "Coho Vineyards", "Alpine Ski House", "Fourth Coffee", "Graphic Design Institute",
    "Humongous Insurance", "Lamna Healthcare", "Relecloud Hosting", "School of Fine Art",
    "Tasty Treats Bakery", "The Phone Company", "VanArsdel Banking", "Wingtip Toys",
    "Woodgrove Bank", "World Wide Importers", "Adatum Corporation", "Best For You Organics",
    "Blue Yonder Airlines", "City Power & Light", "Consolidated Messenger", "Datum Corporation",
    "First Up Consultants", "Liberty's Delightful Bakery", "Munson's Pickles", "Nod Publishers",
    "Parnell Aerospace", "Proseware Robotics", "Tailspin Toys", "The Volcano Coffee Company",
    "Treetops Resort", "Wide World Couriers", "World Wide Importers", "A. Datum",
    "Adventure Works Cycles", "Margie's Travel", "Northwind Electric", "Coho Winery",
    "Lucerne Health", "Wingtip Bikes", "Fabrikam Residences", "Adatum Insurance",
    "Trey Lawn Care", "Litware Software", "Contoso Pharma", "Globex Energy",
    "VanArsdel Apparel", "Relecloud Travel", "Tailspin Sports", "Wingtip Coffee",
    "Coho Cosmetics", "Nod Bookstore", "Liberty Garage", "Munson's Catering",
    "Parnell Logistics", "Treetops Camping", "Best For You Foods", "Lamna Bank",
    "Humongous Health", "Datum Cloud", "City Power Holdings", "Phone Co Wireless",
]


def _vendor_to_domain(vendor: str) -> str:
    """Convert 'Acme Corp Inc' -> 'acmecorpinc.com'."""
    slug = re.sub(r"[^a-z0-9]", "", vendor.lower())
    return f"{slug}.com" if slug else "vendor.com"


def _email_for(full_name: str, domain: str) -> str:
    parts = [p for p in re.split(r"\s+", full_name.strip()) if p]
    if len(parts) >= 2:
        local = f"{parts[0].lower()}.{parts[-1].lower()}"
    elif parts:
        local = parts[0].lower()
    else:
        local = "user"
    local = re.sub(r"[^a-z0-9.]", "", local)
    return f"{local}@{domain}"


def substitute_deal(
    source_deal: Dict[str, Any],
    vendor_company: Optional[str] = None,
    ae_name: Optional[str] = None,
    se_name: Optional[str] = None,
    industry: Optional[str] = None,
    deal_size: Optional[str] = None,
    customer_company: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Return a transformed copy of source_deal with overrides applied.
    Pulls the source values out of metadata, then runs a global
    string-replace pass over the entire deal so transcripts/emails/CRM
    notes also get rewritten.
    """
    deal = json.loads(json.dumps(source_deal))  # deep copy
    metadata = deal["metadata"]

    # --- source values ---
    src_vendor = metadata["sales_rep"]["vendor_company"]
    src_ae_name = metadata["sales_rep"]["name"]
    src_ae_email = metadata["sales_rep"].get("email", "")
    src_email_domain = src_ae_email.split("@")[-1] if "@" in src_ae_email else ""

    src_se = metadata.get("sales_engineer") or {}
    src_se_name = src_se.get("name")

    src_customer = metadata["company"]["name"]

    # --- resolve new values ---
    new_vendor = vendor_company or src_vendor
    new_ae_name = ae_name or src_ae_name
    new_se_name = se_name or src_se_name
    new_customer = customer_company or random.choice(FICTIONAL_CUSTOMERS)
    new_email_domain = _vendor_to_domain(new_vendor)
    new_ae_email = _email_for(new_ae_name, new_email_domain)
    new_se_email = _email_for(new_se_name, new_email_domain) if new_se_name else None

    # --- structured metadata updates ---
    metadata["sales_rep"]["vendor_company"] = new_vendor
    metadata["sales_rep"]["name"] = new_ae_name
    metadata["sales_rep"]["email"] = new_ae_email

    if metadata.get("sales_engineer"):
        metadata["sales_engineer"]["vendor_company"] = new_vendor
        if new_se_name:
            metadata["sales_engineer"]["name"] = new_se_name
        if new_se_email:
            metadata["sales_engineer"]["email"] = new_se_email

    metadata["company"]["name"] = new_customer
    if industry:
        metadata["company"]["industry"] = industry
        metadata["config"]["industry"] = industry
    if deal_size:
        metadata["config"]["deal_size"] = deal_size

    new_deal_id = str(uuid.uuid4())
    metadata["deal_id"] = new_deal_id
    metadata["generated_at"] = (
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    )

    # --- global string sweep over the whole deal JSON ---
    # Order matters: longer/more-specific tokens first so they don't get partially
    # clobbered by a later shorter replacement.
    deal_json = json.dumps(deal)

    def replace_token(text: str, src: str, dst: str, word_boundary: bool) -> str:
        if not src or src == dst:
            return text
        if word_boundary:
            return re.sub(r"\b" + re.escape(src) + r"\b", dst, text)
        return text.replace(src, dst)

    deal_json = replace_token(deal_json, src_ae_email, new_ae_email, False)
    if src_se and src_se.get("email") and new_se_email:
        deal_json = replace_token(deal_json, src_se["email"], new_se_email, False)
    if src_email_domain:
        deal_json = replace_token(deal_json, src_email_domain, new_email_domain, False)
    deal_json = replace_token(deal_json, src_vendor, new_vendor, False)

    # Customer: full name first, then first-word fallback for transcripts
    # that say just "VelocityPay" instead of "VelocityPay Systems".
    deal_json = replace_token(deal_json, src_customer, new_customer, False)
    src_cust_first = src_customer.split()[0] if src_customer else ""
    new_cust_first = new_customer.split()[0] if new_customer else ""
    if src_cust_first and len(src_cust_first) > 3 and src_cust_first.lower() not in _GENERIC_WORDS:
        deal_json = replace_token(deal_json, src_cust_first, new_cust_first, True)

    # Names: full -> first -> last so transcripts that drop to first/last
    # name only ("Alex says...") also get rewritten.
    _replace_name(deal_json, src_ae_name, new_ae_name)  # full
    deal_json = _replace_name_inline(deal_json, src_ae_name, new_ae_name)
    if src_se_name and new_se_name:
        deal_json = _replace_name_inline(deal_json, src_se_name, new_se_name)

    return json.loads(deal_json)


_GENERIC_WORDS = {
    "the", "and", "inc", "corp", "llc", "ltd", "co", "group", "systems",
    "solutions", "technologies", "services", "holdings", "global",
}


def _replace_name(text: str, src: str, dst: str) -> str:
    """Kept for backward compat; just word-boundary full-name replace."""
    if not src or src == dst:
        return text
    return re.sub(r"\b" + re.escape(src) + r"\b", dst, text)


def _replace_name_inline(text: str, src_full: str, dst_full: str) -> str:
    """Replace full name, then first-name, then last-name (word-boundary)."""
    if not src_full or src_full == dst_full:
        return text
    text = re.sub(r"\b" + re.escape(src_full) + r"\b", dst_full, text)
    src_parts = [p for p in src_full.split() if p]
    dst_parts = [p for p in dst_full.split() if p]
    if len(src_parts) >= 1 and len(dst_parts) >= 1:
        text = re.sub(r"\b" + re.escape(src_parts[0]) + r"\b", dst_parts[0], text)
    if len(src_parts) >= 2 and len(dst_parts) >= 2:
        text = re.sub(r"\b" + re.escape(src_parts[-1]) + r"\b", dst_parts[-1], text)
    return text
