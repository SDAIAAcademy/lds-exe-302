# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Check every lab of LDS-EXE-302 and print PASS or the first difference.

    uv run labs/solutions/run_all.py      (from the repository root)

1. The case files are deterministic: the generator, run again, writes the same bytes.
2. Lab 1.1: the test key is spread over the letters; the scorer gives the stand-in sheet its
   scripted score; the dispatch figures recomputed from the CSV agree with the key and the
   confounder holds in every distance band.
3. Lab 1.2: the fallback sheet the lab starts from is the stand-in scored, and is labelled as such.
4. Lab 1.4: the eight credentials parse, use .example issuers, and the reference map agrees with
   their metadata; the rework summary and the three estimates recomputed from the panel agree
   with the key; the programme brief quotes the same figures.
"""
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

SOL = Path(__file__).resolve().parent
LABS = SOL.parent
FILES = LABS / "files"


def digest():
    h = hashlib.sha256()
    for p in sorted(list(FILES.rglob("*")) + [SOL / "key.json", SOL / "standin_answers.csv"]):
        if p.is_file():
            h.update(p.relative_to(LABS).as_posix().encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def rows(name):
    with open(FILES / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def check(cond, what):
    if not cond:
        print("FAIL:", what)
        sys.exit(1)
    print("ok  ", what)


def score_sheet(sheet):
    items = sum(int(r["passed"]) for r in sheet if r["part"] == "test")
    crit = sum(int(r["passed"]) for r in sheet if r["part"] == "takehome")
    return items, crit


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    before = digest()
    subprocess.run([sys.executable, str(LABS / "_tools" / "prepare_data.py")], check=True, stdout=subprocess.DEVNULL)
    check(digest() == before, "the generator writes the same bytes again")
    key = json.loads((SOL / "key.json").read_text(encoding="utf-8"))

    # Lab 1.1
    tk = rows("test_key.csv")
    check(len(tk) == 24, "24 test items in the key")
    spread = {L: sum(1 for r in tk if r["key"] == L) for L in "ABCD"}
    check(max(spread.values()) <= 7, f"test keys spread over the letters {spread}")
    items_md = (FILES / "test_items.md").read_text(encoding="utf-8")
    check(all(f"**{r['item_id']}.**" in items_md for r in tk), "every key item is in test_items.md")
    standin = {r["part_id"]: r["standin_output"] for r in csv.DictReader(open(SOL / "standin_answers.csv", encoding="utf-8"))}
    passed = sum(1 for r in tk if standin[r["item_id"]] == r["key"])
    check(passed == key["standin"]["standin_items_passed"] == 21, f"stand-in scores {passed} of 24 by the key")

    d = rows("dispatch_records.csv")
    check(len(d) == 600, "600 dispatch records in the file")
    seen, clean = set(), []
    for r in d:
        t = tuple(r.values())
        if t not in seen:
            seen.add(t)
            clean.append(r)
    check(len(d) - len(clean) == 12, "12 exact duplicates planted")
    check(sum(1 for r in clean if r["distance_band"] == "") == 9, "9 records without a distance band")
    def late(rs):
        return round(100 * sum(int(r["late"]) for r in rs) / len(rs), 1)
    own = [r for r in clean if r["truck_type"] == "own_fleet"]
    con = [r for r in clean if r["truck_type"] == "contracted"]
    check((late(own), late(con)) == (8.8, 14.9), f"late rates own {late(own)}% and contracted {late(con)}%")
    for band in ("near", "mid", "far"):
        o = late([r for r in own if r["distance_band"] == band])
        c = late([r for r in con if r["distance_band"] == band])
        check(c < o, f"contracted less often late in band {band}: {c}% against {o}%")
        check(o == key["dispatch"]["by_truck"]["own_fleet"]["by_band"][band]["late_pct"], f"band {band} agrees with the key")

    # Lab 1.2
    fb = rows("exposure_sheet_fallback.csv")
    check(score_sheet(fb) == (21, 4), "fallback sheet scores 21 of 24 items and 4 of 6 criteria")
    check(all("ليست نتيجة نموذج" in r["note"] for r in fb), "every fallback row says it is not a model result")
    blank = rows("exposure_sheet.csv")
    check(len(blank) == 30 and all(r["passed"] == "" for r in blank), "blank exposure sheet has 30 empty rows")

    # Lab 1.4: credentials
    meta = {r["credential"]: r for r in rows("credentials_metadata.csv")}
    check(len(meta) == 8, "eight credentials in the metadata")
    for cid in meta:
        cred = json.loads((FILES / "credentials" / f"{cid}.json").read_text(encoding="utf-8"))
        host = cred["issuer"]["id"].split("//")[1]
        check(host.endswith(".example"), f"{cid} issuer is on a reserved .example domain")
        check(("proof" in cred) == (meta[cid]["signed"] == "yes"), f"{cid} signature agrees with the metadata")
        check(("credentialStatus" in cred) == (meta[cid]["status_check"] == "yes"), f"{cid} status agrees with the metadata")
    ref = {r["credential"]: r for r in csv.DictReader(open(SOL / "credential_map_reference.csv", encoding="utf-8"))}
    flagged = sorted(c for c, r in ref.items() if r["over_claim"] == "yes")
    check(flagged == ["C1", "C2", "C3", "C5", "C8"], f"reference over-claims {flagged}")
    check(meta["C6"]["valid_until"] == "2025-12-31" and "2025-12-31" in ref["C6"]["note"], "C6 expiry is noted")
    check(meta["C1"]["signed"] == "no" and ref["C1"]["how_verified"] == "لا شيء", "C1 cannot be verified")

    # Lab 1.4: evaluation
    panel = rows("rework_panel.csv")
    P = [r for r in panel if r["group"] == "participant"]
    C = [r for r in panel if r["group"] == "comparison"]
    m = lambda rs, k: round(sum(float(r[k]) for r in rs) / len(rs), 1)
    summ = {r["group"]: r for r in rows("rework_summary.csv")}
    check(m(P, "rework_before_pct") == float(summ["participant"]["rework_before_pct"]) == key["evaluation"]["p_before"], "participants before agrees")
    check(m(P, "rework_after_pct") == float(summ["participant"]["rework_after_pct"]), "participants after agrees")
    check(m(C, "rework_before_pct") == float(summ["comparison"]["rework_before_pct"]), "comparison before agrees")
    check(m(C, "rework_after_pct") == float(summ["comparison"]["rework_after_pct"]), "comparison after agrees")
    e = key["evaluation"]
    pb, pa, cb, ca = e["p_before"], e["p_after"], e["c_before"], e["c_after"]
    check(round(pa - ca, 1) == -7.0 and round(pa - pb, 1) == -5.2 and round((pa - pb) - (ca - cb), 1) == -2.0,
          f"post-only {round(pa - ca, 1)}, pre-post {round(pa - pb, 1)}, difference in differences {round((pa - pb) - (ca - cb), 1)}")
    check(all(r["nominated_by_manager"] == ("yes" if r["group"] == "participant" else "no") for r in panel), "nomination marks the participants")
    brief = (FILES / "programme_brief.md").read_text(encoding="utf-8")
    for s in (f"{pb}%", f"{pa}%", str(e["reaction_mean"]), "120 موظفًا", "اجتازها 10 منهم"):
        check(s in brief, f"programme brief quotes {s}")
    for c in key["history"]["cohorts"]:
        check(f"| {c['cohort']} | {c['candidates']} | {c['test_passed']} (" in brief, f"brief row for cohort {c['cohort']}")
    sl = key["slides"]
    check(sl["detector"]["expected_false_flags"] == 3.0, "detector example: 3 expected false flags")
    check(sl["cut_score_simulation"]["within_one_sem_of_cut"] == 11, "cut-score simulation: 11 within one SEM")
    print("PASS")


if __name__ == "__main__":
    main()
