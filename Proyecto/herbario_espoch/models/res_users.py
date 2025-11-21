from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class ResUsers(models.Model):
    _inherit = 'res.users'

    # Rol específico del herbario
    herbario_role = fields.Selection([
        ('encargado', 'Encargado del Herbario'),
        ('admin_ti', 'Administrador TI'),
        ('usuario', 'Usuario General')
    ], string='Rol en Herbario', 
       default='usuario',
       required=True,
       tracking=True,
       help='Define el nivel de acceso y responsabilidades en el sistema del herbario'
    )

    # Estadísticas
    specimens_created_count = fields.Integer(
        string='Especímenes Creados',
        compute='_compute_herbario_stats',
        help='Número total de especímenes registrados por el usuario'
    )
    locations_added_count = fields.Integer(
        string='Ubicaciones Agregadas',
        compute='_compute_herbario_stats'
    )
    specimens_modified_count = fields.Integer(
        string='Especímenes Modificados',
        compute='_compute_herbario_stats',
        help='Número total de especímenes modificados por el usuario'
    )
    images_uploaded_count = fields.Integer(
        string='Imágenes Subidas',
        compute='_compute_herbario_stats',
        help='Número total de imágenes subidas por el usuario'
    )
    last_herbario_activity = fields.Datetime(
        string='Última Actividad en Herbario',
        compute='_compute_last_activity',
        help='Fecha y hora de la última actividad en el sistema'
    )

    # Información adicional
    institution = fields.Char(
        string='Institución',
        help='Institución académica o de investigación'
    )
    research_area = fields.Char(
        string='Área de Investigación',
        help='Área específica de investigación botánica'
    )
    orcid_id = fields.Char(
        string='ORCID ID',
        help='Identificador ORCID del investigador'
    )

    @api.depends('specimens_created_count', 'locations_added_count', 'images_uploaded_count')
    def _compute_herbario_stats(self):
        for user in self:
            user.specimens_created_count = self.env['herbario.specimen'].search_count([
                ('created_by', '=', user.id)
            ])
            user.locations_added_count = self.env['herbario.collection.site'].search_count([
                ('created_by', '=', user.id)
            ])
            user.images_uploaded_count = self.env['herbario.image'].search_count([
                ('uploaded_by', '=', user.id),
                ('deleted_at', '=', False)
            ])

    @api.depends()
    def _compute_last_activity(self):
        for user in self:
            last_log = self.env['herbario.history.log'].search([
                ('user_id', '=', user.id)
            ], limit=1, order='timestamp desc')
            user.last_herbario_activity = last_log.timestamp if last_log else False

    def action_view_my_specimens(self):
        self.ensure_one()
        return {
            'name': 'Mis Especímenes',
            'type': 'ir.actions.act_window',
            'res_model': 'herbario.specimen',
            'view_mode': 'tree,form',
            'domain': [('created_by', '=', self.id)],
            'context': {'default_created_by': self.id}
        }

    def action_view_my_activity(self):
        self.ensure_one()
        return {
            'name': 'Mi Actividad',
            'type': 'ir.actions.act_window',
            'res_model': 'herbario.history.log',
            'view_mode': 'tree',
            'domain': [('user_id', '=', self.id)],
            'context': {'search_default_group_by_action': 1}
        }
        
    def action_deactivate_user(self):
        self.ensure_one()
        if self.herbario_role == 'encargado':
            # Verificar si hay otro encargado activo
            other_encargados = self.search([
                ('id', '!=', self.id),
                ('herbario_role', '=', 'encargado'),
                ('is_active', '=', True)
            ])
            if not other_encargados:
                raise ValidationError(
                    'No se puede desactivar al último encargado del herbario. '
                    'Debe haber al menos un encargado activo en el sistema.'
                )
        self.write({'is_active': False})