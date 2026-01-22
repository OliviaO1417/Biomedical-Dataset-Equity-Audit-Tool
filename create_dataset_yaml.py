import yaml
from pathlib import Path

data = {
    "id": "new_lung_ct",
    "name": "New Lung CT Collection",
    "source": {
        "organization": "National Cancer Institute",
        "url": "https://www.cancerimagingarchive.net/",
        "license": "CC BY 4.0",
    },
    "domain": {
        "modality": "CT",
        "anatomy": "Lung",
        "task": "Diagnosis",
    },
    "cohort": {
        "n_patients": 1243,
        "n_images": 38920,
        "sites": 7,
        "countries": ["US"],
    },
    "demographics": {
        "age": {
            "mean": 63.4,
            "std": 9.8,
            "bins": {
                "0-17": 10,
                "18-39": 54,
                "40-59": 20,
                "60-79": 662,
                "80+": 197,
            },
            "completeness": 0.97,
        },
        "sex": {
            "male": 222,
            "female": 131,
            "unknown": 0,
            "completeness": 1.0,
        },
        "race_ethnicity": {
            "white": 612,
            "black": 113,
            "asian": 44,
            "hispanic": 16,
            "other": 34,
            "unknown": 44,
            "schema": "NIH_OMB_1997",
            "completeness": 0.92,
        },
    },
    "provenance": {
        "derived_from": [
            {
                "publication": "Smith et al. 2021",
                "doi": "10.1234/example",
            }
        ],
        "notes": "Demographics extracted from Table 1 of primary publication.",
    },
}

output_path = Path("datasets/new_lung_ct.yaml")
output_path.parent.mkdir(parents=True, exist_ok=True)

with output_path.open("w") as f:
    yaml.safe_dump(data, f, sort_keys=False)

print("YAML file created at:", output_path)
