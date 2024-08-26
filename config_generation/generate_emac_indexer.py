from db_to_xml import XmlEditor

# collection_metadata
name = "EMAC: Exoplanet Modeling and Analysis Center"
machine_name = "emac_exoplanet_modeling_and_analysis_center"
config_folder = None
url = "https://emac.gsfc.nasa.gov/"
division = "Astrophysics"
update_frequency = "Monthly"
document_type = "Software and Tools"
tree_root = "Astrophysics/Models/EMAC: Exoplanet Modeling and Analysis Center/"

# rule_metadata
URL_EXCLUDES = [
    "https://emac.gsfc.nasa.gov/?related_resource=*",
    "https://emac.gsfc.nasa.gov/news/rss/",
]

TITLE_RULES = [
    {
        "title_criteria": "https://emac.gsfc.nasa.gov/subscriptions/",
        "title_value": "EMAC - Tool Category Subscription",
    },
    {
        "title_criteria": "https://emac.gsfc.nasa.gov/submissions/",
        "title_value": "EMAC - Resource Submission",
    },
    {
        "title_criteria": "https://emac.gsfc.nasa.gov/FAQ/",
        "title_value": "EMAC - Frequently Asked Questions",
    },
    {
        "title_criteria": "https://emac.gsfc.nasa.gov/team/",
        "title_value": "EMAC - Team",
    },
    {
        "title_criteria": "https://emac.gsfc.nasa.gov/developers/",
        "title_value": "EMAC - Software Best Practices and Challenges",
    },
    {
        "title_criteria": "https://emac.gsfc.nasa.gov/workshop/",
        "title_value": "EMAC - Workshop",
    },
    {
        "title_criteria": "https://emac.gsfc.nasa.gov/lightkurve/",
        "title_value": "EMAC - WebApp",
    },
    {
        "title_criteria": "https://emac.gsfc.nasa.gov/?sort=date",
        "title_value": "EMAC - Published Resource List",
    },
    {
        "title_criteria": "https://emac.gsfc.nasa.gov/?cid=*",
        "title_value": """xpath://*[@id="resource_content"]/div[1]/div[1]/div[2]/div""",
    },
    # {
    #     "title_criteria": "https://emac.gsfc.nasa.gov/news/*",
    #     "title_value": """xpath:/html/body/div[6]/div/div[2]/div/div/h1""",
    # },
]

# file saving information
ORIGINAL_CONFIG_PATH = "xmls/scraper_template.xml"

# collection metadata adding
editor = XmlEditor(ORIGINAL_CONFIG_PATH)
editor.convert_scraper_to_indexer()
# editor.add_id()
editor.add_document_type(document_type)
editor.update_or_add_element_value("visibility", "publicCollection")
editor.update_or_add_element_value("Description", f"Webcrawler for the {name}")
editor.update_or_add_element_value("Url", url)
editor.update_or_add_element_value("TreeRoot", tree_root)
editor.update_or_add_element_value("ShardIndexes", "@SMD_ASTRO_Repository_1,@SMD_ASTRO_Repository_2")
editor.update_or_add_element_value("ShardingStrategy", "Balanced")

# rule adding
[editor.add_url_exclude(url) for url in URL_EXCLUDES]
[editor.add_title_mapping(**title_rule) for title_rule in TITLE_RULES]

editor.create_config_folder_and_default("indexing_configs", machine_name)
