from odoo import http
from odoo.http import request
import base64  # ← AGREGAR ESTE IMPORT

class HerbarioController(http.Controller):

    @http.route(['/herbario', '/herbario/'], type='http', auth='public', website=True)
    def herbario_home(self, **kw):
        return request.render('herbario_web.herbario_home', {})

    @http.route(['/herbario/stats'], type='http', auth='public', website=True)
    def herbario_stats(self, **kw):
        Especimen = request.env['herbario.especimen'].sudo()
        total = Especimen.search_count([])
        familias = len(set(Especimen.search([]).mapped('familia')))
        imagenes = Especimen.search_count([('imagen', '!=', False)])  # ← CAMBIO: image → imagen
        activos = Especimen.search_count([('estado', '=', 'activo')])
        return request.render('herbario_web.herbario_stats', {
            'total_especimenes': total,
            'familias_unicas': familias,
            'imagenes_count': imagenes,
            'activos_count': activos,
        })

    @http.route(['/herbario/repositorio'], type='http', auth='public', website=True)
    def herbario_repo(self, **kw):
        Especimen = request.env['herbario.especimen'].sudo()
        especimenes = Especimen.search([('es_publico', '=', True)], order='nombre_comun asc')
        return request.render('herbario_web.herbario_repo', {'especimenes': especimenes})

    @http.route(['/herbario/galeria'], type='http', auth='public', website=True)
    def herbario_gallery(self, **kw):
        Especimen = request.env['herbario.especimen'].sudo()
        especimenes_con_imagen = Especimen.search([('imagen', '!=', False), ('es_publico', '=', True)])  # ← CAMBIO: image → imagen
        return request.render('herbario_web.herbario_gallery', {'especimenes_con_imagen': especimenes_con_imagen})

    @http.route(['/herbario/about'], type='http', auth='public', website=True)
    def herbario_about(self, **kw):
        return request.render('herbario_web.herbario_about', {})

    @http.route(['/herbario/detalle/<model("herbario.especimen"):especimen>'], type='http', auth='public', website=True)
    def herbario_detalle(self, especimen, **kw):
        return request.render('herbario_web.herbario_detalle', {'especimen': especimen})

    # Rutas para CRUD (solo usuarios autenticados)
    @http.route(['/herbario/crear'], type='http', auth='user', methods=['GET', 'POST'], website=True, csrf=False)
    def herbario_crear(self, **post):
        if request.httprequest.method == 'POST':
            Especimen = request.env['herbario.especimen'].sudo()
            vals = {
                'nombre_comun': post.get('nombre_comun'),
                'nombre_cientifico': post.get('nombre_cientifico'),
                'familia': post.get('familia', ''),
                'descripcion': post.get('descripcion', ''),
                'fecha_coleccion': post.get('fecha_coleccion'),
                'ubicacion': post.get('ubicacion', ''),
                'estado': 'activo',
                'es_publico': True,
            }
            if 'imagen' in post and post['imagen']:  # ← CAMBIO: imagen en el form HTML
                try:
                    image_file = post['imagen']
                    vals['imagen'] = base64.b64encode(image_file.read())  # ← CAMBIO: image → imagen
                except:
                    pass
            Especimen.create(vals)
            return request.redirect('/herbario/repositorio')
        return request.render('herbario_web.herbario_repo')

    @http.route(['/herbario/editar/<model("herbario.especimen"):especimen>'], type='http', auth='user', methods=['GET', 'POST'], website=True, csrf=False)
    def herbario_editar(self, especimen, **post):
        if request.httprequest.method == 'POST':
            vals = {
                'nombre_comun': post.get('nombre_comun'),
                'nombre_cientifico': post.get('nombre_cientifico'),
                'familia': post.get('familia', ''),
                'descripcion': post.get('descripcion', ''),
                'fecha_coleccion': post.get('fecha_coleccion'),
                'ubicacion': post.get('ubicacion', ''),
                'estado': post.get('estado', 'activo'),
                'es_publico': post.get('es_publico', True),
            }
            if 'imagen' in post and post['imagen']:  # ← CAMBIO: imagen en el form HTML
                try:
                    image_file = post['imagen']
                    vals['imagen'] = base64.b64encode(image_file.read())  # ← CAMBIO: image → imagen
                except:
                    pass
            especimen.sudo().write(vals)
            return request.redirect('/herbario/detalle/%s' % especimen.id)
        return request.render('herbario_web.herbario_edit_form', {'especimen': especimen})

    @http.route(['/herbario/borrar/<model("herbario.especimen"):especimen>'], type='http', auth='user', methods=['POST'], website=True, csrf=False)
    def herbario_borrar(self, especimen, **kw):
        especimen.sudo().unlink()
        return request.redirect('/herbario/repositorio')