from odoo.tests import tagged
from odoo.exceptions import ValidationError, AccessError
from .common import HerbarioTestCase

@tagged('post_install', '-at_install', 'herbario')
class TestUsers(HerbarioTestCase):
    """Tests para permisos y roles de usuarios"""
    
    def test_01_admin_can_create_specimen(self):
        """Test: Admin TI puede crear especímenes"""
        specimen = self.env['herbario.specimen'].with_user(self.admin_user).create({
            'taxon_id': self.taxon.id,
            'herbarium_id': self.herbarium.id,
        })
        
        self.assertTrue(specimen.id, "Admin debe poder crear especímenes")
        print(f"✅ Test 1 PASÓ: Admin creó {specimen.codigo_herbario}")
    
    def test_02_encargado_can_create_specimen(self):
        """Test: Encargado puede crear especímenes"""
        specimen = self.env['herbario.specimen'].with_user(self.encargado_user).create({
            'taxon_id': self.taxon.id,
            'herbarium_id': self.herbarium.id,
        })
        
        self.assertTrue(specimen.id, "Encargado debe poder crear especímenes")
        print(f"✅ Test 2 PASÓ: Encargado creó {specimen.codigo_herbario}")
    
    def test_03_usuario_cannot_create_specimen(self):
        """Test: Usuario normal NO puede crear especímenes"""
        with self.assertRaises(AccessError, msg="Usuario no debe poder crear"):
            self.env['herbario.specimen'].with_user(self.usuario_user).create({
                'taxon_id': self.taxon.id,
                'herbarium_id': self.herbarium.id,
            })
        
        print(f"✅ Test 3 PASÓ: Usuario bloqueado correctamente")
    
    def test_04_usuario_can_read_specimen(self):
        """Test: Usuario puede leer especímenes públicos"""
        specimen = self.env['herbario.specimen'].create({
            'taxon_id': self.taxon.id,
            'herbarium_id': self.herbarium.id,
            'es_publico': True,
        })
        
        # Usuario intenta leer
        specimen_as_user = specimen.with_user(self.usuario_user)
        
        self.assertEqual(specimen_as_user.codigo_herbario, specimen.codigo_herbario,
                        "Usuario debe poder leer especímenes públicos")
        
        print(f"✅ Test 4 PASÓ: Usuario leyó {specimen.codigo_herbario}")
    
    def test_05_herbario_stats_computation(self):
        """Test: Estadísticas de usuario se calculan correctamente"""
        # Crear especímenes como encargado
        for i in range(3):
            self.env['herbario.specimen'].with_user(self.encargado_user).create({
                'taxon_id': self.taxon.id,
                'herbarium_id': self.herbarium.id,
            })
        
        # Refrescar usuario
        self.encargado_user._compute_herbario_stats()
        
        self.assertEqual(self.encargado_user.specimens_created_count, 3,
                        "Debe contar 3 especímenes creados")
        
        print(f"✅ Test 5 PASÓ: Stats calculadas: {self.encargado_user.specimens_created_count}")
    
    def test_06_cannot_deactivate_last_encargado(self):
        """Test: No se puede desactivar al último encargado"""
        with self.assertRaises(ValidationError, 
                              msg="No debe poder desactivar último encargado"):
            self.encargado_user.action_deactivate_user()
        
        print(f"✅ Test 6 PASÓ: Protección de último encargado")