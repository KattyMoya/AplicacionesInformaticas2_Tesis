-- ====================================================
-- HT-07.1: OPTIMIZACIÓN CON ÍNDICES
-- ====================================================

-- Índices en herbario_specimen
CREATE INDEX IF NOT EXISTS idx_specimen_codigo 
    ON herbario_specimen(codigo_herbario);

CREATE INDEX IF NOT EXISTS idx_specimen_taxon 
    ON herbario_specimen(taxon_id);

CREATE INDEX IF NOT EXISTS idx_specimen_status 
    ON herbario_specimen(status);

CREATE INDEX IF NOT EXISTS idx_specimen_public 
    ON herbario_specimen(es_publico);

CREATE INDEX IF NOT EXISTS idx_specimen_date 
    ON herbario_specimen(collection_date DESC);

CREATE INDEX IF NOT EXISTS idx_specimen_status_public 
    ON herbario_specimen(status, es_publico);

-- Índices en herbario_taxon
CREATE INDEX IF NOT EXISTS idx_taxon_name 
    ON herbario_taxon(name);

CREATE INDEX IF NOT EXISTS idx_taxon_family 
    ON herbario_taxon(family_id);

-- Índices en herbario_family
CREATE INDEX IF NOT EXISTS idx_family_name 
    ON herbario_family(name);

-- Índices en herbario_collection_site
CREATE INDEX IF NOT EXISTS idx_collection_country_id
    ON herbario_collection_site(country_id);

CREATE INDEX IF NOT EXISTS idx_collection_province_id
    ON herbario_collection_site(province_id);

CREATE INDEX IF NOT EXISTS idx_collection_lower_id
    ON herbario_collection_site(lower_id);

CREATE INDEX IF NOT EXISTS idx_collection_locality_id
    ON herbario_collection_site(locality_id);

CREATE INDEX IF NOT EXISTS idx_collection_vicinity_id
    ON herbario_collection_site(vicinity_id);

CREATE INDEX IF NOT EXISTS idx_collection_specimen
    ON herbario_collection_site(specimen_id);

-- Analizar tablas para actualizar estadísticas
ANALYZE herbario_specimen;
ANALYZE herbario_taxon;
ANALYZE herbario_family;
ANALYZE herbario_collection_site;
ANALYZE herbario_collector;
ANALYZE herbario_author;

-- Reindexar para mejor rendimiento
REINDEX TABLE herbario_specimen;
REINDEX TABLE herbario_taxon;