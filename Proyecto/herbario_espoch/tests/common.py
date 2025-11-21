from odoo.tests import common
from datetime import date

class HerbarioTestCase(common.TransactionCase):
    """Clase base con datos de prueba comunes"""
    
    def setUp(self):
        super().setUp()
        
        # Crear familia
        self.family = self.env['herbario.family'].create({
            'name': 'Asteraceae'
        })
        
        # Crear taxón
        self.taxon = self.env['herbario.taxon'].create({
            'name': 'Baccharis latifolia',
            'family_id': self.family.id,
            'genero': 'Baccharis',
            'especie': 'latifolia'
        })
        
        # Crear colector
        self.collector = self.env['herbario.collector'].create({
            'name': 'Juan Pérez'
        })
        
        # Crear autor
        self.author = self.env['herbario.author'].create({
            'name': 'Kunth'
        })
        
        # Crear herbario
        self.herbarium = self.env['herbario.herbarium'].create({
            'name': 'Herbario ESPOCH',
            'code': 'CHEP'
        })
        
        # Crear usuarios de prueba
        self.admin_user = self.env['res.users'].create({
            'name': 'Admin TI Test',
            'login': 'admin_test@espoch.edu.ec',
            'herbario_role': 'admin_ti',
            'groups_id': [(6, 0, [
                self.env.ref('herbario_espoch.group_herbario_admin_ti').id
            ])]
        })
        
        self.encargado_user = self.env['res.users'].create({
            'name': 'Encargado Test',
            'login': 'encargado_test@espoch.edu.ec',
            'herbario_role': 'encargado',
            'groups_id': [(6, 0, [
                self.env.ref('herbario_espoch.group_herbario_encargado').id
            ])]
        })
        
        self.usuario_user = self.env['res.users'].create({
            'name': 'Usuario Test',
            'login': 'usuario_test@espoch.edu.ec',
            'herbario_role': 'usuario',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id
            ])]
        })