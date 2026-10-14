# AquaVision AI — Research Contribution Statement

## Attribution rule

The applicant has confirmed that they were the sole human project lead and that AI tools assisted throughout research and development. The repository proves that technical and research artifacts exist; it does not prove that the GitHub account owner independently authored every artifact. Task-level personal claims must be based on contemporaneous work records and explicit confirmation.

## Verifiable from repository evidence

The project contains verifiable evidence of:

- exact recovery and hashing of 288 historical Sentinel arrays and 288 historical CyAN arrays;
- reconstruction of fixed v2 split membership and High-class support counts;
- an audit showing that historical product, footprint, waterbody, and event identity remains unverified;
- preservation of the validation-selected NDCI failure, post hoc Logistic Regression result, unsuccessful CNNs, and the final LIMITED conclusion;
- an identity-first v3 protocol with explicit scene, waterbody, footprint, time, source-product, and native-cell relationships;
- official acquisition and version verification of six NASA Ocean Color CyAN V6 products;
- CRS transformation, spatial intersection, temporal matching, nearest-neighbor label generation, source/derived hashes, and diagnostic interpolation checks for six Sentinel candidates;
- native-cell deduplication, High-unit qualification, cross-split isolation, confirmation exclusion, and fail-closed tests;
- a bounded twelve-candidate expansion that stopped when nine independent units became arithmetically impossible;
- a documented decision not to train Phase 3B without qualified independent High units.

These are project-level contributions. The sole-human-lead confirmation does not by itself establish unaided authorship or which specific ideas, code, reviews, or decisions originated with the applicant.

## Statements requiring the project owner’s confirmation

Before publication or an application, the owner should verify:

1. Which code, tests, manifests, and reports they personally wrote or materially revised.
2. Whether they designed the geographic audit, v3 identity chain, High-unit rules, candidate budget, and stopping decision.
3. Which NASA Earthdata authentication, download, geospatial verification, and local processing steps they personally carried out.
4. Whether they independently reviewed the six source products, CRS/affine metadata, patch overlays, masks, and High-support records.
5. What work originated from the dataset authors, cited publication, upstream Apache-licensed repository, collaborators, or instructors.
6. Which historical experiments they personally ran and which were inherited artifacts.
7. Which AI-assisted tools were used for code, browser interaction, research design, analysis, tests, or writing.
8. What validation they personally performed on AI-assisted outputs.

## Public data, prior work, and frameworks

- Historical dataset: Zenodo record 14230064, CC BY 4.0.
- NASA CyAN products: NASA Ocean Color / Ocean Biology Processing Group; version and source are preserved per product. Their terms and required attribution remain independent of this repository’s MIT code license.
- Waterbody geometry/identity: USGS public hydrography services and records, as captured in the v3 manifests.
- Sentinel metadata: Copernicus Data Space STAC records; Sentinel product licensing/terms remain applicable.
- Upstream author repository: Apache 2.0, pinned in the README.
- Frameworks: Python, NumPy, Matplotlib, PyYAML, requests, scikit-learn, PyTorch, torchvision, and segmentation-models-pytorch according to source and requirement files.
- Neural models used no downloaded pretrained weights. DeepLabV3/ResNet18 uses `encoder_weights=None` with 12 channels; it is a framework architecture, not a newly invented model.

## Confirmed project-level attribution and AI assistance

The applicant was the sole human project lead. AI tools provided assistance during research and development, including technical discussions, coding, experiment analysis, checking, and documentation. Specific task-level idea attribution and unaided implementation claims are not asserted without supporting evidence.

## Applicant confirmation status

Project-level leadership and broad AI assistance are confirmed. Specific claims about who originated a method, personally wrote particular code, performed a particular check, or completed work without AI assistance remain pending unless supported by contemporaneous evidence and the applicant's explicit confirmation.
