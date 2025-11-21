from odoo.tests import tagged
from odoo.exceptions import ValidationError
from datetime import date, timedelta
from .common import HerbarioTestCase

@tagged('post_install', '-at_install', 'herbario')
class TestSpecimen(HerbarioTestCase):
    """Tests para el modelo herbario.specimen"""
    
    def test_01_create_specimen_basic(self):
        """Test: Crear espécimen con datos básicos"""
        specimen = self.env['herbario.specimen'].create({
            'taxon_id': self.taxon.id,
            'herbarium_id': self.herbarium.id,
            'collector_ids': [(6, 0, [self.collector.id])],
            'collection_date': date.today(),
        })
        
        # Verificaciones
        self.assertTrue(specimen.id, "El espécimen debe crearse correctamente")
        self.assertTrue(specimen.codigo_herbario.startswith('CHEP-'), 
                       "El código debe empezar con CHEP-")
        self.assertEqual(specimen.nombre_cientifico, 'Baccharis latifolia',
                        "El nombre científico debe obtenerse del taxón")
        self.assertEqual(specimen.status, 'borrador',
                        "El estado inicial debe ser 'borrador'")
        
        print(f"✅ Test 1 PASÓ: Espécimen creado: {specimen.codigo_herbario}")
    
    def test_02_codigo_herbario_unique(self):
        """Test: El código de herbario debe ser único"""
        # Crear primer espécimen
        specimen1 = self.env['herbario.specimen'].create({
            'taxon_id': self.taxon.id,
            'herbarium_id': self.herbarium.id,
        })
        
        # Intentar crear otro con el mismo código debe fallar
        with self.assertRaises(Exception, msg="Debe lanzar error por código duplicado"):
            self.env['herbario.specimen'].create({
                'codigo_herbario': specimen1.codigo_herbario,
                'taxon_id': self.taxon.id,
                'herbarium_id': self.herbarium.id,
            })
        
        print(f"✅ Test 2 PASÓ: Código único validado")
    
    def test_03_codigo_herbario_incremental(self):
        """Test: Los códigos se generan incrementalmente"""
        specimen1 = self.env['herbario.specimen'].create({
            'taxon_id': self.taxon.id,
            'herbarium_id': self.herbarium.id,
        })
        
        specimen2 = self.env['herbario.specimen'].create({
            'taxon_id': self.taxon.id,
            'herbarium_id': self.herbarium.id,
        })
        
        # Extraer números de los códigos
        num1 = int(specimen1.codigo_herbario.split('-')[-1])
        num2 = int(specimen2.codigo_herbario.split('-')[-1])
        
        self.assertEqual(num2, num1 + 1,
                        "El segundo código debe ser el siguiente número")
        
        print(f"✅ Test 3 PASÓ: {specimen1.codigo_herbario} → {specimen2.codigo_herbario}")
    
    def test_04_related_fields_from_taxon(self):
        """Test: Campos relacionados del taxón"""
        specimen = self.env['herbario.specimen'].create({
            'taxon_id': self.taxon.id,
            'herbarium_id': self.herbarium.id,
        })
        
        self.assertEqual(specimen.nombre_cientifico, self.taxon.name)
        self.assertEqual(specimen.familia, self.family.name)
        
        print(f"✅ Test 4 PASÓ: Campos relacionados correctos")
    
    def test_05_audit_log_creation(self):
        """Test: Se crea registro de auditoría al crear espécimen"""
        specimen = self.env['herbario.specimen'].create({
            'taxon_id': self.taxon.id,
            'herbarium_id': self.herbarium.id,
        })
        
        # Buscar log de creación
        audit_log = self.env['herbario.audit.log'].search([
            ('specimen_id', '=', specimen.id),
            ('action_type', '=', 'created')
        ])
        
        self.assertTrue(audit_log, "Debe existir un log de auditoría")
        self.assertEqual(audit_log.user_id, self.env.user)
        
        print(f"✅ Test 5 PASÓ: Auditoría registrada")
    
    def test_06_status_change_tracking(self):
        """Test: Cambios de estado se auditan"""
        specimen = self.env['herbario.specimen'].create({
            'taxon_id': self.taxon.id,
            'herbarium_id': self.herbarium.id,
            'status': 'borrador',
        })
        
        # Cambiar estado
        specimen.write({'status': 'activo'})
        
        # Verificar log de actualización
        audit_log = self.env['herbario.audit.log'].search([
            ('specimen_id', '=', specimen.id),
            ('action_type', '=', 'updated')
        ], limit=1)
        
        self.assertTrue(audit_log, "Debe existir log de actualización")
        
        print(f"✅ Test 6 PASÓ: Cambio de estado auditado")
    
    def test_07_name_get_format(self):
        """Test: Formato del nombre mostrado"""
        specimen = self.env['herbario.specimen'].create({
            'taxon_id': self.taxon.id,
            'herbarium_id': self.herbarium.id,
            'collection_date': date(2024, 6, 15),
        })
        
        name = specimen.name_get()[0][1]
        
        self.assertIn(specimen.codigo_herbario, name)
        self.assertIn('Baccharis latifolia', name)
        self.assertIn('2024-06-15', name)
        
        print(f"✅ Test 7 PASÓ: Formato nombre: {name}")
    
    def test_08_unlink_creates_audit(self):
        """Test: Eliminación crea registro de auditoría"""
        specimen = self.env['herbario.specimen'].create({
            'taxon_id': self.taxon.id,
            'herbarium_id': self.herbarium.id,
        })
        
        specimen_id = specimen.id
        codigo = specimen.codigo_herbario
        
        # Eliminar
        specimen.unlink()
        
        # Verificar log
        audit_log = self.env['herbario.audit.log'].search([
            ('entity_id', '=', specimen_id),
            ('action_type', '=', 'deleted')
        ])
        
        self.assertTrue(audit_log, "Debe existir log de eliminación")
        self.assertIn(codigo, audit_log.description)
        
        print(f"✅ Test 8 PASÓ: Eliminación auditada")