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
from typing import Any, Dict, List, Optional

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

    # Build stakeholder remap (DO NOT mutate metadata yet — the atomic swap
    # below operates on the serialized JSON and would re-rewrite anything we
    # write in-place. We apply structured metadata fixes at the very end.)
    customer_domain = _vendor_to_domain(new_customer)
    used_names = {new_ae_name, new_se_name} - {None}
    stakeholder_remap = []  # list of (src_name, new_name, src_email, new_email)
    for sh in metadata.get("stakeholders", []) or []:
        src_sh_name = sh.get("name")
        if not src_sh_name:
            continue
        new_sh_name = _random_full_name(used_names)
        src_sh_email = sh.get("email", "")
        new_sh_email = _email_for(new_sh_name, customer_domain)
        stakeholder_remap.append((src_sh_name, new_sh_name, src_sh_email, new_sh_email))

    new_deal_id = str(uuid.uuid4())

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

    # Non-name swaps run in fixed order; they don't collide with one another.
    deal_json = replace_token(deal_json, src_ae_email, new_ae_email, False)
    if src_se and src_se.get("email") and new_se_email:
        deal_json = replace_token(deal_json, src_se["email"], new_se_email, False)
    for _, _, sh_src_email, sh_new_email in stakeholder_remap:
        if sh_src_email:
            deal_json = replace_token(deal_json, sh_src_email, sh_new_email, False)
    if src_email_domain:
        deal_json = replace_token(deal_json, src_email_domain, new_email_domain, False)
    deal_json = replace_token(deal_json, src_vendor, new_vendor, False)
    deal_json = replace_token(deal_json, src_customer, new_customer, False)
    src_cust_first = src_customer.split()[0] if src_customer else ""
    new_cust_first = new_customer.split()[0] if new_customer else ""
    if src_cust_first and len(src_cust_first) > 3 and src_cust_first.lower() not in _GENERIC_WORDS:
        deal_json = replace_token(deal_json, src_cust_first, new_cust_first, True)

    # Name swaps must run atomically — otherwise replacing SE first-name
    # ("Sarah" -> "Devansh") would clobber the AE first-name we just
    # installed if both share "Sarah".
    name_swaps: List[tuple] = []

    def _push(src: str, dst: str) -> None:
        if src and dst and src != dst:
            name_swaps.append((src, dst))

    # Full names first (longest match wins during placeholder phase).
    _push(src_ae_name, new_ae_name)
    if src_se_name and new_se_name:
        _push(src_se_name, new_se_name)
    for sh_src, sh_new, _, _ in stakeholder_remap:
        _push(sh_src, sh_new)
    # First / last names
    for src_full, new_full in (
        [(src_ae_name, new_ae_name)]
        + ([(src_se_name, new_se_name)] if src_se_name and new_se_name else [])
        + [(s[0], s[1]) for s in stakeholder_remap]
    ):
        s_parts = src_full.split()
        d_parts = new_full.split()
        if len(s_parts) >= 1 and len(d_parts) >= 1:
            _push(s_parts[0], d_parts[0])
        if len(s_parts) >= 2 and len(d_parts) >= 2:
            _push(s_parts[-1], d_parts[-1])

    deal_json = _atomic_swap(deal_json, name_swaps, word_boundary=True)
    deal = json.loads(deal_json)

    # Structured metadata reassignment last so it can't be re-clobbered by the
    # name sweeps above. These are the canonical record-of-truth fields.
    md = deal["metadata"]
    md["deal_id"] = new_deal_id
    md["generated_at"] = (
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    )
    md["sales_rep"]["vendor_company"] = new_vendor
    md["sales_rep"]["name"] = new_ae_name
    md["sales_rep"]["email"] = new_ae_email
    if md.get("sales_engineer"):
        md["sales_engineer"]["vendor_company"] = new_vendor
        if new_se_name:
            md["sales_engineer"]["name"] = new_se_name
        if new_se_email:
            md["sales_engineer"]["email"] = new_se_email
    md["company"]["name"] = new_customer
    if industry:
        md["company"]["industry"] = industry
        md["config"]["industry"] = industry
    if deal_size:
        md["config"]["deal_size"] = deal_size
    for sh, (_, new_sh_name, _, new_sh_email) in zip(
        md.get("stakeholders", []) or [], stakeholder_remap
    ):
        sh["name"] = new_sh_name
        sh["email"] = new_sh_email

    return deal


def _atomic_swap(text: str, swaps: List[tuple], word_boundary: bool = True) -> str:
    """
    Replace many src tokens with dst tokens without inter-swap interference.
    Pass 1: each src -> a unique placeholder. Pass 2: placeholder -> dst.
    Sorted by src length desc so "Sarah Mitchell" wins over "Sarah" when
    both are in the swap list.
    """
    seen_src = set()
    unique_swaps = []
    for src, dst in sorted(swaps, key=lambda s: -len(s[0])):
        if src in seen_src:
            continue
        seen_src.add(src)
        unique_swaps.append((src, dst))

    placeholders = []
    for i, (src, dst) in enumerate(unique_swaps):
        ph = f"\x00NAME_REPL_{i}\x00"
        placeholders.append((ph, dst))
        if word_boundary:
            text = re.sub(r"\b" + re.escape(src) + r"\b", ph, text)
        else:
            text = text.replace(src, ph)
    for ph, dst in placeholders:
        text = text.replace(ph, dst)
    return text


_GENERIC_WORDS = {
    "the", "and", "inc", "corp", "llc", "ltd", "co", "group", "systems",
    "solutions", "technologies", "services", "holdings", "global",
}

_FIRST_NAMES = [
    "Aaron", "Aisha", "Alex", "Amanda", "Amir", "Andrea", "Anthony", "April",
    "Beatriz", "Benjamin", "Brandon", "Brianna", "Caleb", "Camila", "Carlos",
    "Caroline", "Chloe", "Christine", "Daniel", "Deepa", "Derek", "Diana",
    "Dmitri", "Eli", "Elena", "Emily", "Erin", "Ethan", "Fatima", "Felix",
    "Gabriel", "Grace", "Hannah", "Hassan", "Hiroshi", "Ian", "Imani", "Isaac",
    "Isabel", "Jamal", "Jasmine", "Joshua", "Julia", "Karim", "Katherine",
    "Kenji", "Khalid", "Kira", "Laila", "Lauren", "Leila", "Leo", "Liam",
    "Lucia", "Malia", "Marcus", "Margaret", "Maya", "Mateo", "Megan", "Mira",
    "Naomi", "Natalie", "Nicholas", "Noah", "Oliver", "Omar", "Owen", "Paige",
    "Pavel", "Peter", "Priya", "Quincy", "Rafael", "Rebecca", "Riley", "Ruby",
    "Samir", "Sanjay", "Shawn", "Shreya", "Simone", "Sofia", "Soren", "Tara",
    "Theo", "Tristan", "Vera", "Victor", "Vivian", "Wei", "Wesley", "Xavier",
    "Yara", "Yuki", "Zara", "Zoe",
]

_LAST_NAMES = [
    "Adams", "Alvarez", "Anderson", "Bailey", "Banerjee", "Barnes", "Bell",
    "Bennett", "Bishop", "Black", "Brooks", "Bryant", "Burke", "Butler",
    "Campbell", "Carter", "Castro", "Coleman", "Collins", "Cox", "Crawford",
    "Cruz", "Davies", "Diaz", "Dixon", "Edwards", "Elliott", "Fischer",
    "Fitzgerald", "Fleming", "Ford", "Foster", "Franklin", "Gallagher", "Garcia",
    "Gibson", "Goldberg", "Gomez", "Graves", "Greene", "Griffin", "Hamilton",
    "Hanson", "Harper", "Hayes", "Hendricks", "Hernandez", "Holloway", "Hudson",
    "Iqbal", "Jackson", "Jensen", "Jimenez", "Kapoor", "Kennedy", "Khan",
    "Knight", "Kovacs", "Lambert", "Larsen", "Lawson", "Levine", "Lopez",
    "Mackenzie", "Marquez", "Mason", "McCarthy", "Mendoza", "Miller", "Mitchell",
    "Murphy", "Nakamura", "Nakashima", "Nguyen", "Norris", "Okafor", "Olsen",
    "Ortiz", "Owens", "Park", "Pearson", "Petrov", "Phillips", "Pierce", "Powers",
    "Quinn", "Ramirez", "Reeves", "Richardson", "Riley", "Rivera", "Robinson",
    "Romero", "Russo", "Sanchez", "Santos", "Schaefer", "Schmidt", "Shah",
    "Singh", "Snyder", "Sokolov", "Stevens", "Stewart", "Sullivan", "Suzuki",
    "Tanaka", "Thompson", "Vargas", "Vasquez", "Walker", "Wallace", "Watson",
    "Webb", "Wells", "Whitfield", "Wright", "Yamamoto", "Yoshida", "Zhao",
]


def _random_full_name(used: set) -> str:
    """Pick a random first+last not already in `used`. Mutates `used`."""
    for _ in range(200):
        name = f"{random.choice(_FIRST_NAMES)} {random.choice(_LAST_NAMES)}"
        if name not in used:
            used.add(name)
            return name
    # Pool exhausted — fall back to indexed name
    return f"Person {len(used)+1}"


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
