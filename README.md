# Biomedical-Dataset-Equity-Audit-Tool
This is an early-stage auditing tool for demographic equity in biomedical datasets. Given dataset metadata of demographic characteristics (sex, age, race), it returns summary statistics (e.g. % of patients in each age bracket) within and across, as well as flags for potentially significant representation gaps. Flags are descriptive rather than judgements and indicate potential equity risks.

Flags include the following:
Age
missing_pediatric_population – No patients aged 0–17 reported.


younger_population_underrepresented – Patients under 40 comprise <10% of the cohort.


age_distribution_skewed – A single age bin contains >60% of patients.


Sex
sex_imbalance – One sex represents >70% of the cohort.


single_sex_dataset – One sex represents >90% of the cohort.



Race / Ethnicity
race_majority_dominant – One racial/ethnic group represents >75% of reported patients.


race_group_sparse – One or more groups have fewer than 30 patients.


high_unknown_fraction – >5% of patients have unknown or unreported race/ethnicity.


Data Quality
low_age_completeness – Age completeness <95%.


low_sex_completeness – Sex completeness <99%.


low_race_completeness – Race/ethnicity completeness <95%.


These flags support dataset auditing, transparency, and downstream fairness analysis prior to model development.

Usage:
Dataset metadata can be stored for further processing by entering raw counts for sex, age, and race into create_datasets_yaml.py
Summary statistics and flags for a single dataset can be created by entering the .yaml file created in the previous step into the input field of create_dataset.py
Summary statistics and flags across datasets can be created by entering their .yaml files into the input fields of combine.py


