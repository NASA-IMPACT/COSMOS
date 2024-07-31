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
QUALITY_CHECK_FAILED = 12, "Quality Check Failed"
QUALITY_CHECK_PERFECT = 13, "Ready for Public Production"
PROD_PERFECT = 14, "Perfect and on Production"
PROD_MINOR = 15, "Low Priority Problems on Production"
PROD_MAJOR = 16, "High Priority Problems on Production, only for old sources"
MERGE_PENDING = 17, "Code Merge Pending"

perfect = [
    "Van_Allen_Probes",
    "gamma_ray_data_tools_github",
    "hawc_observatory",
    "activate_aerosol_cloud_meteorology_interactions_over_the_western_atlantic_experiment",
    "nasa_visible_earth",
    "global_sulfur_dioxide_monitoring",
    "Voyager_Cosmic_Ray_Subsystem",
    "stereo_at_gsfc",
    "nasa_applied_sciences",
    "cosmic_data_stories",
    "solar_terrestrial_probes_program",
    "atmospheric_imaging_assembly",
    "treasure_map",
    "incus_investigation_of_convective_updrafts",
    "airmoss_airborne_microwave_observatory_of_subcanopy_and_subsurface_at_jpl",
    "cii_hosted_payload_opportunity_online_database",
    "act_america_atmospheric_carbon_and_transport_america",
    "astropy",
    "pds_website",
    "astrophysics_source_code_library",
]

low_priority = [
    "nasa_arcgis_online",
    "physics_of_the_cosmos",
    "dscovr_epic_earth_polychromatic_imaging_camera",
]

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

# for config in perfect:
#     collection = Collection.objects.get(config_folder=config)
#     collection.workflow_status = WorkflowStatusChoices.PROD_PERFECT
#     collection.save()
