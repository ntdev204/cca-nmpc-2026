from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import time
from datetime import datetime, timezone

UTC = timezone.utc
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image

from _bootstrap import PROJECT_ROOT


API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "CCA-NMPC-research/0.1 (Wikimedia candidate acquisition; contact pending)"
ALLOWED_LICENSES = ("CC0", "Public domain", "CC BY", "CC BY-SA")
REJECT_TERMS = (
    "ai-generated",
    "artificial intelligence",
    "cartoon",
    "drawing",
    "illustration",
    "mannequin",
    "painting",
    "poster",
    "render",
    "sculpture",
    "statue",
)
GROUPS = (
    {"name": "outdoor_walking", "query": "Person walking in urban sunset", "pageid": 92291208, "expected_people": True, "split": "calibration", "count": 1},
    {"name": "indoor_person", "query": "Back view of a seated person", "pageid": 178901022, "expected_people": True, "split": "test_id", "count": 1},
    {"name": "standing_person", "query": "Person standing on top of canyon wall", "pageid": 160353619, "expected_people": True, "split": "test_id", "count": 1},
    {"name": "crowd_ood", "query": "Walking on a sidewalk", "pageid": 24051851, "expected_people": True, "split": "test_ood", "count": 1},
    {"name": "backlight_ood", "query": "Silhouette of a woman jogging", "pageid": 50090597, "expected_people": True, "split": "test_ood", "count": 1},
    {"name": "empty_indoor", "query": "Empty classroom", "pageid": None, "expected_people": False, "split": "test_id", "count": 1},
    {"name": "empty_outdoor", "query": "Empty street", "pageid": None, "expected_people": False, "split": "test_ood", "count": 1},
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def request_json(params: dict[str, str]) -> dict:
    request = Request(f"{API}?{urlencode(params)}", headers={"User-Agent": USER_AGENT})
    for attempt in range(4):
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            if error.code != 429 or attempt == 3:
                raise
            retry_after = error.headers.get("Retry-After")
            delay = max(2.0, min(30.0, float(retry_after))) if retry_after else 2.0 ** (attempt + 1)
            time.sleep(delay)
    raise RuntimeError("Wikimedia API retry loop ended unexpectedly")


def plain_text(value: str | None) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_allowed_license(short_name: str) -> bool:
    value = short_name.strip()
    return any(value == item or value.startswith(f"{item} ") for item in ALLOWED_LICENSES)


def license_url(short_name: str, supplied: str | None) -> str:
    if supplied and supplied.startswith("http"):
        return supplied
    if short_name.startswith("CC0"):
        return "https://creativecommons.org/publicdomain/zero/1.0/"
    if short_name.startswith("Public domain"):
        return "https://creativecommons.org/publicdomain/mark/1.0/"
    return "https://creativecommons.org/licenses/by-sa/4.0/"


def search_group(group: dict, limit: int) -> list[dict]:
    params = {
        "action": "query",
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata|sha1|timestamp",
        "iiurlwidth": "1280",
        "format": "json",
    }
    if group.get("pageid") is not None:
        params["pageids"] = str(group["pageid"])
    else:
        params.update(
            {
                "generator": "search",
                "gsrsearch": group["query"],
                "gsrnamespace": "6",
                "gsrlimit": str(limit),
            }
        )
    payload = request_json(params)
    pages = payload.get("query", {}).get("pages", {})
    return sorted(pages.values(), key=lambda item: int(item.get("pageid", 0)))


def candidate_text(page: dict) -> str:
    info = page.get("imageinfo", [{}])[0]
    metadata = info.get("extmetadata", {})
    return " ".join(
        [
            page.get("title", ""),
            plain_text(metadata.get("ImageDescription", {}).get("value")),
            plain_text(metadata.get("ObjectName", {}).get("value")),
        ]
    ).lower()


def download(url: str, path: Path) -> None:
    request = Request(url.split("?", 1)[0], headers={"User-Agent": USER_AGENT})
    for attempt in range(4):
        try:
            with urlopen(request, timeout=60) as response:
                path.write_bytes(response.read())
            time.sleep(0.8)
            return
        except HTTPError as error:
            if error.code != 429 or attempt == 3:
                raise
            time.sleep(2.0 ** (attempt + 1))
    raise RuntimeError("Wikimedia download retry loop ended unexpectedly")


def make_record(page: dict, group: dict, path: Path, relative_path: str, retrieved_at: str, index: int) -> dict:
    info = page["imageinfo"][0]
    metadata = info.get("extmetadata", {})
    title = page["title"]
    short_license = plain_text(metadata.get("LicenseShortName", {}).get("value"))
    creator = plain_text(metadata.get("Artist", {}).get("value")) or "Wikimedia Commons creator metadata pending manual review"
    landing_url = f"https://commons.wikimedia.org/wiki/{quote(title, safe=':')}".replace("%3A", ":")
    creator_attribution = f"{creator}; {short_license}; {landing_url}"
    contains_people = bool(group["expected_people"])
    privacy = {
        "contains_people": contains_people,
        "face_handling": "retained_with_basis" if contains_people else "not_applicable",
        "reviewed_at_utc": retrieved_at,
        "notes": "Candidate pre-screen only; final privacy, ethics and identity-free annotation review remains open.",
    }
    if contains_people:
        privacy["ethics_or_legal_basis"] = "Publicly licensed Wikimedia Commons candidate; internal research processing only; no identity or biometric labels; release decision pending."
    split = group["split"]
    asset_id = f"asset-wm-{group['name'].replace('_', '-')}-{index:02d}"
    source_id = f"source-wm-{page['pageid']}"
    return {
        "asset_id": asset_id,
        "source_id": source_id,
        "landing_url": landing_url,
        "download_url": info.get("thumburl") or info["url"],
        "retrieved_at_utc": retrieved_at,
        "http_etag": None,
        "sha256": sha256_file(path),
        "byte_size": path.stat().st_size,
        "mime": info.get("mime", "image/jpeg"),
        "width": Image.open(path).width,
        "height": Image.open(path).height,
        "fps": None,
        "local_relative_path": relative_path,
        "license": {
            "name": short_license,
            "url": license_url(short_license, plain_text(metadata.get("LicenseUrl", {}).get("value"))),
            "checked_at_utc": retrieved_at,
            "download_allowed": True,
            "processing_allowed": True,
            "derivative_annotation_allowed": True,
            "notes": "License metadata read from the Commons file page API; candidate release remains subject to privacy/ethics review.",
        },
        "creator": creator,
        "required_attribution": creator_attribution,
        "source_split_group": source_id,
        "real_media": True,
        "ai_generated": False,
        "redistribution_allowed": True,
        "annotation_status": "pending",
        "reviewer_id": "unassigned-candidate",
        "privacy_review": privacy,
        "split_eligibility": {"split": split, "held_out": True, "approved": False},
        "scene_tags": [
            "candidate",
            "internet",
            group["name"],
            "positive" if contains_people else "negative",
            "person_present" if contains_people else "person_absent",
        ],
    }


def cleanup_failed_output(output: Path) -> None:
    data_root = (PROJECT_ROOT / "data" / "raw").resolve()
    if output == data_root or data_root not in output.parents:
        return
    if output.exists():
        shutil.rmtree(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit-per-query", type=int, default=16)
    args = parser.parse_args()
    if args.limit_per_query < 2:
        raise SystemExit("--limit-per-query must be at least 2")
    output = (PROJECT_ROOT / args.output).resolve()
    data_root = (PROJECT_ROOT / "data" / "raw").resolve()
    if output == data_root or data_root not in output.parents:
        raise SystemExit("output must be a new directory below data/raw")
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"output must be new and empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    image_root = output / "images"
    image_root.mkdir()
    retrieved_at = utc_now()
    records: list[dict] = []
    seen_pageids: set[int] = set()
    selection_log: list[dict] = []
    for group in GROUPS:
        selected = 0
        try:
            pages = search_group(group, args.limit_per_query)
        except Exception:
            cleanup_failed_output(output)
            raise
        for page in pages:
            pageid = int(page.get("pageid", 0))
            info = page.get("imageinfo", [{}])[0]
            short_license = plain_text(info.get("extmetadata", {}).get("LicenseShortName", {}).get("value"))
            mime = str(info.get("mime", ""))
            text = candidate_text(page)
            if pageid in seen_pageids or not mime.startswith("image/") or not is_allowed_license(short_license):
                continue
            if any(term in text for term in REJECT_TERMS):
                continue
            if group["expected_people"] and any(term in text for term in ("dog", "animal", "vehicle")) and "person" not in text:
                continue
            if not group["expected_people"] and any(term in text for term in ("person", "people", "crowd", "pedestrian")):
                continue
            suffix = ".jpg" if mime in {"image/jpeg", "image/jpg"} else ".png"
            path = image_root / f"{group['name']}-{selected + 1:02d}{suffix}"
            try:
                download(info.get("thumburl") or info["url"], path)
                with Image.open(path) as image:
                    image.verify()
                    width, height = image.size
                if width < 160 or height < 120:
                    path.unlink()
                    continue
            except Exception:
                if path.exists():
                    path.unlink()
                continue
            seen_pageids.add(pageid)
            selected += 1
            record = make_record(page, group, path, path.relative_to(PROJECT_ROOT).as_posix(), retrieved_at, selected)
            records.append(record)
            selection_log.append(
                {
                    "group": group["name"],
                    "query": group["query"],
                    "pageid": pageid,
                    "title": page.get("title"),
                    "license": short_license,
                    "landing_url": record["landing_url"],
                }
            )
            if selected >= int(group["count"]):
                break
        if selected < int(group["count"]):
            cleanup_failed_output(output)
            raise SystemExit(f"could not acquire requested count for {group['name']}: {selected}/{group['count']}")
    manifest = {
        "schema_version": "2.0.0",
        "dataset_id": "ds-wikimedia-person-candidate-20260814",
        "created_at_utc": retrieved_at,
        "records": records,
    }
    (output / "web-image-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    acquisition = {
        "schema": "cca-pr10-wikimedia-acquisition-v1",
        "status": "CANDIDATE_NOT_EVIDENCE",
        "created_at_utc": retrieved_at,
        "paper_edit": False,
        "source": "Wikimedia Commons API",
        "api": API,
        "user_agent": USER_AGENT,
        "group_plan": GROUPS,
        "selection": selection_log,
        "record_count": len(records),
        "approved_count": sum(bool(item["split_eligibility"]["approved"]) for item in records),
        "next_gate": "independent blinded annotation, adjudication, privacy/ethics review, detector pretraining-overlap review and held-out expansion",
    }
    (output / "acquisition-record.json").write_text(json.dumps(acquisition, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": acquisition["status"], "output": output.as_posix(), "record_count": len(records)}, indent=2))
    time.sleep(0.1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
