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
READY_FOR_PUBLIC_PROD = 13, "Ready for Public Production"
PERFECT_ON_PROD = 14, "Perfect and on Production"
LOW_PRIORITY_PROBLEMS_ON_PROD = 15, "Low Priority Problems on Production"
HIGH_PRIORITY_PROBLEMS_ON_PROD = 16, "High Priority Problems on Production, only for old sources"
MERGE_PENDING = 17, "Code Merge Pending"

perfect = [
    # "WIND_Spacecraft",
    # "gamma_ray_data_tools_core_package",
    # "land_processes_distributed_active_archive_center",
    # "mdscc_deep_space_network",
    # "HelioAnalytics",
    # "nasa_infrared_telescope_facility_irtf",
    # "gmao_fluid",
    # "starchild_a_learning_center_for_young_astronomers",
    # "voyager_Cosmic_Ray_Subsystem",
    "ldas_land_data_assimilatin_system",
    "ppi_node",
]

low_priority = [
    "nasa_applied_sciences",
    "parker_solar_probe",
    "virtual_wave_observatory",
    "explorer_program_acquisition",
    "lisa_consortium",
    "astropy",
    "fermi_at_gsfc",
    "microobservatory_robotic_telescope_network",
]

for config in perfect:
    print(config)
    collection = Collection.objects.get(config_folder=config)
    collection.workflow_status = WorkflowStatusChoices.PERFECT_ON_PROD
    collection.save()

for config in low_priority:
    print(config)
    collection = Collection.objects.get(config_folder=config)
    collection.workflow_status = WorkflowStatusChoices.LOW_PRIORITY_PROBLEMS_ON_PROD
    collection.save()

# for config in perfect:
#     collection = Collection.objects.get(config_folder=config)
#     collection.workflow_status = WorkflowStatusChoices.PERFECT_ON_PROD
#     collection.save()
