import yaml
from pathlib import Path

INPUT_FILE = Path("datasets/tcia_lung_ct.yaml")
OUTPUT_FILE = Path("datasets/tcia_lung_ct_summary.yaml")

def summarize_category(category_data, total_patients):
    counts = {}
    reported_total = 0

    def process(d):
        nonlocal reported_total
        for k, v in d.items():

            # Explicitly handle age bins
            if k == "bins" and isinstance(v, dict):
                for bin_name, bin_count in v.items():
                    if bin_count is None:
                        continue
                    counts[bin_name] = bin_count
                    reported_total += bin_count
                continue

            # Skip metadata
            if k in {"mean", "std", "schema", "completeness"}:
                continue

            # Count only integer values (people)
            if isinstance(v, int):
                counts[k] = v
                if k.lower() != "unknown":
                    reported_total += v

    process(category_data)

    percentages = {
        k: round((v / total_patients) * 100, 2)
        for k, v in counts.items()
    }

    completeness = round(reported_total / total_patients, 3)

    return {
        "counts": counts,
        "percentages": percentages,
        "completeness": completeness,
    }

def generate_flags(demographics_summary, total_patients):
    flags = {
        "age": {},
        "sex": {},
        "race_ethnicity": {},
        "data_quality": {}
    }

    # ---------- AGE ----------
    age = demographics_summary.get("age", {})
    counts = age.get("counts", {})

    pediatric = counts.get("0-17", 0)
    younger = sum(
        counts.get(k, 0) for k in ["0-17", "18-39"]
    )

    flags["age"]["missing_pediatric_population"] = pediatric == 0
    flags["age"]["younger_population_underrepresented"] = (
        total_patients > 0 and (younger / total_patients) < 0.10
    )

    flags["age"]["age_distribution_skewed"] = any(
        v / total_patients > 0.6 for v in counts.values()
    )

    if age.get("completeness", 1.0) < 0.95:
        flags["data_quality"]["low_age_completeness"] = True

    # ---------- SEX ----------
    sex = demographics_summary.get("sex", {})
    counts = sex.get("counts", {})

    male = counts.get("male", 0)
    female = counts.get("female", 0)
    unknown = counts.get("unknown", 0)
    sex_total = male + female + unknown

    if sex_total:
        max_frac = max(male, female) / sex_total
        flags["sex"]["sex_imbalance"] = max_frac > 0.7
        flags["sex"]["single_sex_dataset"] = max_frac > 0.9
    else:
        flags["sex"]["sex_imbalance"] = False
        flags["sex"]["single_sex_dataset"] = False


    if sex.get("completeness", 1.0) < 0.99:
        flags["data_quality"]["low_sex_completeness"] = True

    # ---------- RACE / ETHNICITY ----------
    race = demographics_summary.get("race_ethnicity", {})
    counts = race.get("counts", {})

    known_counts = {
        k: v for k, v in counts.items() if k != "unknown"
    }

    known_total = sum(known_counts.values())
    largest_group = max(known_counts.values()) if known_counts else 0

    flags["race_ethnicity"]["race_majority_dominant"] = (
        known_total > 0 and (largest_group / known_total) > 0.75
    )

    flags["race_ethnicity"]["race_group_sparse"] = {
        k: v < 30 for k, v in known_counts.items()
    }

    unknown_frac = counts.get("unknown", 0) / total_patients if total_patients else 0
    flags["race_ethnicity"]["high_unknown_fraction"] = unknown_frac > 0.05

    if race.get("completeness", 1.0) < 0.95:
        flags["data_quality"]["low_race_completeness"] = True

    return flags


def main():
    with INPUT_FILE.open() as f:
        data = yaml.safe_load(f)

    total_patients = data["cohort"]["n_patients"]
    demographics = data["demographics"]

    summary = {
        "id": data["id"],
        "name": data["name"],
        "n_patients": total_patients,
        "demographics_summary": {},
    }

    for category_name, category_data in demographics.items():
        # Remove old completeness if present
        category_data = {
            k: v for k, v in category_data.items()
            if k != "completeness"
        }

        summary["demographics_summary"][category_name] = summarize_category(
            category_data,
            total_patients,
        )

    summary["inequity_flags"] = generate_flags(
        summary["demographics_summary"],
        total_patients
    )


    with OUTPUT_FILE.open("w") as f:
        yaml.safe_dump(summary, f, sort_keys=False)

    print("Summary written to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
