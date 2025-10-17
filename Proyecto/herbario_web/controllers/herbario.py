import logging
from datetime import datetime
from odoo import fields
from odoo import http  # Import para @http.route
from odoo.http import request
from odoo.addons.website.controllers.main import Website

_logger = logging.getLogger(__name__)

class HerbarioController(Website):

    @staticmethod
    def _get_especimenes(domain=None):
        """Helper para obtener especímenes públicos."""
        if domain is None:
            domain = [('es_publico', '=', True)]
        return request.env['herbario.especimen'].search(domain, order='nombre_comun asc')

    # Ruta principal /herbario (home)
    @http.route(['/herbario'], type='http', auth='public', website=True)
    def home(self, **kwargs):
        values = {
            'especimenes': self._get_especimenes(),
        }
        return request.render('herbario_web.herbario_home', values)

    # Ruta estadísticas /herbario/stats
    @http.route(['/herbario/stats'], type='http', auth='public', website=True)
    def stats(self, **kwargs):
        Especimen = request.env['herbario.especimen']
        total_especimenes = Especimen.search_count([('es_publico', '=', True)])
        familias_unicas = len(Especimen.search([('es_publico', '=', True)], distinct=True).mapped('familia'))
        imagenes_count = Especimen.search_count([('es_publico', '=', True), ('imagen', '!=', False)])
        activos_count = Especimen.search_count([('es_publico', '=', True), ('estado', '=', 'activo')])
        
        values = {
            'total_especimenes': total_especimenes,
            'familias_unicas': familias_unicas,
            'imagenes_count': imagenes_count,
            'activos_count': activos_count,
        }
        return request.render('herbario_web.herbario_stats', values)

    # Ruta repositorio /herbario/repositorio
    @http.route(['/herbario/repositorio'], type='http', auth='public', website=True)
    def repositorio(self, **kwargs):
        today = fields.Date.context_today(request.env.user)
        especimenes = self._get_especimenes()
        
        values = {
            'especimenes': especimenes,
            'today': today,
        }
        return request.render('herbario_web.herbario_repo', values)

    # Ruta galería /herbario/galeria
    @http.route(['/herbario/galeria'], type='http', auth='public', website=True)
    def galeria(self, **kwargs):
        especimenes_con_imagen = self._get_especimenes([('imagen', '!=', False)])
        
        values = {
            'especimenes_con_imagen': especimenes_con_imagen,
        }
        return request.render('herbario_web.herbario_gallery', values)

    # Ruta about /herbario/about
    @http.route(['/herbario/about'], type='http', auth='public', website=True)
    def about(self, **kwargs):
        values = {}  # Estático, no necesita datos dinámicos
        return request.render('herbario_web.herbario_about', values)