from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HerbarioAuthor(models.Model):
    _name = 'herbario.author'
    _description = 'Autores Botánicos'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Nombre del Autor',
        required=True,
        index=True,
        tracking=True
    )

    specimen_ids = fields.Many2many(
        'herbario.specimen',
        'herbario_specimen_author',
        'author_id',
        'specimen_id',
        string='Especímenes'
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name)',
         'El nombre del autor debe ser único!')
    ]

    def name_get(self):
        return [(record.id, record.name) for record in self]

class HerbarioDeterminer(models.Model):
    _name = 'herbario.determiner'
    _description = 'Determinadores Botánicos'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Nombre del Determinador',
        required=True,
        index=True,
        tracking=True
    )

    specimen_ids = fields.Many2many(
        'herbario.specimen',
        'herbario_specimen_determiner',
        'determiner_id',
        'specimen_id',
        string='Especímenes'
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name)',
         'El nombre del determinador debe ser único!')
    ]

    def name_get(self):
        return [(record.id, record.name) for record in self]

class HerbarioCollector(models.Model):
    _name = 'herbario.collector'
    _description = 'Colectores Botánicos'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Nombre del Colector',
        required=True,
        index=True,
        tracking=True
    )

    specimen_ids = fields.Many2many(
        'herbario.specimen',
        'herbario_specimen_collector',
        'collector_id',
        'specimen_id',
        string='Especímenes'
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name)',
         'El nombre del colector debe ser único!')
    ]

    def name_get(self):
        return [(record.id, record.name) for record in self]