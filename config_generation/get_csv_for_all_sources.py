from api import Api
from generate_collection_list import turned_on_remaining_webcrawlers


api = Api("test_server")

dont_ingest_into_webapp = [
    "giss_datasets_and_derived_materials",
    "nasa_sea_level_change",
    "PDS_Missions_Archive_Page_Website",
    "PDS_Venus_Orbital_Data_Explorer_Website",
    "PDS_PDS4_Documents_Website",
    "PDS_Mars_Lander_Data_Website",
    "PDS_Planetary_Science_Tools_Website",
    "PDS_PDS_Documentation_Website",
    "PDS_PDS4_Local_Data_Dictionary_Tool_Website",
    "PDS_Data_Volumes_Index_Website",
    "PDS_Mars_Orbital_Data_Explorer_Website",
    "giss_publication_list",
    "nasa_carbon_monitoring_system",
    "PDS_Mars_Exploration_Program_Website",
    "PDS_PDS_Tool_Registry_Website",
    "ASTRO_NASA_Exoplanet_Archive_Documents_Website",
    "ASTRO_MAST_Documentation_Website",
    "Autoplot_Website",
    "PDS_ISIS_Website",
    "PDS_LOLA_RDR_Query_V20_Website",
    "ASTRO_Data_Reduction_Tools_Website",
    "PDS_Ring",
    "ASTRO_TAP_Search_Website",
    "PDS_Geosciences_Node_Spectral_Library_Website",
    "PDS_SPICE",
    "PDS_DIVINER_RDR_Query_V20_Website",
    "PDS_PDS4_JParser_Website",
    "PDS_Atmospheric_Escape_Chemistry_Page_Website",
    "goddard_institute_for_space_studies",
    "emac_exoplanet_modeling_and_analysis_center",
]

for collection in turned_on_remaining_webcrawlers:
    if collection not in dont_ingest_into_webapp:
        response = api.sql("SMD", collection)
        # TODO: save response['Rows'] to a csv with f'{collection}.xml' as the name
