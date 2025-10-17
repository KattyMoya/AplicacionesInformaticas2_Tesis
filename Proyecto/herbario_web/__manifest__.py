{
    'name': 'Herbario Web',
    'version': '1.0',
    'summary': 'Página web pública para herbario virtual con CRUD de especímenes',
    'description': """
        Extiende el herbario virtual con una interfaz web pública.
        Incluye menú hamburguesa, estadísticas, repositorio en cards, galería y about.
        CRUD: Read público, full CRUD para admins.
    """,
    'author': 'Katty Moyano',
    'category': 'Website',
    'depends': ['base', 'website', 'herbario_virtual'],  # Depende del módulo anterior y website
    'data': [
        'views/herbario_menus.xml',  # Menús web
        'views/herbario_templates.xml',  # Plantillas QWeb para frontend
        #'security/ir.model.access.csv',  
    ],
    'assets': {
        'web.assets_frontend': [
            'herbario_web/static/src/css/herbario_styles.css',
            'herbario_web/static/src/js/herbario_scripts.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}