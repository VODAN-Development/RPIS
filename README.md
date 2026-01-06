FieldLab1 – Refugee Protection Data Entry Prototype

This repository contains a Streamlit-based prototype developed for the Data Science in Practice (FieldLab) course at Leiden University. The prototype demonstrates how sensitive refugee protection data can be collected, transformed, and stored in a FAIR- and GDPR-aware manner using semantic technologies.

The application provides a simple web interface for recording refugee protection incidents. Data entered through the interface is validated, mapped to a domain ontology (HDS Common Data Model), transformed into RDF, and stored in an AllegroGraph triplestore. The system is designed as a proof-of-concept and focuses on governance, data minimization, interoperability, and reproducibility rather than operational deployment.

Repository contents:
- final_ui.py: main Streamlit application
- README.txt / README.md: project documentation

How to run the application:

1. Requirements:
   - Python 3.10 or higher
   - Internet connection
   - An existing AllegroGraph repository

2. Install required Python packages:
   pip install streamlit rdflib requests

3. Run the application using:
   python -m streamlit run final_ui.py

4. It will open the application in a browser at:
   http://localhost:8501

How the application works:

The application guides the user through a structured data entry process. Users provide information about a protection incident, including the incident type, date, and location. Optional demographic information such as gender, age group, and household size can be added. A short textual description can be entered, limited to 200 characters, and users are explicitly instructed not to include personal identifiers.

When the “Preview and Validate” button is clicked, the application checks that required fields are present and that input constraints are respected. If validation succeeds, a structured record is created and displayed to the user. At this stage, no data is stored.

When the “Store in Triplestore (ETL)” button is clicked, the application performs an ETL process. A unique Incident resource is created, along with associated Location and optional Victim resources. These resources are mapped to the HDS Common Data Model and assembled into an RDF graph using RDFLib. The graph is serialized in Turtle format and uploaded to an AllegroGraph triplestore using the repository’s statements endpoint. Errors during this process are reported directly in the user interface.

Once stored, the data can be queried using SPARQL. For example, all incidents can be retrieved by selecting resources of type hds:Incident and their associated properties such as type, date, and location.

To create a backup of the stored data, the entire repository is exported using a SPARQL CONSTRUCT query that reconstructs all triples in the triplestore. The results are downloaded in Turtle format, producing a complete RDF backup of the repository contents.

Data protection and ethics:

The prototype enforces data minimization by design. No names or direct personal identifiers are collected, and demographic fields are optional. Governance oversight is assumed at the organizational level through a designated Data Protection Officer. The design aligns with GDPR principles and FAIR data practices, demonstrating responsible handling of sensitive humanitarian data.

Academic context:

This project was developed as part of the Data Science in Practice (FieldLab) course at Leiden University in 2025. It serves as a conceptual and technical demonstration rather than a production-ready system.


## Contributing & issue reporting

!UPDATE THE LINKS BELOW TO FIT WITH THIS REPOSITORY.!

For reuse see the [license](https://github.com/VODAN-Development/FAIR-Data-Point/blob/main/LICENSE).
For contributing to this project see the [contributor file](https://github.com/VODAN-Development/FAIR-Data-Point/blob/main/CONTRIBUTING.md).
For issue reporting use the [issue board](https://github.com/VODAN-Development/FAIR-Data-Point/issues).
