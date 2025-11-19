import markdown
import bleach
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.nl2br import Nl2BrExtension

# Dozvoljeni HTML tagovi nakon konverzije iz Markdowna
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'code', 'pre', 'hr', 'ul', 'ol', 'li', 'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td'
]

# Dozvoljeni atributi
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'title'],
    'code': ['class'],
    'pre': ['class']
}

# Dozvoljeni protokoli za linkove
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def markdown_to_html(markdown_text):
    """
    Konvertira Markdown u HTML i sanitizira ga protiv XSS napada.
    
    Args:
        markdown_text (str): Markdown tekst
        
    Returns:
        str: Siguran HTML
    """
    if not markdown_text:
        return ""
    
    # 1. Konverzija Markdown → HTML
    html = markdown.markdown(
        markdown_text,
        extensions=[
            'extra',              # dodaje tabele, footnotes, itd.
            'codehilite',         # syntax highlighting za kod
            FencedCodeExtension(),  # ``` code blocks
            TableExtension(),     # tabele
            Nl2BrExtension()      # novi redovi → <br>
        ]
    )
    
    # 2. Sanitizacija HTML-a (zaštita od XSS)
    clean_html = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True  # ukloni nedozvoljene tagove umjesto escapanja
    )
    
    # 3. Linkovi se otvaraju u novom tabu
    clean_html = bleach.linkify(
        clean_html,
        callbacks=[lambda attrs, new: attrs]
    )
    
    return clean_html