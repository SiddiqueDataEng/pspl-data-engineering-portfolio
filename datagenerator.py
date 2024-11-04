# data_generator_pro.py
# Each dataset is saved in ONE randomly assigned format — no duplicate data across formats.
# Datasets: Pakistani social protection beneficiaries + Afghan refugee population.

import os
import random
import sys
import traceback
import pandas as pd
import numpy as np
import json
import pyarrow as pa
import pyarrow.parquet as pq
import avro.schema
import avro.datafile
import avro.io
try:
    import fastavro
    _USE_FASTAVRO = True
except ImportError:
    _USE_FASTAVRO = False
from faker import Faker
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import kagglehub
import warnings

warnings.filterwarnings('ignore')


def _make_faker(locale: str, fallback: str = "en_US") -> Faker:
    try:
        return Faker(locale)
    except AttributeError:
        return Faker(fallback)


# en_PK is not available in all Faker versions; en_US is fine for synthetic portfolio data.
fake_pk = _make_faker("en_PK")
fake_en = Faker("en_US")  # Afghan names (no Dari locale in Faker)

# ============================================================
# CONFIGURATION
# ============================================================
class Config:
    NUM_BENEFICIARIES   = 50000
    NUM_SURVEYS         = 200000
    NUM_INVENTORY       = 5000
    NUM_DONOR_REPORTS   = 2000
    NUM_PAYMENTS        = 100000
    NUM_COMPLAINTS      = 10000
    NUM_AFGHAN_REFUGEES = 30000   # UNHCR-registered Afghan refugees in Pakistan

    # Available output formats — each dataset gets exactly ONE
    FORMATS = ['csv', 'parquet', 'json', 'avro']

    START_DATE = datetime(2020, 1, 1)
    END_DATE   = datetime(2024, 12, 31)

    # Pakistani districts (host communities + refugee-heavy areas)
    DISTRICTS = [
        'Karachi', 'Lahore', 'Peshawar', 'Quetta', 'Multan', 'Faisalabad',
        'Hyderabad', 'Rawalpindi', 'Sukkur', 'Gujranwala', 'Sialkot', 'Bahawalpur',
        'Muzaffargarh', 'Rajanpur', 'Dera Ghazi Khan', 'Layyah', 'Bhakkar', 'Khushab',
        'Tharparkar', 'Umerkot', 'Badin', 'Sanghar', 'Kashmore', 'Shikarpur',
        'Nowshera', 'Swat', 'Mardan', 'Kohat', 'Bannu', 'Dera Ismail Khan',
        'Gwadar', 'Turbat', 'Khuzdar', 'Zhob', 'Loralai',
    ]

    # Districts with significant Afghan refugee presence
    REFUGEE_DISTRICTS = [
        'Peshawar', 'Nowshera', 'Mardan', 'Kohat', 'Bannu',
        'Dera Ismail Khan', 'Swat', 'Quetta', 'Zhob', 'Loralai',
        'Karachi', 'Rawalpindi', 'Islamabad',
    ]

    # Afghan refugee camps / settlements
    REFUGEE_CAMPS = [
        'Nasir Bagh Camp', 'Kacha Gari Camp', 'Jalozai Camp',
        'Azakhel Camp', 'Shamshatoo Camp', 'Surkhab Camp',
        'Girdi Jungle Camp', 'Kuchlak Camp', 'Urban Settlement',
    ]

    AFGHAN_PROVINCES_OF_ORIGIN = [
        'Nangarhar', 'Kunar', 'Laghman', 'Kabul', 'Kandahar',
        'Helmand', 'Kunduz', 'Baghlan', 'Herat', 'Logar',
        'Paktia', 'Khost', 'Ghazni', 'Wardak', 'Badakhshan',
    ]

    PROGRAMS = [
        'BISP - Benazir Income Support',
        'Ehsaas Kafaalat',
        'Ehsaas Langar',
        'Ehsaas Tahafuz',
        'Ehsaas Amdan',
        'Sehat Sahulat Program',
        'Waseela-e-Taleem',
        'Waseela-e-Rozgar',
    ]

    REFUGEE_PROGRAMS = [
        'UNHCR Cash Assistance',
        'WFP Food Voucher',
        'PSPL Livelihood Support',
        'UNICEF Child Protection',
        'NRC Shelter Programme',
        'IOM Voluntary Return',
        'UNHCR Health Referral',
        'Save the Children Education',
    ]

    DONORS = [
        'World Bank', 'DFID', 'Asian Development Bank',
        'Government of Pakistan', 'UNICEF', 'WFP', 'USAID',
        'Islamic Development Bank', 'EU', 'GIZ', 'UNHCR', 'PSPL',
    ]


# ============================================================
# KAGGLE INTEGRATION (optional enrichment)
# ============================================================
def download_kaggle_dataset(dataset_path: str = "bisp-pakistan/beneficiary-data") -> Optional[str]:
    try:
        path = kagglehub.dataset_download(dataset_path)
        print(f"Kaggle dataset downloaded to: {path}")
        return path
    except Exception as e:
        print(f"Kaggle download skipped: {e}. Using synthetic data.")
        return None

def load_kaggle_data(path: Optional[str]) -> Dict[str, pd.DataFrame]:
    if path is None:
        return {}
    data = {}
    for file in os.listdir(path):
        if file.endswith('.csv'):
            df = pd.read_csv(os.path.join(path, file))
            data[file.replace('.csv', '')] = df
            print(f"  Loaded {file}: {len(df)} rows")
    return data


# ============================================================
# FORMAT ASSIGNMENT
# Each dataset gets exactly one format — assigned round-robin
# so all four formats are represented across the portfolio.
# ============================================================
def assign_formats(dataset_names: list) -> Dict[str, str]:
    """
    Assign one output format per dataset.
    Cycles through formats so every format appears at least once.
    """
    formats = Config.FORMATS
    assignment = {}
    for i, name in enumerate(dataset_names):
        assignment[name] = formats[i % len(formats)]
    return assignment


# ============================================================
# CORE GENERATORS
# ============================================================
class DataGenerator:
    def __init__(self, config: Config):
        self.config = config
        self.output_dir = 'data_large'
        os.makedirs(self.output_dir, exist_ok=True)

    # ----------------------------------------------------------
    # Pakistani social protection datasets
    # ----------------------------------------------------------
    def generate_beneficiaries(self) -> pd.DataFrame:
        n = self.config.NUM_BENEFICIARIES
        programs = self.config.PROGRAMS
        weights  = [0.35, 0.25, 0.05, 0.10, 0.05, 0.10, 0.05, 0.05]
        return pd.DataFrame({
            'beneficiary_id':    [fake_pk.uuid4() for _ in range(n)],
            'cnic':              [self._cnic() for _ in range(n)],
            'name':              [fake_pk.name() for _ in range(n)],
            'gender':            [random.choices(['Female', 'Male'], weights=[0.7, 0.3])[0] for _ in range(n)],
            'age':               [random.randint(18, 65) for _ in range(n)],
            'phone':             [self._phone() for _ in range(n)],
            'district':          [random.choice(self.config.DISTRICTS) for _ in range(n)],
            'tehsil':            [fake_pk.city() for _ in range(n)],
            'union_council':     [f"UC-{random.randint(1, 100)}" for _ in range(n)],
            'program':           [random.choices(programs, weights=weights)[0] for _ in range(n)],
            'registration_date': [fake_pk.date_between(start_date='-3y', end_date='today') for _ in range(n)],
            'poverty_score':     [round(random.uniform(0, 100), 2) for _ in range(n)],
            'family_size':       [random.randint(2, 12) for _ in range(n)],
            'is_disabled':       [random.random() < 0.05 for _ in range(n)],
            'is_eligible':       [random.random() < 0.85 for _ in range(n)],
            'bank_account':      [random.choice(['Yes', 'No']) for _ in range(n)],
            'last_payment_date': [fake_pk.date_between(start_date='-1y', end_date='today') for _ in range(n)],
        })

    def generate_payments(self, beneficiaries_df: pd.DataFrame) -> pd.DataFrame:
        n   = self.config.NUM_PAYMENTS
        ids = np.random.choice(beneficiaries_df['beneficiary_id'], n)
        return pd.DataFrame({
            'payment_id':          [fake_pk.uuid4() for _ in range(n)],
            'beneficiary_id':      ids,
            'amount':              [random.randint(2000, 15000) for _ in range(n)],
            'payment_date':        [fake_pk.date_between(start_date='-2y', end_date='today') for _ in range(n)],
            'payment_mode':        [random.choice(['Bank Transfer', 'Cash', 'Mobile Wallet', 'ATM Card']) for _ in range(n)],
            'payment_status':      [random.choices(['Success', 'Failed', 'Pending'], weights=[0.90, 0.07, 0.03])[0] for _ in range(n)],
            'bank_code':           [f"BANK{random.randint(1, 20):02d}" for _ in range(n)],
            'transaction_ref':     [fake_pk.uuid4() for _ in range(n)],
            'disbursement_center': [random.choice(['Karachi Center', 'Lahore Center', 'Peshawar Center', 'Quetta Center']) for _ in range(n)],
        })

    def generate_surveys(self) -> pd.DataFrame:
        n = self.config.NUM_SURVEYS
        metrics = ['meals_served', 'hospital_visits', 'income_generated',
                   'disbursements_received', 'children_enrolled', 'vaccination_doses']
        return pd.DataFrame({
            'survey_id':          [fake_pk.uuid4() for _ in range(n)],
            'beneficiary_id':     [fake_pk.uuid4() for _ in range(n)],
            'survey_date':        [fake_pk.date_between(start_date='-1y', end_date='today') for _ in range(n)],
            'program':            [random.choice(self.config.PROGRAMS) for _ in range(n)],
            'metric_type':        [random.choice(metrics) for _ in range(n)],
            'metric_value':       [random.randint(0, 1000) for _ in range(n)],
            'field_worker':       [fake_pk.name() for _ in range(n)],
            'district':           [random.choice(self.config.DISTRICTS) for _ in range(n)],
            'data_quality_score': [round(random.uniform(0.5, 1.0), 2) for _ in range(n)],
            'is_verified':        [random.random() < 0.8 for _ in range(n)],
        })

    def generate_inventory(self) -> pd.DataFrame:
        n = self.config.NUM_INVENTORY
        return pd.DataFrame({
            'item_id':       [fake_pk.uuid4() for _ in range(n)],
            'item_name':     [fake_pk.word() for _ in range(n)],
            'item_type':     [random.choice(['Food', 'Medicine', 'Cash', 'Stationery', 'Vaccine', 'Equipment']) for _ in range(n)],
            'quantity':      [random.randint(0, 10000) for _ in range(n)],
            'unit':          [random.choice(['kg', 'liters', 'pcs', 'envelopes', 'doses']) for _ in range(n)],
            'warehouse':     [random.choice(['Karachi Central', 'Lahore Hub', 'Peshawar Depot',
                                             'Quetta Storage', 'Sukkur Warehouse']) for _ in range(n)],
            'last_updated':  [fake_pk.date_time_this_year() for _ in range(n)],
            'reorder_level': [random.randint(50, 500) for _ in range(n)],
            'program':       [random.choice(self.config.PROGRAMS) for _ in range(n)],
            'supplier':      [fake_pk.company() for _ in range(n)],
        })

    def generate_complaints(self) -> pd.DataFrame:
        n = self.config.NUM_COMPLAINTS
        categories = ['Payment Delay', 'Wrong Amount', 'Ineligible', 'Missing CNIC',
                      'Harassment', 'Technical Issue', 'Other']
        return pd.DataFrame({
            'complaint_id':    [fake_pk.uuid4() for _ in range(n)],
            'cnic':            [self._cnic() for _ in range(n)],
            'complaint_date':  [fake_pk.date_between(start_date='-1y', end_date='today') for _ in range(n)],
            'category':        [random.choice(categories) for _ in range(n)],
            'description':     [fake_pk.text(max_nb_chars=200) for _ in range(n)],
            'status':          [random.choice(['Open', 'In Progress', 'Resolved', 'Rejected']) for _ in range(n)],
            'resolution_date': [fake_pk.date_between(start_date='-6m', end_date='today')
                                if random.random() < 0.7 else None for _ in range(n)],
            'assigned_to':     [fake_pk.name() for _ in range(n)],
            'district':        [random.choice(self.config.DISTRICTS) for _ in range(n)],
        })

    def generate_donor_reports(self) -> pd.DataFrame:
        n = self.config.NUM_DONOR_REPORTS
        amount_committed = [round(random.uniform(100000, 50000000), 2) for _ in range(n)]
        amount_disbursed = [round(random.uniform(0, c), 2) for c in amount_committed]
        return pd.DataFrame({
            'report_id':        [fake_pk.uuid4() for _ in range(n)],
            'donor':            [random.choice(self.config.DONORS) for _ in range(n)],
            'program':          [random.choice(self.config.PROGRAMS + self.config.REFUGEE_PROGRAMS) for _ in range(n)],
            'district':         [random.choice(self.config.DISTRICTS) for _ in range(n)],
            'amount_committed': amount_committed,
            'amount_disbursed': amount_disbursed,
            'disbursement_date':[fake_pk.date_between(start_date='-2y', end_date='today') for _ in range(n)],
            'currency':         ['PKR' for _ in range(n)],
            'project_code':     [f"PK-{random.randint(1000, 9999)}" for _ in range(n)],
            'reporting_period': [f"Q{random.randint(1,4)} {random.randint(2020, 2024)}" for _ in range(n)],
        })

    # ----------------------------------------------------------
    # Afghan refugee datasets
    # ----------------------------------------------------------
    def generate_afghan_refugees(self) -> pd.DataFrame:
        """
        UNHCR-registered Afghan refugee registry in Pakistan.
        Covers proof-of-registration (PoR) card holders, Afghan Citizen Card (ACC)
        holders, and undocumented populations across KPK and Balochistan.
        """
        n = self.config.NUM_AFGHAN_REFUGEES
        doc_types = ['PoR Card', 'Afghan Citizen Card (ACC)', 'Undocumented', 'Passport']
        doc_weights = [0.45, 0.30, 0.20, 0.05]
        arrival_waves = ['Pre-1979', '1979-1989 (Soviet War)', '1992-1996 (Civil War)',
                         '2001-2010 (Post-9/11)', '2011-2020', '2021+ (Taliban Takeover)']
        arrival_weights = [0.05, 0.25, 0.10, 0.20, 0.15, 0.25]

        return pd.DataFrame({
            'refugee_id':           [fake_en.uuid4() for _ in range(n)],
            'unhcr_case_number':    [f"PAK-{random.randint(100000, 999999)}" for _ in range(n)],
            'name':                 [fake_en.name() for _ in range(n)],
            'gender':               [random.choices(['Male', 'Female'], weights=[0.52, 0.48])[0] for _ in range(n)],
            'age':                  [random.randint(0, 75) for _ in range(n)],
            'province_of_origin':   [random.choice(self.config.AFGHAN_PROVINCES_OF_ORIGIN) for _ in range(n)],
            'arrival_wave':         [random.choices(arrival_waves, weights=arrival_weights)[0] for _ in range(n)],
            'documentation_type':   [random.choices(doc_types, weights=doc_weights)[0] for _ in range(n)],
            'camp_settlement':      [random.choice(self.config.REFUGEE_CAMPS) for _ in range(n)],
            'host_district':        [random.choice(self.config.REFUGEE_DISTRICTS) for _ in range(n)],
            'family_size':          [random.randint(1, 14) for _ in range(n)],
            'vulnerability_score':  [round(random.uniform(0, 10), 2) for _ in range(n)],
            'is_unaccompanied_minor':[random.random() < 0.04 for _ in range(n)],
            'has_disability':       [random.random() < 0.07 for _ in range(n)],
            'enrolled_in_program':  [random.choice(self.config.REFUGEE_PROGRAMS) for _ in range(n)],
            'registration_date':    [fake_en.date_between(start_date='-5y', end_date='today') for _ in range(n)],
            'last_verification':    [fake_en.date_between(start_date='-2y', end_date='today') for _ in range(n)],
            'return_intention':     [random.choices(['Yes', 'No', 'Undecided'], weights=[0.20, 0.45, 0.35])[0] for _ in range(n)],
        })

    def generate_refugee_assistance(self, refugees_df: pd.DataFrame) -> pd.DataFrame:
        """Cash and in-kind assistance transactions for Afghan refugees"""
        n = int(self.config.NUM_AFGHAN_REFUGEES * 1.5)   # ~1.5 transactions per refugee
        ids = np.random.choice(refugees_df['refugee_id'], n)
        modalities = ['Cash Transfer', 'Food Voucher', 'In-Kind Food', 'NFI Kit',
                      'Shelter Grant', 'Education Stipend', 'Health Referral Subsidy']
        return pd.DataFrame({
            'assistance_id':    [fake_en.uuid4() for _ in range(n)],
            'refugee_id':       ids,
            'program':          [random.choice(self.config.REFUGEE_PROGRAMS) for _ in range(n)],
            'modality':         [random.choice(modalities) for _ in range(n)],
            'amount_usd':       [round(random.uniform(10, 500), 2) for _ in range(n)],
            'amount_pkr':       [round(random.uniform(2800, 140000), 2) for _ in range(n)],
            'delivery_date':    [fake_en.date_between(start_date='-2y', end_date='today') for _ in range(n)],
            'delivery_point':   [random.choice(['Camp Distribution', 'Mobile Unit', 'Bank Transfer',
                                                'Hawala', 'Partner NGO']) for _ in range(n)],
            'status':           [random.choices(['Delivered', 'Pending', 'Failed'], weights=[0.88, 0.08, 0.04])[0] for _ in range(n)],
            'implementing_org': [random.choice(['UNHCR', 'WFP', 'PSPL', 'NRC', 'IOM', 'Save the Children']) for _ in range(n)],
            'host_district':    [random.choice(self.config.REFUGEE_DISTRICTS) for _ in range(n)],
        })

    def generate_refugee_protection(self, refugees_df: pd.DataFrame) -> pd.DataFrame:
        """Protection incident and case management records"""
        n = int(self.config.NUM_AFGHAN_REFUGEES * 0.3)   # ~30% have a protection case
        ids = np.random.choice(refugees_df['refugee_id'], n)
        incident_types = ['GBV', 'Child Protection', 'Detention', 'Refoulement Risk',
                          'Documentation Issue', 'Statelessness', 'Family Separation',
                          'Forced Eviction', 'Labour Exploitation']
        return pd.DataFrame({
            'case_id':          [fake_en.uuid4() for _ in range(n)],
            'refugee_id':       ids,
            'incident_type':    [random.choice(incident_types) for _ in range(n)],
            'incident_date':    [fake_en.date_between(start_date='-2y', end_date='today') for _ in range(n)],
            'reported_to':      [random.choice(['UNHCR', 'Police', 'NGO Partner', 'Community Leader', 'Not Reported']) for _ in range(n)],
            'case_status':      [random.choice(['Open', 'Under Review', 'Referred', 'Closed']) for _ in range(n)],
            'risk_level':       [random.choice(['Critical', 'High', 'Medium', 'Low']) for _ in range(n)],
            'host_district':    [random.choice(self.config.REFUGEE_DISTRICTS) for _ in range(n)],
            'case_worker':      [fake_en.name() for _ in range(n)],
            'follow_up_date':   [fake_en.date_between(start_date='-1y', end_date='+3m')
                                 if random.random() < 0.75 else None for _ in range(n)],
        })

    # ----------------------------------------------------------
    # Format writers — one format per dataset
    # ----------------------------------------------------------
    def save_one_format(self, df: pd.DataFrame, name: str, fmt: str):
        """Save dataframe in exactly one format."""
        base = os.path.join(self.output_dir, name)
        if fmt == 'csv':
            df.to_csv(f"{base}.csv.gz", index=False, compression='gzip')
            print(f"  OK {name}.csv.gz  ({len(df):,} rows)")
        elif fmt == 'parquet':
            df.to_parquet(f"{base}.parquet", compression='snappy', index=False)
            print(f"  OK {name}.parquet  ({len(df):,} rows)")
        elif fmt == 'json':
            df.to_json(f"{base}.json", orient='records', lines=True)
            print(f"  OK {name}.json  ({len(df):,} rows)")
        elif fmt == 'avro':
            self._save_avro(df, base)
            print(f"  OK {name}.avro  ({len(df):,} rows)")

    def _save_avro(self, df: pd.DataFrame, base_path: str):
        """Write Avro using fastavro (fast) with robust NA handling."""
        fields = [{"name": col, "type": ["null", "string"]} for col in df.columns]
        schema_dict = {"type": "record", "name": "Record", "fields": fields}

        # Vectorised NA → None, everything else → str
        str_df = df.copy()
        for col in str_df.columns:
            str_df[col] = str_df[col].apply(lambda v: None if pd.isna(v) else str(v))
        records = str_df.to_dict(orient='records')

        if _USE_FASTAVRO:
            parsed = fastavro.parse_schema(schema_dict)
            with open(f"{base_path}.avro", 'wb') as f:
                fastavro.writer(f, parsed, records)
        else:
            schema = avro.schema.parse(json.dumps(schema_dict))
            with open(f"{base_path}.avro", 'wb') as f:
                w = avro.datafile.DataFileWriter(f, avro.io.DatumWriter(), schema)
                for r in records:
                    w.append(r)
                w.close()

    def _cnic(self) -> str:
        return ''.join([str(random.randint(0, 9)) for _ in range(13)])

    def _phone(self) -> str:
        return f"03{random.randint(0,9)}{random.randint(0,9)}-{random.randint(1000000,9999999)}"


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 65)
    print("Pakistan Social Protection + Afghan Refugee Data Generator")
    print("=" * 65)

    kaggle_path = download_kaggle_dataset()
    kaggle_data = load_kaggle_data(kaggle_path)

    gen = DataGenerator(Config())

    # Define all datasets and assign ONE format each (round-robin)
    # Format order: csv → parquet → json → avro → csv → ...
    DATASETS = [
        'beneficiaries',        # csv
        'payments',             # parquet
        'surveys',              # json
        'inventory',            # avro
        'complaints',           # csv
        'donor_reports',        # parquet
        'afghan_refugees',      # json
        'refugee_assistance',   # avro
        'refugee_protection',   # csv
    ]
    fmt_map = assign_formats(DATASETS)

    print("\nFormat assignment (each dataset saved ONCE):")
    for ds, fmt in fmt_map.items():
        print(f"  {ds:<25} -> {fmt}")
    print()

    # ── Pakistani social protection ──────────────────────────
    print("-" * 65)
    print("PAKISTANI SOCIAL PROTECTION")
    print("-" * 65)

    print(f"\n1. Beneficiary Registry  ({Config.NUM_BENEFICIARIES:,} records)")
    beneficiaries = gen.generate_beneficiaries()
    gen.save_one_format(beneficiaries, 'beneficiaries', fmt_map['beneficiaries'])

    print(f"\n2. Payment Transactions  ({Config.NUM_PAYMENTS:,} records)")
    payments = gen.generate_payments(beneficiaries)
    gen.save_one_format(payments, 'payments', fmt_map['payments'])

    print(f"\n3. Field Surveys  ({Config.NUM_SURVEYS:,} records)")
    surveys = gen.generate_surveys()
    gen.save_one_format(surveys, 'surveys', fmt_map['surveys'])

    print(f"\n4. Inventory  ({Config.NUM_INVENTORY:,} records)")
    inventory = gen.generate_inventory()
    gen.save_one_format(inventory, 'inventory', fmt_map['inventory'])

    print(f"\n5. Complaints / Grievances  ({Config.NUM_COMPLAINTS:,} records)")
    complaints = gen.generate_complaints()
    gen.save_one_format(complaints, 'complaints', fmt_map['complaints'])

    print(f"\n6. Donor Reports  ({Config.NUM_DONOR_REPORTS:,} records)")
    donor_reports = gen.generate_donor_reports()
    gen.save_one_format(donor_reports, 'donor_reports', fmt_map['donor_reports'])

    # ── Afghan refugee population ────────────────────────────
    print("\n" + "-" * 65)
    print("AFGHAN REFUGEE POPULATION")
    print("-" * 65)

    print(f"\n7. Afghan Refugee Registry  ({Config.NUM_AFGHAN_REFUGEES:,} records)")
    refugees = gen.generate_afghan_refugees()
    gen.save_one_format(refugees, 'afghan_refugees', fmt_map['afghan_refugees'])

    print(f"\n8. Refugee Assistance Transactions  (~{int(Config.NUM_AFGHAN_REFUGEES*1.5):,} records)")
    refugee_assistance = gen.generate_refugee_assistance(refugees)
    gen.save_one_format(refugee_assistance, 'refugee_assistance', fmt_map['refugee_assistance'])

    print(f"\n9. Refugee Protection Cases  (~{int(Config.NUM_AFGHAN_REFUGEES*0.3):,} records)")
    refugee_protection = gen.generate_refugee_protection(refugees)
    gen.save_one_format(refugee_protection, 'refugee_protection', fmt_map['refugee_protection'])

    # ── Summary ──────────────────────────────────────────────
    files = os.listdir(gen.output_dir)
    total_size = sum(
        os.path.getsize(os.path.join(gen.output_dir, f)) for f in files
    )
    print("\n" + "=" * 65)
    print("GENERATION COMPLETE")
    print("=" * 65)
    print(f"Output directory : {gen.output_dir}/")
    print(f"Total files      : {len(files)}")
    print(f"Total size       : {total_size / (1024*1024):.1f} MB")
    print(f"Formats used     : {', '.join(Config.FORMATS)}")
    if kaggle_data:
        print(f"Kaggle datasets  : {len(kaggle_data)} available for enrichment")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
    except Exception:
        print("ERROR: data generation failed.", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
