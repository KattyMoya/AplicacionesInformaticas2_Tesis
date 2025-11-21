from odoo import models, fields, api
from odoo.http import request


class HerbarioAuditLog(models.Model):
    _name = 'herbario.audit.log'
    _description = 'Registro de Auditoría del Herbario'
    _order = 'timestamp desc'

    # --- CAMPOS GENÉRICOS DE AUDITORÍA (REEMPLAZAN A specimen_id, entity_type, entity_id) ---
    res_model = fields.Char(
        string='Modelo Afectado',
        readonly=True,
        required=True,
        index=True
    )
    res_id = fields.Integer(
        string='ID del Registro Afectado',
        readonly=True,
        required=True,
        index=True
    )
    res_id_display = fields.Reference(
        string='Registro Afectado',
        selection='_referencable_models',
        compute='_compute_res_id_display',
        readonly=True,
        help="El registro que fue modificado (Espécimen, Imagen, etc.)"
    )

    # Tipo de acción
    action_type = fields.Selection([
        ('created', 'Creado'),
        ('updated', 'Actualizado'),
        ('deleted', 'Eliminado'),
    ], string='Acción', required=True, index=True)

    # Detalles del cambio
    field_modified = fields.Char(
        string='Campo Modificado',
        help='Nombre del campo que fue modificado'
    )
    old_value = fields.Text(
        string='Valor Anterior'
    )
    new_value = fields.Text(
        string='Valor Nuevo'
    )
    
    # Descripción del cambio
    description = fields.Text(
        string='Descripción'
    )

    # Información del usuario
    user_id = fields.Many2one(
        'res.users',
        string='Usuario',
        required=True,
        default=lambda self: self.env.user,
        readonly=True
    )
    user_name = fields.Char(related='user_id.name', string='Nombre del Usuario', readonly=True)
    
    # Timestamp
    timestamp = fields.Datetime(
        string='Fecha y Hora',
        required=True,
        index=True,
        default=fields.Datetime.now
    )

    # Metadata adicional
    ip_address = fields.Char(
        string='Dirección IP',
        help='IP desde donde se realizó el cambio',
        readonly=True
    )
    user_agent = fields.Char(
        string='User Agent',
        help='Navegador/cliente utilizado',
        readonly=True
    )

    # Campos computados
    time_ago = fields.Char(
        string='Hace',
        compute='_compute_time_ago',
        readonly=True
    )

    @api.model
    def _referencable_models(self):
        """ Devuelve los modelos que pueden ser referenciados en la auditoría. """
        return [
            ('herbario.specimen', 'Espécimen'),
            ('herbario.image', 'Imagen'),
        ]

    @api.depends('res_model', 'res_id')
    def _compute_res_id_display(self):
        """ Construye el campo de referencia para la vista. """
        for log in self:
            if log.res_model and log.res_id:
                log.res_id_display = f'{log.res_model},{log.res_id}'
            else:
                log.res_id_display = False

    @api.depends('timestamp')
    def _compute_time_ago(self):
        """Calcula tiempo transcurrido desde el cambio"""
        for record in self:
            record.time_ago = fields.Datetime.from_string(record.timestamp).strftime('%Y-%m-%d %H:%M') if record.timestamp else ''

    @api.model
    def _log_change(self, res_model, res_id, action, description, changes=None):
        """
        Método centralizado para crear logs.
        'changes' es una lista de diccionarios: [{'field': 'nombre', 'old': 'val1', 'new': 'val2'}]
        """
        http_request = request.httprequest if request else None
        ip_address = http_request.remote_addr if http_request else None
        user_agent = http_request.user_agent.string if http_request and http_request.user_agent else None

        if changes:
            for change in changes:
                self.create({
                    'res_model': res_model,
                    'res_id': res_id,
                    'action_type': action,
                    'description': description,
                    'field_modified': change.get('field'),
                    'old_value': str(change.get('old')),
                    'new_value': str(change.get('new')),
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                })
        else:
            self.create({
                'res_model': res_model,
                'res_id': res_id,
                'action_type': action,
                'description': description,
                'ip_address': ip_address,
                'user_agent': user_agent,
            })