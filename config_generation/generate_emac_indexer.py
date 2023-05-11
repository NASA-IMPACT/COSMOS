from db_to_xml import XmlEditor

# collection_metadata
name = "EMAC: Exoplanet Modeling and Analysis Center"
machine_name = "emac_exoplanet_modeling_and_analysis_center"
config_folder = None
url = "https://emac.gsfc.nasa.gov/"
division = "Astrophysics"
update_frequency = "Monthly"
document_type = "Software and Tools"
tree_root = "Astrophysics/Models/EMAC"

# rule_metadata
URL_EXCLUDES = [
    "https://emac.gsfc.nasa.gov/?related_resource=df13b6d8-4670-4fcd-8978-20ec5a419636",
    "https://emac.gsfc.nasa.gov/?related_resource=1fac4c84-9855-4c98-ad96-9851afa631fe",
    "https://emac.gsfc.nasa.gov/?related_resource=7f767d67-67db-4308-973e-2e91cc4cc74b",
    "https://emac.gsfc.nasa.gov/?related_resource=6b2255c2-cde8-46a3-8152-9adcec4f578f",
    "https://emac.gsfc.nasa.gov/?related_resource=9e015de1-f0d6-452b-b740-6862d68ff46a",
    "https://emac.gsfc.nasa.gov/?related_resource=7d08589f-b654-47e8-be3a-ebad9aca2640",
    "https://emac.gsfc.nasa.gov/?related_resource=0f3f0b46-9660-46a6-ba92-f27b75229b6e",
    "https://emac.gsfc.nasa.gov/?related_resource=ce7a2612-986d-430d-a0de-07128c014f5b",
    "https://emac.gsfc.nasa.gov/?related_resource=42435cc7-ba52-460e-93df-fbdc71c9b061",
    "https://emac.gsfc.nasa.gov/?related_resource=2995fe1f-ff3d-4ba3-b951-5d0e63906c7d",
    "https://emac.gsfc.nasa.gov/?related_resource=2eb1dcd2-ae79-459c-a5da-d0a7fd0c9e01",
    "https://emac.gsfc.nasa.gov/?related_resource=24ff76eb-e42d-44e5-af41-a2e4721d35b2",
    "https://emac.gsfc.nasa.gov/?related_resource=d77aeaf0-5d69-455c-8c78-f056ae728f23",
    "https://emac.gsfc.nasa.gov/?related_resource=21ea436a-3c5a-477c-81d8-06549c7bb3b2",
    "https://emac.gsfc.nasa.gov/?related_resource=e430c5de-b542-4a2f-ace9-00333a3f03a4",
    "https://emac.gsfc.nasa.gov/?related_resource=1b3ed3dc-6b84-4717-9f7d-8519236bd12d",
    "https://emac.gsfc.nasa.gov/?related_resource=88f2a333-d081-4bcd-908d-14c4d8cf702f",
    "https://emac.gsfc.nasa.gov/?related_resource=bd857f5b-cc9a-4ae4-a7ad-b2e506e54740",
    "https://emac.gsfc.nasa.gov/?related_resource=417d1844-72d9-4614-b200-9d6f606c0b77",
    "https://emac.gsfc.nasa.gov/?related_resource=c9539dbb-fd84-4eeb-8606-3cb2440edffb",
    "https://emac.gsfc.nasa.gov/?related_resource=a4e1297f-09eb-43ca-9d32-3fec8b322dda",
    "https://emac.gsfc.nasa.gov/?related_resource=479f0b6c-d191-49b3-9066-910cca188e16",
    "https://emac.gsfc.nasa.gov/?related_resource=33f94adf-513f-4d79-8fec-476e6dfaa915",
    "https://emac.gsfc.nasa.gov/?related_resource=da0480c1-32c4-4e8c-9a42-7931d3f4b088",
    "https://emac.gsfc.nasa.gov/?related_resource=6cb8ee25-4d3d-438a-aad6-29f0ddb011ac",
    "https://emac.gsfc.nasa.gov/?related_resource=f56dff02-56b6-4374-84d6-cb59abf48602",
    "https://emac.gsfc.nasa.gov/?related_resource=a87ea5c0-1647-4936-85ee-3f629fe3b6a5",
    "https://emac.gsfc.nasa.gov/?related_resource=d25fc293-8ad8-49a3-af8e-ddf86dc34acc",
    "https://emac.gsfc.nasa.gov/?related_resource=0e6e852b-8bfe-4213-98c5-4136cad15c98",
    "https://emac.gsfc.nasa.gov/?related_resource=b4ed2732-f128-4962-84f2-9aab960140f0",
    "https://emac.gsfc.nasa.gov/?related_resource=6602dbe5-e5d8-43e2-8816-2e062bc7f033",
    "https://emac.gsfc.nasa.gov/?related_resource=2266c18c-f059-40e3-9c54-960cb423f4ac",
    "https://emac.gsfc.nasa.gov/?related_resource=e6b635b8-53c3-43ac-9ff4-63c47b8fe19c",
    "https://emac.gsfc.nasa.gov/?related_resource=6e4f684a-cfa0-45db-90fa-23f2a38f582f",
    "https://emac.gsfc.nasa.gov/?related_resource=6fdbe6b7-ea6c-4ad3-8c16-8cf4a5fa97ca",
    "https://emac.gsfc.nasa.gov/?related_resource=8ef3e9d0-05a4-4e6a-ba0b-c0139b186676",
    "https://emac.gsfc.nasa.gov/?related_resource=16158121-c49b-4f61-b918-4222fe0d4076",
    "https://emac.gsfc.nasa.gov/?related_resource=765ab561-a499-45b2-862c-7f5b6d0f6fa0",
    "https://emac.gsfc.nasa.gov/?related_resource=f476b21b-8365-49f3-97ab-0f19785affef",
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
        "title_value": """xpath://*[@id="resource_content"]/div[3]/div/div[1]/div[2]/p[1]/text()""",
    },
    {
        "title_criteria": "https://emac.gsfc.nasa.gov/news/*",
        "title_value": """xpath:/html/body/div[6]/div/div[2]/div/div/h1""",
    },
]

# file saving information
ORIGINAL_CONFIG_PATH = "xmls/scraper_template.xml"

# collection metadata adding
editor = XmlEditor(ORIGINAL_CONFIG_PATH)
editor.convert_scraper_to_indexer()
editor.add_id()
editor.add_document_type(document_type)
editor.update_or_add_element_value("Description", f"Webcrawler for the {name}")
editor.update_or_add_element_value("Url", url)
editor.update_or_add_element_value("TreeRoot", tree_root)

# rule adding
[editor.add_url_exclude(url) for url in URL_EXCLUDES]
[editor.add_title_mapping(**title_rule) for title_rule in TITLE_RULES]

editor.create_config_folder_and_default("indexing_configs", machine_name)
