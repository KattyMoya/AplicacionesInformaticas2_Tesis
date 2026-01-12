{
    'name': 'HerbaProgram - Sistema Integral',
    'version': '1.0.0',
    'sequence': 10,
    'category': 'Education',
    'summary': 'Sistema de Gestión Integral de Registros Botánicos e Imágenes del Herbario ESPOCH',
    'description': """
        Sistema Completo de Gestión del Herbario ESPOCH
        ================================================
        
        Características principales:
        * Gestión completa de especímenes botánicos
        * Múltiples ubicaciones de recolección por espécimen
        * Galería de imágenes con EXIF
        * Generación automática de códigos QR
        * Sistema de auditoría completo
        * Búsqueda y filtros avanzados
        * Mapas de geolocalización
        * Estadísticas y reportes
        * Portal web público
        
        Desarrollado por: Katty Alexandra Moyano Ramos
        Director: Ing. Cristian Alexis García Pumagualle
        Institución: ESPOCH
    """,
    'author': 'Katty Alexandra Moyano Ramos',
    'website': 'https://www.espoch.edu.ec',
    'depends': ['base', 'web', 'website', 'mail'],
    'data': [
        # Seguridad
        'security/herbario_security.xml',
        'security/ir.model.access.csv',

        # Datos base
        'data/sequence_data.xml',
        'data/optimization.sql',

        # Vistas Backend
        'views/specimen_views.xml',
        'views/collection_site_views.xml',
        'views/image_views.xml',
        'views/qr_code_views.xml',
        'views/audit_log_views.xml',
        'views/herbario_menus.xml',
        'views/location_views.xml',

        # Vistas Website
        'views/website_templates.xml',
        'views/website_menus.xml',
        'views/website_snippets.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'herbario_espoch/static/src/css/herbario_backend.css',
        ],
        'web.assets_frontend': [
            # Tus archivos JS personalizados
            'herbario_espoch/static/src/css/herbario_website.css',
            'herbario_espoch/static/src/js/repository_snippet.js',
            'herbario_espoch/static/src/js/statistics_pages.js',
        ],
        'web.assets_qweb': [
            'herbario_espoch/static/src/xml/*.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}