---
type: dataset-screening-note
status: screening
evidence_status: publisher-landing-screen
screened_date: 2026-08-13
paper_edit: prohibited
---

# Dataset candidates for real context and overlay — 2026

This note records dataset candidates found during a Google-oriented and
Google-Scholar-oriented discovery pass. It is not an admission or a result
package. Any candidate must be converted to the direct CSV/JSON contract before
it can enter the active pipeline; the runtime remains middleware-free.

## Candidate comparison

| Candidate | What the primary page indicates | Scope decision |
|---|---|---|
| [Oxford Indoor Human Motion Dataset](https://ori.ox.ac.uk/publications/datasets/oxford-indoor-human-motion-dataset-2024) | Robot-mounted and static RGB-D views, motion-capture human/robot state, maps, and approximately 60 minutes of recordings; the official page identifies the raw release as rosbag | Reference candidate only unless the maintainers provide a permitted direct CSV/JSON export; rosbag is not admissible in the active pipeline |
| [JRDB/JRDB-Pose](https://jrdb.erc.monash.edu/dataset/) | Egocentric robot scenes, indoor/outdoor sequences, dense human pose/head annotations, and trajectory resources | Strong OOD/perception candidate; account and CC BY-NC-SA terms must be checked before acquisition |
| [SiT Dataset](https://github.com/SPALaboratory/SiT-Dataset) | Socially interactive robot data with detection/tracking/prediction resources; the page states CC BY-NC-ND 4.0 and a Husky/ROS Melodic setup | Not active until a permitted non-ROS extraction and derivative-data terms are explicitly approved |
| [NavWareSet](https://anr-navware.github.io/navwareset/) | Official page describes robot/participant pose CSVs, occupancy JSON, annotated point clouds, RGB-D/video/LiDAR recordings and seven social-navigation scenarios; the processed `x_poses.zip` product is a direct CSV/JSON route | Strong candidate for metric context/map diagnostics. Raw robot/GRS recordings are ROS bags, so only processed CSV/JSON products fit the current no-ROS scope; camera-frame overlay and license/redistribution terms still require verification |
| [uB-VisioGeoloc](https://doi.org/10.1016/j.dib.2024.110088) | CC-licensed RGB-D image sequences with inertial/geolocation metadata from a pedestrian viewpoint | Auxiliary perception/context source, not a robot-view primary dataset |

## Decision for the active protocol

The first admissible route is the user's own final robot capture. Oxford-IHM
remains a useful reference and becomes admissible only if an authorized direct
export into `robot_state.csv`, `context.csv`, `events.csv` and `map.json` is
available without processing or replaying rosbag. JRDB is a possible external
OOD route after account and license approval. SiT is not silently imported
because its public description explicitly references ROS and a no-derivatives
license.

## Protocol continuation — robot-view context sources — 2026-08-13

The official NavWareSet page reports over 172 minutes of annotated trajectories,
robot and participant positions, occupancy grids and multimodal recordings. Its
processed pose product is structurally close to the active `context.csv` and
`map.json` contract, but the public raw sensor products are ROS bags. The
current study does not ingest, replay or retain ROS/ROS2/rosbag artifacts; a
processed CSV/JSON-only route would still need image-frame hashes, calibration,
license/derivative review and an independent reference audit before PR11 can
move beyond `DRAFT-DESIGN`. A read-only GitHub API check on 2026-08-13 found no
machine-readable license record for the linked tutorial repository; the
website's CC BY-SA statement applies to the website and is not treated as a
dataset redistribution grant.

JRDB is a second robot-view candidate with real RGB/LiDAR video, persistent
person tracks and pose annotations. The official site requires an account for
download and publishes the dataset under CC BY-NC-SA 3.0. Until access and a
permitted direct export are confirmed, JRDB remains screening-only and cannot
be used to train or evaluate the active LSTM.

No candidate is currently frozen, trained on, or used to create an LSTM overlay.
The previous ten-image Internet smoke cohort and the earlier eight-image
package were purged; they cannot supply temporal velocity or direction labels.
A new licensed cohort remains an acquisition task, not active evidence.

## Required checks before admission

- access and license snapshot, including derivative/redistribution permission;
- source/site/group split and near-duplicate audit;
- direct non-ROS export with timestamp/frame/coordinate provenance;
- sensor calibration and robot-frame transform audit;
- independent context labels or motion-capture reference;
- held-out ID/OOD split frozen before LSTM selection;
- parent hashes for every image/context overlay.

## Links

[[03_Literature/source-index]] · [[03_Literature/web-verified-gap-sources]] ·
[[06_Methods/dataset-sources]] · [[06_Methods/lstm-protocol]] ·
[[06_Methods/final-run-data-package]] · [[00_MOC/project-map]]
