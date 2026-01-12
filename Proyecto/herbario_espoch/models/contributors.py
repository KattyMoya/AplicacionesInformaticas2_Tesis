from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

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

    def unlink(self):
        for record in self:
            if record.specimen_ids:
                raise UserError(
                    f"No se puede eliminar el autor '{record.name}' porque está asociado a {len(record.specimen_ids)} especímenes.\n"
                    "Solo se pueden eliminar autores que no tengan registros asociados."
                )
        return super(HerbarioAuthor, self).unlink()

    def action_safe_delete(self):
        self.ensure_one()
        self.unlink()
        return {'type': 'ir.actions.client', 'tag': 'reload'}

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

    def unlink(self):
        for record in self:
            if record.specimen_ids:
                raise UserError(
                    f"No se puede eliminar el determinador '{record.name}' porque está asociado a {len(record.specimen_ids)} especímenes.\n"
                    "Solo se pueden eliminar determinadores que no tengan registros asociados."
                )
        return super(HerbarioDeterminer, self).unlink()

    def action_safe_delete(self):
        self.ensure_one()
        self.unlink()
        return {'type': 'ir.actions.client', 'tag': 'reload'}

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

    def unlink(self):
        for record in self:
            if record.specimen_ids:
                raise UserError(
                    f"No se puede eliminar el colector '{record.name}' porque está asociado a {len(record.specimen_ids)} especímenes.\n"
                    "Solo se pueden eliminar colectores que no tengan registros asociados."
                )
        return super(HerbarioCollector, self).unlink()

    def action_safe_delete(self):
        self.ensure_one()
        self.unlink()
        return {'type': 'ir.actions.client', 'tag': 'reload'}