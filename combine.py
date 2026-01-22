import yaml
from collections import defaultdict

def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def sum_dicts(*dicts):
    out = defaultdict(float)
    for d in dicts:
        for k, v in d.items():
            if v is not None:
                out[k] += v
    return dict(out)

def completeness_from_counts(counts, total, exclude_keys=None):
    exclude_keys = exclude_keys or []
    reported = sum(
        v for k, v in counts.items()
        if v is not None and k not in exclude_keys
    )
    return round(reported / total, 3) if total else 0


def percentages(counts, total):
    return {k: round((v / total) * 100, 2) if total else 0 for k, v in counts.items()}

def weighted_avg(v1, n1, v2, n2):
    return round((v1 * n1 + v2 * n2) / (n1 + n2), 3)

def combine_yaml(file1, file2):
    y1 = load_yaml(file1)
    y2 = load_yaml(file2)

    n1 = y1["cohort"]["n_patients"]
    n2 = y2["cohort"]["n_patients"]
    total_patients = n1 + n2

    combined = {
        "id": f"{y1['id']}+{y2['id']}",
        "name": f"{y1['name']} + {y2['name']}",
        "source": y1.get("source"),
        "domain": y1.get("domain"),
        "cohort": {
            "n_patients": total_patients,
            "n_images": y1["cohort"].get("n_images", 0) + y2["cohort"].get("n_images", 0),
            "sites": None,
            "countries": sorted(set(
                y1["cohort"].get("countries", []) +
                y2["cohort"].get("countries", [])
            ))
        },
        "demographics": {}
    }

    # ---- AGE ----
    age1 = y1["demographics"]["age"]
    age2 = y2["demographics"]["age"]

    age_bins = sum_dicts(age1["bins"], age2["bins"])

    combined["demographics"]["age"] = {
    "mean": weighted_avg(age1["mean"], n1, age2["mean"], n2),
    "std": weighted_avg(age1["std"], n1, age2["std"], n2),
    "bins": age_bins,
    "percentages": percentages(age_bins, total_patients),
    "completeness": completeness_from_counts(
        age_bins,
        total_patients
    )
}

    # ---- SEX ----
    sex1 = y1["demographics"]["sex"]
    sex2 = y2["demographics"]["sex"]

    sex_counts = sum_dicts(
        {k: v for k, v in sex1.items() if k != "completeness"},
        {k: v for k, v in sex2.items() if k != "completeness"}
    )

    combined["demographics"]["sex"] = {
    **sex_counts,
    "percentages": percentages(sex_counts, total_patients),
    "completeness": completeness_from_counts(
        sex_counts,
        total_patients,
        exclude_keys=["unknown"]
    )
}


    # ---- RACE / ETHNICITY ----
    r1 = y1["demographics"]["race_ethnicity"]
    r2 = y2["demographics"]["race_ethnicity"]

    race_counts = sum_dicts(
        {k: v for k, v in r1.items() if k not in ["schema", "completeness"]},
        {k: v for k, v in r2.items() if k not in ["schema", "completeness"]}
    )

    combined["demographics"]["race_ethnicity"] = {
    **race_counts,
    "percentages": percentages(race_counts, total_patients),
    "schema": r1.get("schema"),
    "completeness": completeness_from_counts(
        race_counts,
        total_patients,
        exclude_keys=["unknown"]
    )
}


    combined["provenance"] = {
        "derived_from": (
            y1.get("provenance", {}).get("derived_from", []) +
            y2.get("provenance", {}).get("derived_from", [])
        ),
        "notes": "Combined demographics from multiple cohorts."
    }

    combined["inequity_flags"] = generate_inequity_flags(
        combined["demographics"],
        total_patients
    )


    return combined

def generate_inequity_flags(demographics, total_patients):
    flags = {
        "age": {},
        "sex": {},
        "race_ethnicity": {},
        "data_quality": {}
    }

    # ---------- AGE FLAGS ----------
    age = demographics["age"]
    bins = age.get("bins", {})

    pediatric = bins.get("0-17", 0) or 0
    younger = sum(v or 0 for k, v in bins.items() if k in ["0-17", "18-39"])

    flags["age"]["missing_pediatric_population"] = pediatric == 0
    flags["age"]["younger_population_underrepresented"] = (
        total_patients > 0 and (younger / total_patients) < 0.10
    )
    flags["age"]["age_distribution_skewed"] = any(
        (v or 0) / total_patients > 0.6 for v in bins.values()
    )

    if age.get("completeness", 1.0) < 0.95:
        flags["data_quality"]["low_age_completeness"] = True

    # ---------- SEX FLAGS ----------
    sex = demographics["sex"]
    male = sex.get("male", 0) or 0
    female = sex.get("female", 0) or 0
    unknown = sex.get("unknown", 0) or 0

    sex_total = male + female + unknown
    max_frac = max(male, female) / sex_total if sex_total else 0

    flags["sex"]["sex_imbalance"] = max_frac > 0.7
    flags["sex"]["single_sex_dataset"] = max_frac > 0.9
    

    if sex.get("completeness", 1.0) < 0.99:
        flags["data_quality"]["low_sex_completeness"] = True

    # ---------- RACE / ETHNICITY FLAGS ----------
    race = demographics["race_ethnicity"]
    race_counts = {
        k: v for k, v in race.items()
        if k not in ["schema", "percentages", "completeness"]
    }

    known_total = sum(v or 0 for k, v in race_counts.items() if k != "unknown")
    largest_group = max(
        (v or 0) for k, v in race_counts.items() if k != "unknown"
    ) if known_total else 0

    flags["race_ethnicity"]["race_majority_dominant"] = (
        known_total > 0 and (largest_group / known_total) > 0.75
    )

    flags["race_ethnicity"]["race_group_sparse"] = {
        k: (v or 0) < 30
        for k, v in race_counts.items()
        if k != "unknown"
    }

    unknown_frac = (race_counts.get("unknown", 0) or 0) / total_patients if total_patients else 0
    flags["race_ethnicity"]["high_unknown_fraction"] = unknown_frac > 0.05

    if race.get("completeness", 1.0) < 0.95:
        flags["data_quality"]["low_race_completeness"] = True

    flags["race_ethnicity"]["non_standard_schema"] = (
        race.get("schema") != "NIH_OMB_1997"
    )

    return flags


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage: python combine.py file1.yaml file2.yaml output.yaml")
        sys.exit(1)

    combined = combine_yaml(sys.argv[1], sys.argv[2])

    with open(sys.argv[3], "w") as f:
        yaml.dump(combined, f, sort_keys=False)

    print(f"Combined file written to {sys.argv[3]}")
