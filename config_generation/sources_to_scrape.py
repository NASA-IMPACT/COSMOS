# this list is read by generate_scrapers when making a list of sources to scrape
test_sources = [
    {"source_name": "quotes", "url": "https://quotes.toscrape.com"},
]

kaylins_new_sources = [
    {"source_name": "nasa_power", "url": "https://power.larc.nasa.gov/"},
    {
        "source_name": "emac_exoplanet_modeling_and_analysis_center",
        "url": "https://emac.gsfc.nasa.gov/",
    },
    {
        "source_name": "goddard_institute_for_space_studies",
        "url": "https://www.giss.nasa.gov/",
    },
    {
        "source_name": "earth_science_decadal_surveys",
        "url": "https://science.nasa.gov/earth-science/decadal-surveys/",
    },
    {
        "source_name": "exoplanet_opacities_database",
        "url": "https://science.data.nasa.gov/opacities/",
    },
    {
        "source_name": "interactive_multiinstrument_database_of_solar_flares",
        "url": "https://data.nas.nasa.gov/helio/portals/solarflares/",
    },
    {"source_name": "general_coordinates_network_gcn", "url": "https://gcn.nasa.gov/"},
    {
        "source_name": "gcn_missions_instruments_and_facilities",
        "url": "https://gcn.nasa.gov/missions",
    },
    {"source_name": "gcn_circulars", "url": "https://gcn.nasa.gov/circulars"},
    {
        "source_name": "igwn_public_alerts_user_guide",
        "url": "https://emfollow.docs.ligo.org/userguide/",
    },
    {
        "source_name": "algorithm_theoretical_basis_documents",
        "url": "https://eospso.nasa.gov/content/algorithm-theoretical-basis-documents",
    },
    {
        "source_name": "eos_mission_page",
        "url": "https://eospso.nasa.gov/content/all-missions",
    },
    {
        "source_name": "earth_observer_publications",
        "url": "https://eospso.nasa.gov/earth-observer-archive/",
    },
    {
        "source_name": "our_changing_planet_the_view_from_space_images",
        "url": "https://eospso.nasa.gov/content/our-changing-planet-view-space",
    },
    {"source_name": "nasa_global_climate_change", "url": "https://climate.nasa.gov/"},
    {"source_name": "giss_publication_list", "url": "https://pubs.giss.nasa.gov/"},
    {"source_name": "giss_software_tools", "url": "https://www.giss.nasa.gov/tools/"},
    {
        "source_name": "giss_datasets_and_derived_materials",
        "url": "https://data.giss.nasa.gov/",
    },
    {
        "source_name": "nasa_wavelength",
        "url": "https://science.nasa.gov/learners/wavelength",
    },
    {"source_name": "my_nasa_data", "url": "https://mynasadata.larc.nasa.gov/"},
    {
        "source_name": "mars_target_encyclopeida_mte",
        "url": "https://github.com/wkiri/MTE",
    },
    {
        "source_name": "astrogeology_analysis_ready_data",
        "url": "https://stac.astrogeology.usgs.gov/docs/",
    },
    {
        "source_name": "nasa_science_missions_earth",
        "url": "https://science.nasa.gov/missions-page?field_division_tid=103&field_phase_tid=All",
    },
    {"source_name": "f_prime", "url": "https://github.com/nasa/fprime"},
    {"source_name": "nasa_sea_level_change", "url": "https://sealevel.nasa.gov/"},
    {"source_name": "earth_observing_dashboard", "url": "https://eodashboard.org/"},
    {
        "source_name": "fire_information_for_resource_management_system_firms",
        "url": "https://firms.modaps.eosdis.nasa.gov/",
    },
    {"source_name": "nasa_carbon_monitoring_system", "url": "https://carbon.nasa.gov/"},
    {
        "source_name": "nasa_2023_climate_strategy",
        "url": "https://www.nasa.gov/sites/default/files/atoms/files/advancing_nasas_climate_strategy_2023.pdf",
    },
]
# i've started running up through igwn
sprint_2_sources = [
    {
        "source_name": "nasa_science_solar_system_exploration",
        "url": "https://solarsystem.nasa.gov/",
    },
    {
        "source_name": "emac_exoplanet_modeling_and_analysis_center",
        "url": "https://emac.gsfc.nasa.gov/",
    },
    {"source_name": "mars_exploration_program", "url": "https://mars.nasa.gov/"},
    {
        "source_name": "astropedia_lunar_and_planetary_cartographic_catalog",
        "url": "https://astrogeology.usgs.gov/search?pmi-target=mercury",
    },
    {
        "source_name": "pds_cassini_resource_page_website",
        "url": "https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/Cassini/Cassini.html",
    },
    {
        "source_name": "goddard_institute_for_space_studies",
        "url": "https://www.giss.nasa.gov/",
    },
    {
        "source_name": "missions_archive_page",
        "url": "https://pds-ppi.igpp.ucla.edu/mission",
    },
    {
        "source_name": "pds_pds_small_bodies_node_asteroid_dust_subnode_website",
        "url": "https://sbn.psi.edu/pds/",
    },
    {
        "source_name": "earth_science_decadal_surveys",
        "url": "https://science.nasa.gov/earth-science/decadal-surveys/",
    },
    {
        "source_name": "exoplanet_opacities_database",
        "url": "https://science.data.nasa.gov/opacities/",
    },
    {"source_name": "nasa_power", "url": "https://power.larc.nasa.gov/"},
    {
        "source_name": "our_changing_planet_the_view_from_space_images",
        "url": "https://eospso.nasa.gov/content/our-changing-planet-view-space",
    },
    {
        "source_name": "igwn_public_alerts_user_guide",
        "url": "https://emfollow.docs.ligo.org/userguide/",
    },
    {"source_name": "nasa_global_climate_change", "url": "https://climate.nasa.gov/"},
    {
        "source_name": "recently_archived_volumes",
        "url": "https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/recent.htm",
    },
    {"source_name": "lsda_website", "url": "https://nlsp.nasa.gov/explore/lsdahome"},
    {
        "source_name": "small_bodies_data_ferret",
        "url": "https://sbnapps.psi.edu/ferret/listDatasets.action",
    },
    {
        "source_name": "pds_data_archive_website",
        "url": "https://pds-imaging.jpl.nasa.gov/data/",
    },
    {
        "source_name": "interactive_multiinstrument_database_of_solar_flares",
        "url": "https://data.nas.nasa.gov/helio/portals/solarflares/",
    },
    {"source_name": "general_coordinates_network_gcn", "url": "https://gcn.nasa.gov/"},
    {
        "source_name": "gcn_missions_instruments_and_facilities",
        "url": "https://gcn.nasa.gov/missions",
    },
    {
        "source_name": "heliophysics_events_knowledgebase",
        "url": "https://www.lmsal.com/hek/",
    },
    {
        "source_name": "planetary_plasma_interactions_data_volumes",
        "url": "https://pds-ppi.igpp.ucla.edu/search/?s=*",
    },
    {
        "source_name": "astromaterials_acquisition_and_curation_office",
        "url": "https://curator.jsc.nasa.gov/",
    },
    {
        "source_name": "nasa_wavelength",
        "url": "https://science.nasa.gov/learners/wavelength",
    },
    {"source_name": "nasa_sea_level_change", "url": "https://sealevel.nasa.gov/"},
]

finished_sources = [
    "algorithm_theoretical_basis_documents",
    "astrogeology_analysis_ready_data",
    "astromaterials_acquisition_and_curation_office",
    "astropedia_lunar_and_planetary_cartographic_catalog",
    "earth_observing_dashboard",
    "earth_science_decadal_surveys",
    "emac_exoplanet_modeling_and_analysis_center",
    "eos_mission_page",
    "exoplanet_opacities_database",
    "fire_information_for_resource_management_system_firms",
    "f_prime",
    "gcn_circulars",
    "gcn_missions_instruments_and_facilities",
    "general_coordinates_network_gcn",
    "giss_datasets_and_derived_materials",
    "giss_publication_list",
    "giss_software_tools",
    "goddard_institute_for_space_studies",
    "heliophysics_events_knowledgebase",
    "igwn_public_alerts_user_guide",
    "nasa_science_earths_moon",
    "pds4_documents",
    "pds_near_earth_asteroid_rendezvous_near_data_archive_website",
    "solar_system_exploration_research_virtual_institute_sservi",
    "SPASE_JSON_List",
]

sprint_3_sources = [
    {
        "source_name": "solar_system_exploration_research_virtual_institute_sservi",
        "url": "https://sservi.nasa.gov/",
    },
    {
        "source_name": "mars_gcm",
        "url": "https://pds-atmospheres.nmsu.edu/PDS/data/mogc_0001",
    },
    {"source_name": "pds_archive_navigator_website", "url": "https://arcnav.psi.edu/"},
    {
        "source_name": "pds_near_earth_asteroid_rendezvous_near_data_archive_website",
        "url": "https://arcnav.psi.edu/urn:nasa:pds:context:investigation:mission.near_earth_asteroid_rendezvous",
    },
    {"source_name": "my_nasa_data", "url": "https://mynasadata.larc.nasa.gov/"},
    {"source_name": "mars_target_encyclopedia", "url": "https://github.com/wkiri/MTE"},
    {
        "source_name": "astrogeology_analysis_ready_data",
        "url": "https://stac.astrogeology.usgs.gov/docs/",
    },
    {"source_name": "heasarc", "url": "https://heasarc.gsfc.nasa.gov/"},
    {"source_name": "nasa_science_earths_moon", "url": "https://moon.nasa.gov/"},
    {
        "source_name": "pds4_documents",
        "url": "https://pds.nasa.gov/datastandards/documents/",
    },
    {"source_name": "code_nasa_api", "url": "https://impact.earthdata.nasa.gov/casei/"},
    {"source_name": "nasa_earth_observations", "url": "https://neo.gsfc.nasa.gov/"},
    {
        "source_name": "nasa_science_missions_earth",
        "url": "https://science.nasa.gov/missions-page?field_division_tid=103&field_phase_tid=All",
    },
    {"source_name": "f_prime", "url": "https://github.com/nasa/fprime"},
    {"source_name": "ceos_missions", "url": "https://mims.nasa-impact.net/docs"},
    {
        "source_name": "caldb_documentation",
        "url": "https://heasarc.gsfc.nasa.gov/docs/heasarc/caldb/caldb_doc.html",
    },
    {
        "source_name": "genelab_metadata_api",
        "url": "https://genelab.nasa.gov/genelabAPIs#metadata",
    },
    {
        "source_name": "generic_kernels",
        "url": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/",
    },
    {"source_name": "casei", "url": "https://impact.earthdata.nasa.gov/casei/"},
    {"source_name": "errata", "url": "https://pds-ppi.igpp.ucla.edu/search/?e="},
    {"source_name": "ceos_instruments", "url": "https://mims.nasa-impact.net/docs"},
    {"source_name": "james_webb_space_telescope", "url": "https://webb.nasa.gov/"},
    {
        "source_name": "casei_instruments",
        "url": "https://admg.nasa-impact.net/api/docs/",
    },
    {
        "source_name": "highenergy_missions",
        "url": "https://heasarc.gsfc.nasa.gov/docs/heasarc/missions/alphabet.html",
    },
    {
        "source_name": "arset_applied_sciences",
        "url": "https://appliedsciences.nasa.gov/join-mission/training",
    },
    {
        "source_name": "casei_deployments",
        "url": "https://admg.nasa-impact.net/api/docs/",
    },
    {
        "source_name": "operational_flightother_project_kernels",
        "url": "https://naif.jpl.nasa.gov/naif/data_operational.html",
    },
    {
        "source_name": "spice_programming_lessons",
        "url": "https://naif.jpl.nasa.gov/naif/lessons.html",
    },
    {
        "source_name": "spice_selftraining",
        "url": "https://naif.jpl.nasa.gov/naif/self_training.html",
    },
    {
        "source_name": "spice_toolkit_documentation",
        "url": "https://naif.jpl.nasa.gov/naif/documentation.html",
    },
    {
        "source_name": "spice_tutorials",
        "url": "https://naif.jpl.nasa.gov/naif/tutorials.html",
    },
    {
        "source_name": "mast_documentation",
        "url": "https://outerspace.stsci.edu/display/MASTDOCS/Portal+Guidel",
    },
    {"source_name": "ccmc", "url": "https://ccmc.gsfc.nasa.gov/"},
    {"source_name": "nasa_carbon_monitoring_system", "url": "https://carbon.nasa.gov/"},
    {
        "source_name": "nasa_2023_climate_strategy",
        "url": "https://www.nasa.gov/sites/default/files/atoms/files/advancing_nasas_climate_strategy_2023.pdf",
    },
    {"source_name": "nasa_sea_level_change", "url": "https://sealevel.nasa.gov/"},
    {"source_name": "earth_observing_dashboard", "url": "https://eodashboard.org/"},
    {"source_name": "earth_observing_dashboard", "url": "https://eodashboard.org/"},
    {
        "source_name": "fire_information_for_resource_management_system_firms",
        "url": "https://firms.modaps.eosdis.nasa.gov/",
    },
]


all_sources = kaylins_new_sources + sprint_2_sources + sprint_3_sources
remaining_sources = [s for s in all_sources if s["source_name"] not in finished_sources]
