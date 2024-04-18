from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import DocumentTypes

mappings = {
    "solar_system_exploration": DocumentTypes.DOCUMENTATION,
    "igwn_public_alerts_user_guide": DocumentTypes.DOCUMENTATION,
    "land_processes_distributed_active_archive_center": DocumentTypes.DOCUMENTATION,
    "nasa_arcgis_online": DocumentTypes.DOCUMENTATION,
    "global_sulfur_dioxide_monitoring": DocumentTypes.DOCUMENTATION,
    "nasa_applied_sciences": DocumentTypes.DOCUMENTATION,
    "CASEI_Instrument": DocumentTypes.DOCUMENTATION,
    "goddard_institute_for_space_studies": DocumentTypes.DOCUMENTATION,
    "exoplanet_follow_up_observing_program": DocumentTypes.DOCUMENTATION,
    "CEOS_API_I": DocumentTypes.DOCUMENTATION,
    "CASEI_Deployment": DocumentTypes.DOCUMENTATION,
    "ESSCOR_API": DocumentTypes.DOCUMENTATION,
    "GCIS_ARTICLE_API": DocumentTypes.DOCUMENTATION,
    "GCIS_BOOKS_API": DocumentTypes.DOCUMENTATION,
    "GCIS_JOURNAL_API": DocumentTypes.DOCUMENTATION,
    "GCIS_REPORTS_API": DocumentTypes.DOCUMENTATION,
    "CASEI_Platform": DocumentTypes.DOCUMENTATION,
    "PDS_API_Legacy_All": DocumentTypes.DOCUMENTATION,
    "TASKBOOK_Website": DocumentTypes.DOCUMENTATION,
}

for mapping, document_type in mappings.items():
    Collection.objects.filter(config_folder=mapping).update(document_type=mappings[mapping])

Collection.objects.filter(document_type=None)
