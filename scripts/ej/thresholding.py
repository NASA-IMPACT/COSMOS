from create_ej_dump import (
    create_cmr_dict,
    load_json_file,
    update_cmr_with_classifications,
)

inferences = load_json_file("cmr-inference.json")
cmr = load_json_file("cmr_collections_umm_20240807_142146.json")

cmr_dict = create_cmr_dict(cmr)

for threshold in [0.5, 0.6, 0.7, 0.8, 0.9]:
    predicted_cmr = update_cmr_with_classifications(inferences=inferences, cmr_dict=cmr_dict, threshold=threshold)
    print(f"Threshold: {int(threshold*100)}%, EJ datasets: {len(predicted_cmr)}")
