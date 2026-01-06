import streamlit as st
from datetime import date
import uuid
import requests
from requests.auth import HTTPBasicAuth
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, XSD


# CONFIGURATION


# HDS CDM namespace from your TTL
HDS = Namespace("http://example.org/hds#")

# Namespace for instances/resources you create
HDS_RES = Namespace("http://example.org/hds/resource/")

# AllegroGraph connection 
ALLEGRO_BASE = "https://ag1g6r37fkqqzppm.allegrograph.cloud/"   # local AllegroGraph
REPOSITORY = "fieldlab1"                  # repo name
ALLEGRO_USER = "admin"                     # AG username
ALLEGRO_PASSWORD = "fc7bJ0vN88xF01yPbJG60Z"                 # AG password

ALLEGRO_STATEMENTS_URL = f"{ALLEGRO_BASE}/repositories/{REPOSITORY}/statements"



# ETL FUNCTIONS (Transform + Load)


def map_age_range_to_age_group(age_range: str) -> str | None:
    """
    Map UI age ranges to CDM hds:ageGroup values.
    CDM allowed: "0-15" "15-25" "25-40" "40-60" "60+"
    UI options: "<18", "18-35", "36-60", "60+"
    """
    if age_range == "<18":
        return "0-15"
    if age_range == "18-35":
        return "25-40"  # approximated
    if age_range == "36-60":
        return "40-60"
    if age_range == "60+":
        return "60+"
    return None


def build_incident_graph(record: dict) -> Graph:
    """
    Transform step:
    - validate required fields
    - map JSON fields to HDS CDM ontology terms
    - build RDF graph for a single incident + victim + location
    """

    # 1. Basic required field check
    required = ["incidentType", "incidentDate", "location"]
    for key in required:
        if key not in record or not str(record[key]).strip():
            raise ValueError(f"Missing required field: {key}")

    # 2. Create RDF graph and bind prefixes
    g = Graph()
    g.bind("hds", HDS)
    g.bind("hds-res", HDS_RES)

    # 3. Create a unique Incident URI
    incident_id = str(uuid.uuid4())
    incident_uri = HDS_RES[f"incident/{incident_id}"]

    # 4. Type triple: Incident
    g.add((incident_uri, RDF.type, HDS.Incident))

    # 5. Add an ID for the incident (hds:id)
    g.add((incident_uri, HDS.id, Literal(incident_id)))

    # 6. Incident type (hds:type) – store the code (e.g. "ex:HealthConcern")
    g.add((incident_uri, HDS.type, Literal(record["incidentType"])))

    # 7. Date (hds:date)
    g.add(
        (
            incident_uri,
            HDS.date,
            Literal(record["incidentDate"], datatype=XSD.date),
        )
    )

    # 8. Description / notes (hds:description) – if provided
    notes = record.get("notes", "").strip()
    if notes:
        g.add((incident_uri, HDS.description, Literal(notes)))

    # 9. Location: create a Location resource and link via hds:location
    location_label = record["location"].strip()
    location_uri = HDS_RES[f"location/{location_label.replace(' ', '_')}"]

    # Type of location
    g.add((location_uri, RDF.type, HDS.Location))
    # Use hds:description for location name/label
    g.add((location_uri, HDS.description, Literal(location_label)))

    # Link Incident -> Location
    g.add((incident_uri, HDS.location, location_uri))

    # 10. Victim node (for gender, ageGroup, household/number)
    # Only create if we have at least one demographic field
    gender = record.get("gender")
    age_range = record.get("ageRange")
    household_size = record.get("householdSize")

    if (gender and gender != "Prefer not to say") or age_range or household_size:
        victim_id = str(uuid.uuid4())
        victim_uri = HDS_RES[f"victim/{victim_id}"]

        # Victim type
        g.add((victim_uri, RDF.type, HDS.Victim))

        # Optionally, ID
        g.add((victim_uri, HDS.id, Literal(victim_id)))

        # Gender: CDM allows "Male", "Female", "Other"
        if gender and gender != "Prefer not to say":
            g.add((victim_uri, HDS.gender, Literal(gender)))

        # Age group
        if age_range:
            age_group = map_age_range_to_age_group(age_range)
            if age_group is not None:
                g.add((victim_uri, HDS.ageGroup, Literal(age_group)))

        # Household size as hds:number (number of affected persons)
        if household_size is not None:
            g.add(
                (
                    victim_uri,
                    HDS.number,
                    Literal(int(household_size), datatype=XSD.integer),
                )
            )

        # Link Incident -> Victim via hds:affected
        g.add((incident_uri, HDS.affected, victim_uri))

    return g


def load_to_allegrograph(graph: Graph):
    """
    Load step:
    Serialize RDF graph to Turtle and POST to AllegroGraph /statements endpoint.
    """
    ttl_data = graph.serialize(format="turtle")

    headers = {"Content-Type": "application/x-turtle"}

    response = requests.post(
        ALLEGRO_STATEMENTS_URL,
        headers=headers,
        data=ttl_data,
        auth=HTTPBasicAuth(ALLEGRO_USER, ALLEGRO_PASSWORD),
    )

    if response.status_code not in (200, 204):
        raise RuntimeError(
            f"Failed to insert data into AllegroGraph "
            f"({response.status_code}): {response.text}"
        )



# STREAMLIT UI

st.set_page_config(
    page_title="FieldLab1 - Refugee Protection Data Entry Prototype",
    layout="centered",
)

st.title("FieldLab1 - Refugee Protection Data Entry Prototype")
st.write(
    "This prototype demonstrates how field staff can securely capture refugee "
    "protection information following FAIR and GDPR principles. All inputs are "
    "validated, mapped to the HDS CDM, transformed into RDF, and stored in a triplestore."
)

# Local controlled vocabulary for incident types (codes + labels)
ONTOLOGY = {
    "ex:PhysicalViolence": "Physical Violence",
    "ex:PsychologicalAbuse": "Psychological Abuse",
    "ex:SexualViolence": "Sexual Violence",
    "ex:Other": "Other / Not Listed",
    "ex:ForcedDisplacement": "Forced Displacement",
    "ex:HealthConcern": "Health Concern",
    "ex:WaterSupplyIssue": "Water Supply Issue",
}

options_display = [f"{code} - {label}" for code, label in ONTOLOGY.items()]

# Section 1: Incident information 
st.subheader("1. Incident Information")
incident_display = st.selectbox("Type of Incident", options=options_display)
incident_code = incident_display.split(" - ")[0]
incident_label = ONTOLOGY[incident_code]

incident_date = st.date_input("Date of Incident", value=date.today())
location = st.text_input("Location of Incident (camp, settlement, region)")

# Section 2: Demographic overview (optional)
st.subheader("2. Demographic Overview (Optional)")
gender = st.selectbox("Gender", ["Prefer not to say", "Female", "Male", "Other"])
age_range = st.selectbox("Age Range", ["<18", "18-35", "36-60", "60+"])
household_size = st.number_input(
    "Household Size (number of affected persons)",
    min_value=1,
    max_value=20,
    step=1,
    value=1,
)

# Section 3: Protection notes
st.subheader("3. Protection Notes")
notes = st.text_area(
    "Detailed Notes on the Incident (max 200 characters)",
    max_chars=200,
    help="Avoid personal names or identifiable information.",
)

st.markdown("---")

# Keep a validated record in session_state
if "validated_record" not in st.session_state:
    st.session_state["validated_record"] = None

# Preview & Validate button
if st.button("Preview and Validate"):
    errors = []
    if not location.strip():
        errors.append("Location of Incident is required.")
    if len(notes) > 200:
        errors.append("Notes exceed the maximum character limit of 200.")

    if errors:
        for e in errors:
            st.session_state["validated_record"] = None
            for e in errors:
                st.error(e)
    else:
        record = {
            "incidentType": incident_code,
            "incidentLabel": incident_label,
            "location": location.strip(),
            "incidentDate": str(incident_date),
            "notes": notes.strip(),
            "gender": gender,
            "ageRange": age_range,
            "householdSize": int(household_size),
        }
        st.session_state["validated_record"] = record

        st.success("✅ Data validated and structured for ETL transformation.")
        st.json(record)
        st.info(
            "Next step: this record will be transformed into RDF using the HDS CDM "
            "and can be loaded into the AllegroGraph triplestore."
        )

st.markdown("---")

# Store in Triplestore (ETL) button
if st.button("Store in Triplestore (ETL)"):
    record = st.session_state.get("validated_record")
    if record is None:
        st.error("Please validate the form first using 'Preview and Validate'.")
    else:
        try:
            g = build_incident_graph(record)
            load_to_allegrograph(g)
            st.success(" Incident successfully stored in AllegroGraph triplestore.")
            st.code(g.serialize(format="turtle").decode("utf-8") if hasattr(g.serialize(format="turtle"), 'decode') else g.serialize(format="turtle"), language="turtle")
        except Exception as e:
            st.error(f"Failed to store data: {e}")

st.caption(
    "FieldLab1 Prototype – FAIR-Compliant User Interface and ETL for Refugee Protection Data "
    "| Leiden University 2025"
)
