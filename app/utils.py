import markdown
import bleach
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.nl2br import Nl2BrExtension


ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'code', 'pre', 'hr', 'ul', 'ol', 'li', 'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td'
]


ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'title'],
    'code': ['class'],
    'pre': ['class']
}


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
            'extra',              
            'codehilite',         
            FencedCodeExtension(),  
            TableExtension(),     
            Nl2BrExtension()      
        ]
    )
    
    # 2. Sanitizacija HTML-a 
    clean_html = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True  
    )
    
    
    clean_html = bleach.linkify(
        clean_html,
        callbacks=[lambda attrs, new: attrs]
    )
    
    return clean_html