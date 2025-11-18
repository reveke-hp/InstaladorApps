import tkinter as tk
from tkinter import ttk

def setup_styles(root):
    """Configura y devuelve la paleta de colores y estilos usados en la UI.
    Devuelve un dict `colors` que contiene los colores principales.
    """
    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except Exception:
        # Si no está disponible, usar el tema por defecto
        pass

    colors = {
        'primary': '#007bff',
        'primary_light': '#007bff',
        'secondary': '#007bff',
        'success': '#10b981',
        'danger': '#ef4444',
        'warning': '#f59e0b',
        'light': '#f8fafc',
        'dark': '#1e293b',
        'bg': '#f1f5f9',
        'card_bg': '#ffffff',
        'border': '#e2e8f0',
        'text_primary': '#334155',
        'text_secondary': '#64748b'
    }

    # Configurar estilos
    style.configure('Modern.TFrame', background=colors['bg'])
    style.configure('Card.TFrame', background=colors['card_bg'])
    style.configure('Title.TLabel', 
                   background=colors['bg'],
                   foreground=colors['dark'],
                   font=('Segoe UI', 18, 'bold'))

    style.configure('Primary.TButton',
                   padding=(20, 12),
                   background=colors['primary'],
                   foreground='white',
                   borderwidth=0,
                   focuscolor='none')

    style.map('Primary.TButton',
             background=[('active', colors['primary_light']),
                        ('pressed', colors['primary'])]
    )

    style.configure('Secondary.TButton',
                   padding=(15, 8),
                   background=colors['light'],
                   foreground=colors['text_primary'],
                   borderwidth=0)

    style.configure('Modern.Horizontal.TProgressbar',
               background=colors['primary'],
               troughcolor=colors['primary'],
               borderwidth=0,
               lightcolor=colors['primary'],
               darkcolor=colors['primary'])

    style.map('Modern.Horizontal.TProgressbar',
          background=[('!disabled', colors['primary']), ('disabled', colors['primary'])],
          troughcolor=[('!disabled', colors['primary']), ('disabled', colors['primary'])]
    )

    return colors
