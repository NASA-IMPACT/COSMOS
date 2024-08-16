"""
take emily's notes from slack and change the appropriate statuses in the webapp
"""

from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import WorkflowStatusChoices

RESEARCH_IN_PROGRESS = 1, "Research in Progress"
READY_FOR_ENGINEERING = 2, "Ready for Engineering"
ENGINEERING_IN_PROGRESS = 3, "Engineering in Progress"
READY_FOR_CURATION = 4, "Ready for Curation"
CURATION_IN_PROGRESS = 5, "Curation in Progress"
CURATED = 6, "Curated"
QUALITY_FIXED = 7, "Quality Fixed"
SECRET_DEPLOYMENT_STARTED = 8, "Secret Deployment Started"
SECRET_DEPLOYMENT_FAILED = 9, "Secret Deployment Failed"
READY_FOR_LRM_QUALITY_CHECK = 10, "Ready for LRM Quality Check"
READY_FOR_FINAL_QUALITY_CHECK = 11, "Ready for Quality Check"
QUALITY_CHECK_FAILED = 12, "QC: Failed"
QUALITY_CHECK_MINOR = 18, "QC: Minor Issues"
QUALITY_CHECK_PERFECT = 13, "QC: Perfect"
PROD_PERFECT = 14, "Prod: Perfect"
PROD_MINOR = 15, "Prod: Minor Issues"
PROD_MAJOR = 16, "Prod: Major Issues"
MERGE_PENDING = 17, "Code Merge Pending"
NEEDS_DELETE = 19, "Delete from Prod"

ready = []

perfect = [
    "gamma_ray_astrophysics_at_the_nsstc",
    "asteroid_lightcurve_photometry_database",
    "orbital_data_explorer",
    "asdc_misr",
    "ghrc_global_hydrometeorology_resource_center",
    "aurorasaurus_reporting_auroras_from_the_ground_up",
    "hinode_at_msfc",
    "osiris_rex_asteroid_sample_return_mission",
    "sun_climate_powered_by_solar_irradiance",
    "icesat_2_ice_cloud_and_land_elevation_satellite_2",
    "spruce_spruce_and_peatland_responses_under_changing_environments",
    "iasc_international_astronomical_search_collaboration",
    "debit_dynamic_eclipse_broadcast_initiative",
    "astropix",
]

low_priority = [
    "grace_and_grace_fo_groundwater_and_soil_moisture_conditions",
    "NASA_Earth_Observatory",
    "tess_transitioning_exoplanet_survey_satellite",
    "archived_gcn",
    "PDS_Photojournal_Website",
    "neil_gehrel_s_swift_observatory",
]

# for config in ready:
#     collection = Collection.objects.get(config_folder=config)
#     collection.workflow_status = WorkflowStatusChoices.READY_FOR_FINAL_QUALITY_CHECK
#     collection.save()

for config in perfect:
    print(config)
    collection = Collection.objects.get(config_folder=config)
    collection.workflow_status = WorkflowStatusChoices.PROD_PERFECT
    collection.save()

for config in low_priority:
    print(config)
    collection = Collection.objects.get(config_folder=config)
    collection.workflow_status = WorkflowStatusChoices.PROD_MINOR
    collection.save()
