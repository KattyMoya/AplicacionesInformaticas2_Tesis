from odoo import models, fields

class HerbarioEspecimen(models.Model):
    _inherit = 'herbario.especimen'  # HEREDA del módulo padre
    
    # Solo agrega el campo nuevo que no existe en el padre
    es_publico = fields.Boolean(
        string='Visible en Web', 
        default=True, 
        help='Marca si este especímen se muestra en el sitio web público'
    )