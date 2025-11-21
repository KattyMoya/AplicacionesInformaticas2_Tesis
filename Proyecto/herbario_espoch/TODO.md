u# TODO: Fix Specimen Form View Issues

## Step 1: Add author_ids and collector_ids to specimen form view
- [x] Edit views/specimen_views.xml to include author_ids and collector_ids fields in the "Identificación" group.

## Step 2: Modify CollectionSite model to make coordinates direct fields
- [x] Change latitud, longitud, altitud from related readonly to direct Float fields in models/collection_site.py.
- [x] Add compute method for maps_url based on latitud and longitud.

## Step 3: Update specimen views if needed
- [x] Ensure tree editable and form views in specimen_views.xml work with the new direct fields (no readonly issues).
