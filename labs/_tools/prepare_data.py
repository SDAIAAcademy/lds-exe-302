# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Write the synthetic case files of LDS-EXE-302 into labs/files/ and the trainer's figures into
labs/solutions/key.json.

    uv run labs/_tools/prepare_data.py        (from the repository root)

Standard library only, fixed seed: the same bytes on every run. Everything is synthetic: the
group, its programme, its staff (codes only, no names), the dispatch records, the issuers of the
sample credentials (on .example domains) and every figure. No identifier has the shape of a
phone number, an identity number, a bank account or a card number.
"""
import csv
import io
import json
import math
import random
import uuid
from pathlib import Path

SEED = 302
LABS = Path(__file__).resolve().parent.parent
FILES = LABS / "files"
SOL = LABS / "solutions"


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def write_csv(path: Path, header, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    write(path, buf.getvalue())


def pct(x, d=1):
    return round(100 * x, d)


# ---------------------------------------------------------------------------------------------
# 1. Programme history: pass rates by cohort (session 1)
# ---------------------------------------------------------------------------------------------
def programme_history(rng):
    # (cohort, candidates, passed the unsupervised online test, passed the take-home case): planted
    # counts, a steady programme until 2025 and a jump in 2026 once assistants were everywhere.
    plan = [
        ("2024-1", 22, 13, 12), ("2024-2", 24, 14, 14),
        ("2025-1", 23, 14, 14), ("2025-2", 24, 16, 15),
        ("2026-1", 20, 18, 19), ("2026-2", 20, 18, 19), ("2026-3", 20, 19, 20),
    ]
    rows, out = [], []
    for cohort, n, test, case in plan:
        rows.append([cohort, n, test, case, pct(test / n), pct(case / n)])
        out.append({"cohort": cohort, "candidates": n, "test_passed": test, "case_passed": case})
    # The spot re-check: the 19 passers of cohort 2026-3 sat a short supervised version of the test.
    recheck_n = 19
    recheck_pass = 10
    write_csv(FILES / "programme_history.csv",
              ["cohort", "candidates", "online_test_passed", "takehome_passed", "online_test_pass_rate_pct", "takehome_pass_rate_pct"],
              rows)
    return {"cohorts": out, "recheck_n": recheck_n, "recheck_passed": recheck_pass}


# ---------------------------------------------------------------------------------------------
# 2. The synthetic online test (24 items) and its key (lab 1.1)
# ---------------------------------------------------------------------------------------------
BRANCHES = [("B1", 420, 38), ("B2", 310, 41), ("B3", 505, 30), ("B4", 150, 27), ("B5", 270, 22), ("B6", 345, 31)]


def test_items():
    total = sum(b[1] for b in BRANCHES)
    late = sum(b[2] for b in BRANCHES)
    rates = {b[0]: b[2] / b[1] for b in BRANCHES}
    overall = late / total
    mean_rates = sum(rates.values()) / len(rates)
    top = max(rates, key=rates.get)
    b4_fixed = (27 - 6) / 150

    table = "\n".join(
        ["| الفرع | الشحنات | المتأخرة |", "|---|---|---|"] + [f"| {b} | {n} | {l} |" for b, n, l in BRANCHES])

    f1 = lambda x: f"{pct(x, 1)}%"
    items = [
        ("Q01", "knowledge", "S-373",
         "أزمنة التسليم في الفرع B2 ملتوية: أغلب الشحنات تصل في يومين، وقليل منها يتأخر أسبوعين. أي مقياس يصف الشحنة المعتادة بأمانة أكبر؟",
         ["الوسيط", "المتوسط الحسابي", "أكبر قيمة", "المدى"], "A"),
        ("Q02", "table", "T-439",
         "من الجدول أعلاه: أي فرع أعلى نسبة تأخر؟",
         ["B2", "B4", "B1", "B6"], "B"),
        ("Q03", "table", "T-437",
         "من الجدول أعلاه: ما نسبة التأخر في الفروع الستة مجتمعة؟",
         [f1(mean_rates), f1(rates[top]), f1(overall), f"{late}"], "C"),
        ("Q04", "knowledge", "T-435",
         "في ملف الشحنات سجلات متطابقة في كل الأعمدة. أي إجراء يكشفها قبل حساب أي نسبة؟",
         ["رسم مدرج تكراري لزمن التسليم", "حساب متوسط كل عمود رقمي", "فحص التكرار على كل الأعمدة معًا", "حذف الأعمدة النصية من الملف"], "C"),
        ("Q05", "knowledge", "A-209",
         "تسعة سجلات بلا نطاق مسافة من 600 سجل. ما الخطوة الأولى الأصح؟",
         ["ملؤها بالقيمة الأكثر تكرارًا دون ذكر ذلك", "معرفة سبب غيابها وذكر عددها في التقرير", "حذف عمود نطاق المسافة كله", "تجاهلها لأنها أقل من 2%"], "B"),
        ("Q06", "knowledge", "T-434",
         "الفروع التي لديها مشرفون أكثر تأخيرها أكثر. ما الاستنتاج المقبول؟",
         ["المشرفون يسببون التأخير", "يجب تقليل المشرفين", "قد يُعيَّن المشرفون حيث يكثر التأخير، فالعلاقة لا تثبت السبب", "لا علاقة بين المتغيرين"], "C"),
        ("Q07", "knowledge", "T-440",
         "اختبار فرق بين طريقتي تحميل أعطى p = 0.03. ما التفسير الصحيح؟",
         ["احتمال أن الطريقتين متساويتان 3%", "لو لم يكن هناك فرق لكان فرق بهذا الحجم أو أكبر نادرًا", "الطريقة الجديدة أفضل بنسبة 97%", "الفرق كبير الأثر عمليًّا"], "B"),
        ("Q08", "knowledge", "T-442",
         "استبانة رضا العملاء وُزعت في مصنع واحد من أربعة. ما المشكلة الأساسية في تعميم نتيجتها؟",
         ["صغر حجم الاستبانة فقط", "العينة لا تمثل عملاء المصانع الأخرى", "الاستبانات لا تقيس الرضا", "الأسئلة مغلقة"], "B"),
        ("Q09", "knowledge", "T-434",
         "النقل المتعاقد أكثر تأخرًا إجمالًا، لكنه أقل تأخرًا في كل نطاق مسافة على حدة. ما التفسير الأرجح؟",
         ["خطأ في البيانات حتمًا", "النقل المتعاقد يأخذ نسبة أكبر من الرحلات البعيدة", "النقل المتعاقد أسوأ في كل الأحوال", "نطاق المسافة لا علاقة له بالتأخر"], "B"),
        ("Q10", "knowledge", "A-211",
         "تريد أن تعرض نسبة التأخر شهرًا بشهر لاثني عشر شهرًا. أي رسم أنسب؟",
         ["رسم دائري", "خط زمني", "رسم مبعثر", "خريطة حرارية للفروع"], "B"),
        ("Q11", "knowledge", "A-209",
         "شحنة واحدة سُجل زمن تسليمها 400 يوم. ما الإجراء الأصح؟",
         ["حذفها دون ذكر", "التحقق من المصدر، ثم تصحيحها أو استبعادها مع ذكر ذلك", "إبقاؤها لأنها بيانات حقيقية", "استبدالها بالمتوسط"], "B"),
        ("Q12", "knowledge", "K-287",
         "قاعدة المجموعة: لا يُدخل مساعد مستضاف إلا ما صُنف «عام». أي ملف يجوز إدخاله؟",
         ["كشف رواتب فريق التوزيع", "عقد شركة نقل متعاقدة بأسعاره", "دليل منشور لمواصفات المنتجات", "سجل شكاوى عملاء بأرقام حساباتهم"], "C"),
        ("Q13", "knowledge", "S-376",
         "تعرض التحليل على مدير التوزيع في خمس دقائق. بماذا تبدأ؟",
         ["منهجية تنظيف البيانات", "القرار المطلوب والرقم الذي يدعمه", "قائمة كل الجداول", "تاريخ جمع البيانات"], "B"),
        ("Q14", "knowledge", "K-286",
         "فرعان يحسبان «التسليم في الموعد» بطريقتين مختلفتين. ما أثر ذلك؟",
         ["لا أثر إن كانت الأرقام قريبة", "المقارنة بين الفرعين غير صالحة حتى يوحَّد التعريف", "يكفي أخذ المتوسط", "يُعتمد تعريف الفرع الأكبر"], "B"),
        ("Q15", "knowledge", "T-440",
         "جُربت طريقة تحميل جديدة على 8 رحلات فقط فانخفض التأخر. ما الحكم؟",
         ["الطريقة ناجحة", "النتيجة واعدة لكن العينة أصغر من أن تحسم", "الطريقة فاشلة", "لا تجوز التجربة"], "B"),
        ("Q16", "knowledge", "S-373",
         "انخفضت نسبة التأخر من 10% إلى 8%. أي وصف صحيح؟",
         ["انخفاض 2% نسبيًّا", "انخفاض نقطتين مئويتين، أي 20% نسبيًّا", "انخفاض 20 نقطة مئوية", "انخفاض 8%"], "B"),
        ("Q17", "knowledge", "T-434",
         "اختير أسوأ ثلاثة فروع في الربع الأول لبرنامج تحسين، فتحسنت في الربع الثاني. ما الذي يجب استبعاده قبل نسبة التحسن إلى البرنامج؟",
         ["العودة الطبيعية نحو المتوسط", "أثر الطقس فقط", "خطأ الطباعة", "لا شيء"], "A"),
        ("Q18", "knowledge", "T-442",
         "تأتي كل الشكاوى المسجلة من القناة الإلكترونية. ماذا يعني ذلك لتحليل أسباب الشكاوى؟",
         ["الشكاوى الهاتفية غير مهمة", "قد يغيب عملاء لا يستخدمون القناة الإلكترونية", "التحليل مكتمل", "القناة الإلكترونية أفضل"], "B"),
        ("Q19", "table", "S-377",
         "من الجدول أعلاه: لو عولجت 6 من شحنات الفرع B4 المتأخرة، كم تصبح نسبة تأخره؟",
         [f1(b4_fixed), f1(rates["B4"]), f1((27 - 6) / (150 - 6)), "4.0%"], "A"),
        ("Q20", "knowledge", "K-284",
         "ما الفائدة الأولى لقاموس البيانات في مشروع تحليل؟",
         ["تسريع الحاسوب", "توحيد معنى كل عمود ومصدره ووحدته", "إخفاء البيانات الشخصية", "تصغير حجم الملف"], "B"),
        ("Q21", "knowledge", "S-371",
         "بعد ربط جدول الشحنات بجدول العملاء تضاعف إجمالي الشحنات. ما السبب الأرجح؟",
         ["العملاء أكثر من الشحنات", "في جدول العملاء أكثر من سطر للعميل الواحد", "الربط يضاعف دائمًا", "خطأ في الحاسوب"], "B"),
        ("Q22", "knowledge", "T-440",
         "ماذا يحدث عادة لعرض فترة الثقة حول نسبة التأخر حين تزيد العينة من 100 إلى 400 شحنة؟",
         ["يتضاعف", "يقل إلى النصف تقريبًا", "لا يتغير", "يقل إلى الربع"], "B"),
        ("Q23", "knowledge", "S-377",
         "أي توصية مبنية على البيانات؟",
         ["إلغاء النقل المتعاقد لأن المدير لا يثق به", "مراجعة توزيع الرحلات البعيدة لأن التأخر يتركز فيها في كل أنواع النقل", "زيادة الشاحنات لأن الطلب سيرتفع", "تغيير المورد لأن سعره أعلى"], "B"),
        ("Q24", "knowledge", "K-283",
         "طلب مدير قائمة السائقين الأكثر تأخرًا بأرقامهم الوظيفية لنشرها في لوحة عامة. ما الرد الأنسب؟",
         ["نشرها كما طُلبت", "تقديم صورة مجمعة بلا أفراد، ومناقشة الهدف قبل أي عرض فردي", "رفض أي تحليل للتأخر", "نشرها دون الأرقام الوظيفية فقط"], "B"),
    ]
    # Spread the keys over the letters: rotate options of chosen items so the key is not mostly B.
    letters = "ABCD"
    target = ["A", "B", "C", "D"] * 6
    rng = random.Random(SEED + 2)
    rng.shuffle(target)
    final = []
    for (iid, kind, code, stem, opts, key), want in zip(items, target):
        k = letters.index(key)
        right = opts[k]
        others = [o for i, o in enumerate(opts) if i != k]
        pos = letters.index(want)
        new = others[:pos] + [right] + others[pos:]
        final.append((iid, kind, code, stem, new, want))

    lines = [
        "# اختبار برنامج «محلل البيانات المعتمد»: النسخة الاصطناعية",
        "",
        "مجموعة صِلِّيان لمواد البناء (جهة افتراضية) · إدارة التعلّم والمواهب",
        "",
        "اختبار عبر الإنترنت غير مراقب، 24 بندًا اختيارًا من متعدد، 40 دقيقة، يُؤدى من البيت. حد الاجتياز 17 من 24.",
        "هذه نسخة اصطناعية للتدريب: كل الأرقام والجهات مخترعة، والملف مصنف «عام».",
        "",
        "## الجدول المستخدم في البنود Q02 وQ03 وQ19",
        "",
        "أداء التسليم في ستة فروع للتوزيع، الربع الثالث:",
        "",
        table,
        "",
        "## البنود",
        "",
    ]
    for iid, kind, code, stem, opts, key in final:
        lines.append(f"**{iid}.** {stem}")
        lines.append("")
        for L, o in zip(letters, opts):
            lines.append(f"- {L}) {o}")
        lines.append("")
    write(FILES / "test_items.md", "\n".join(lines))
    write_csv(FILES / "test_key.csv", ["item_id", "key", "item_type", "role_card_item"],
              [[i, k, kind, code] for i, kind, code, _, _, k in final])
    keys = {i: k for i, _, _, _, _, k in final}
    return {"items": len(final), "keys": keys, "cut": 17,
            "overall_late_pct": pct(overall, 2), "mean_of_rates_pct": pct(mean_rates, 2),
            "top_branch": top, "b4_after_fix_pct": pct(b4_fixed, 1),
            "key_letters": {L: sum(1 for k in keys.values() if k == L) for L in letters}}


# ---------------------------------------------------------------------------------------------
# 3. The take-home case: dispatch records with planted problems (lab 1.1)
# ---------------------------------------------------------------------------------------------
def dispatch(rng):
    plants = ["P1", "P2", "P3", "P4"]
    products = ["gypsum_board", "white_cement", "insulation", "tiles"]
    # Planted counts (trucks, band, records, late): contracted trucks are less often late in every
    # distance band, but take most of the long routes, so they look worse overall (the confounder).
    cells = [("own_fleet", "near", 190, 6), ("own_fleet", "mid", 100, 10), ("own_fleet", "far", 50, 14),
             ("contracted", "near", 50, 1), ("contracted", "mid", 70, 5), ("contracted", "far", 128, 31)]
    recs = []
    for truck, band, n, n_late in cells:
        flags = [1] * n_late + [0] * (n - n_late)
        rng.shuffle(flags)
        recs += [(truck, band, f) for f in flags]
    rng.shuffle(recs)
    rows = []
    for i, (truck, band, late) in enumerate(recs, start=1):
        damaged = 1 if rng.random() < 0.03 else 0
        rows.append([f"D-{i:04d}", 1 + (i * 7) % 12, rng.choice(plants), rng.choice(products), band, truck, late, damaged])
    # planted: nine on-time records with no distance band
    for j in rng.sample([k for k, r in enumerate(rows) if r[6] == 0], 9):
        rows[j][4] = ""
    # planted: twelve exact duplicates (same record id and values), appended in place
    dups = [list(rows[j]) for j in rng.sample(range(len(rows)), 12)]
    for d in dups:
        rows.insert(rng.randrange(len(rows)), d)
    write_csv(FILES / "dispatch_records.csv",
              ["record_id", "week", "plant", "product", "distance_band", "truck_type", "late", "damaged"], rows)

    # figures for the key, computed on the de-duplicated records
    seen, clean = set(), []
    for r in rows:
        t = tuple(r)
        if t in seen:
            continue
        seen.add(t)
        clean.append(r)
    def rate(rs):
        return sum(r[6] for r in rs) / len(rs) if rs else float("nan")
    by = {}
    for truck in ("own_fleet", "contracted"):
        sub = [r for r in clean if r[5] == truck]
        by[truck] = {"n": len(sub), "late_pct": pct(rate(sub), 1),
                     "by_band": {b: {"n": len([r for r in sub if r[4] == b]), "late_pct": pct(rate([r for r in sub if r[4] == b]), 1)}
                                 for b in ("near", "mid", "far")}}
    return {"rows_in_file": len(rows), "duplicates": len(rows) - len(clean), "missing_band": sum(1 for r in clean if r[4] == ""),
            "clean_rows": len(clean), "by_truck": by}


# ---------------------------------------------------------------------------------------------
# 4. The scripted stand-in answer set (not a model run) and the fallback exposure sheet
# ---------------------------------------------------------------------------------------------
def standin(test):
    keys = test["keys"]
    letters = "ABCD"
    # Scripted, not measured: wrong on three items chosen to exercise the scoring.
    wrong = {"Q03", "Q17", "Q21"}
    answers = []
    for iid in sorted(keys):
        k = keys[iid]
        a = letters[(letters.index(k) + 1) % 4] if iid in wrong else k
        answers.append([iid, a])
    criteria = [("C1", 0), ("C2", 1), ("C3", 1), ("C4", 1), ("C5", 0), ("C6", 1)]
    write_csv(SOL / "standin_answers.csv", ["part_id", "standin_output"], answers + [[c, "met" if v else "not met"] for c, v in criteria])
    rows = []
    for iid, a in answers:
        rows.append(["test", iid, a, keys[iid], 1 if a == keys[iid] else 0, "ورقة تمرين من بديل مكتوب، ليست نتيجة نموذج"])
    for c, v in criteria:
        rows.append(["takehome", c, "met" if v else "not met", "rubric", v, "ورقة تمرين من بديل مكتوب، ليست نتيجة نموذج"])
    header = ["part", "id", "model_output", "key_or_rubric", "passed", "note"]
    write_csv(FILES / "exposure_sheet_fallback.csv", header, rows)
    blank = [["test", iid, "", keys[iid], "", ""] for iid in sorted(keys)] + [["takehome", c, "", "rubric", "", ""] for c, _ in criteria]
    write_csv(FILES / "exposure_sheet.csv", header, blank)
    items_passed = sum(r[4] for r in rows if r[0] == "test")
    crit_met = sum(v for _, v in criteria)
    return {"standin_items_passed": items_passed, "standin_criteria_met": crit_met,
            "standin_items_pct": pct(items_passed / 24, 1), "standin_criteria_pct": pct(crit_met / 6, 1)}


# ---------------------------------------------------------------------------------------------
# 5. Eight sample credentials (lab 1.4)
# ---------------------------------------------------------------------------------------------
def credentials(rng):
    def uid():
        while True:
            u = str(uuid.UUID(int=rng.getrandbits(128), version=4))
            # keep every digit run short, so no run looks like a phone, ID or card number
            if max(len(x) for x in "".join(c if c.isdigit() else " " for c in u).split() or [""]) <= 6:
                return f"urn:uuid:{u}"
    ctx = ["https://www.w3.org/ns/credentials/v2", "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json"]
    D_AN = {"type": ["Alignment"], "targetName": "D-AN محلل البيانات", "targetFramework": "إطار المعايير المهنية في البيانات والذكاء الاصطناعي", "targetType": "ext:RoleCard"}
    def T(code, text):
        return {"type": ["Alignment"], "targetName": f"{code} {text}", "targetFramework": "إطار المعايير المهنية في البيانات والذكاء الاصطناعي، البطاقة D-AN", "targetType": "ext:RoleCardItem"}
    proof = lambda: {"type": "DataIntegrityProof", "cryptosuite": "eddsa-rdfc-2022", "proofPurpose": "assertionMethod",
                     "verificationMethod": "#key-1", "proofValue": "z-synthetic-sample-not-a-signature"}
    status = lambda host: {"id": f"https://{host}/status/1#{rng.randrange(1000, 9999)}", "type": "BitstringStatusListEntry", "statusPurpose": "revocation"}

    specs = [
        ("C1", "provider-a.example", "مزوّد تدريب خارجي (أ)", ["VerifiableCredential", "OpenBadgeCredential"], "Certificate",
         "شهادة حضور ندوة «تحليل البيانات في عصر الذكاء الاصطناعي»",
         "تثبت هذه الشهادة إتقان حاملها لتحليل البيانات وأدواته الحديثة.",
         "حضور ندوة مباشرة مدتها 90 دقيقة.", [], None, False, False, "2026-04-12", None),
        ("C2", "learning.silliyan.example", "مجموعة صِلِّيان لمواد البناء، إدارة التعلّم والمواهب", ["VerifiableCredential", "OpenBadgeCredential"], "Certification",
         "محلل بيانات معتمد",
         "يشهد بأن حامله محلل بيانات معتمد يملك الكفاءة المهنية الكاملة لدور محلل البيانات.",
         "إكمال البرنامج ستة أسابيع، واجتياز اختبار عبر الإنترنت غير مراقب (17 من 24)، ودراسة حالة تُنجز في البيت وتُصحح بستة معايير.",
         [D_AN], None, False, True, "2026-06-30", None),
        ("C3", "selfpaced-b.example", "منصة تعلّم ذاتي (ب)", ["VerifiableCredential", "OpenBadgeCredential"], "Certificate",
         "شهادة إنجاز: بناء لوحات المعلومات",
         "يجيد حاملها تصميم لوحات المعلومات وعرض النتائج لأصحاب القرار.",
         "مشاهدة 14 مقطعًا وحل اختبارات قصيرة تُصحح آليًّا بعد كل مقطع، وتُعاد بلا حد.",
         [], None, False, True, "2026-02-03", None),
        ("C4", "skills-c.example", "مزوّد تقييم المهارات (ج)", ["VerifiableCredential", "OpenBadgeCredential"], "MicroCredential",
         "شارة مهارية: عرض نتيجة تحليل على صاحب قرار",
         "أنجز حاملها مهمة واحدة مقيَّمة: عرض نتيجة تحليل وتوصية على صاحب قرار، وناقشها مباشرة.",
         "مشروع موثق بمسوداته يراجعه مقيِّمان، ثم مناقشة مباشرة 15 دقيقة يسأل فيها المقيِّم عن قرارات التحليل. الإفصاح عن أي استخدام للذكاء الاصطناعي شرط في المشروع.",
         [T("T-441", "عرض النتائج على أصحاب القرار")], [{"type": ["Evidence"], "name": "المشروع ومسوداته وتسجيل المناقشة", "id": "https://skills-c.example/evidence/4417"}],
         True, True, "2026-05-20", "2029-05-20"),
        ("C5", "skills-c.example", "مزوّد تقييم المهارات (ج)", ["VerifiableCredential", "OpenBadgeCredential"], "Certificate",
         "شهادة مسار محلل البيانات (ثلاث شارات متراكمة)",
         "يدل اكتمال المسار على كفاءة شاملة في كل مهام محلل البيانات.",
         "جمع ثلاث شارات: شارة العرض (مشروع ومناقشة)، وشارة تنظيف البيانات (مهمة عملية مراقبة)، وشارة المفاهيم الإحصائية (اختبار قصير يُصحح آليًّا غير مراقب).",
         [D_AN], [{"type": ["Evidence"], "name": "روابط الشارات الثلاث", "id": "https://skills-c.example/evidence/5520"}],
         True, True, "2026-07-08", None),
        ("C6", "exams-d.example", "هيئة اختبارات مهنية (د)", ["VerifiableCredential", "OpenBadgeCredential"], "Certification",
         "اجتياز اختبار المفاهيم الإحصائية للتحليل",
         "اجتاز حاملها اختبارًا مراقبًا في مركز اختبار في المفاهيم الإحصائية للتحليل.",
         "اختبار مراقب حضوريًّا مع التحقق من الهوية، 60 بندًا، حد اجتياز منشور.",
         [T("T-440", "مقاييس الدقة واختبار الفرضيات")], None, True, True, "2023-11-15", "2025-12-31"),
        ("C7", "employer-e.example", "شركة صناعية أخرى (هـ)، إدارة الموارد البشرية", ["VerifiableCredential"], None,
         "إفادة عمل: تحليل تأخر الشحنات",
         "نفّذ حامله تحليلًا واحدًا لتأخر الشحنات وقدّمه للإدارة، وراجعه مديره وناقشه فيه.",
         "عمل فعلي في الوظيفة، بمراجعة المدير المباشر ومناقشة مسجلة في ملف الأداء.",
         [T("T-434", "التحليل الاستكشافي والإحصائي")], [{"type": ["Evidence"], "name": "ملخص المراجعة", "id": "https://employer-e.example/evidence/7703"}],
         True, False, "2026-09-01", None),
        ("C8", "remote-f.example", "مزوّد اختبارات عن بُعد (و)", ["VerifiableCredential", "OpenBadgeCredential"], "Badge",
         "خبير تحليل بيانات",
         "حامل هذه الشارة خبير في تحليل البيانات.",
         "اختبار عن بُعد بمراقبة آلية بالكاميرا، يُصحح جزؤه المقالي آليًّا بنموذج لغوي، وتُلغى المحاولة آليًّا عند رصد سلوك مريب.",
         [], None, True, True, "2026-08-19", None),
    ]
    overview = ["# ثماني شهادات نموذجية", "",
                "كل الجهات المصدرة افتراضية، وعناوينها على النطاق المحجوز `.example`. الملفات بصيغة الشهادات القابلة للتحقق "
                "(نموذج بيانات W3C Verifiable Credentials 2.0، ومعه نموذج Open Badges 3.0 حين يكون الملف شارة). التوقيعات في الملفات "
                "رموز تمثيلية وليست توقيعات حقيقية، والتواريخ أيام فقط.", ""]
    meta = []
    for (cid, host, issuer, types, atype, name, desc, crit, align, evidence, signed, has_status, frm, until) in specs:
        cred = {"@context": ctx, "id": uid(), "type": types,
                "issuer": {"id": f"https://{host}", "type": ["Profile"], "name": issuer},
                "validFrom": frm}
        if until:
            cred["validUntil"] = until
        subj = {"type": ["AchievementSubject"] if "OpenBadgeCredential" in types else ["ext:WorkRecord"]}
        ach = {"id": f"https://{host}/achievements/{cid.lower()}", "type": ["Achievement"], "name": name,
               "description": desc, "criteria": {"narrative": crit}}
        if atype:
            ach["achievementType"] = atype
        if align:
            ach["alignment"] = align
        subj["achievement"] = ach
        cred["credentialSubject"] = subj
        if evidence:
            cred["evidence"] = evidence
        if has_status:
            cred["credentialStatus"] = status(host)
        if signed:
            cred["proof"] = proof()
        write(FILES / "credentials" / f"{cid}.json", json.dumps(cred, ensure_ascii=False, indent=2) + "\n")
        overview += [f"## {cid} · {name}", "",
                     f"- **الجهة المصدرة:** {issuer}",
                     f"- **النوع المعلن:** {atype or 'إفادة عمل (ليست شارة)'}",
                     f"- **ما تقوله الشهادة عن حاملها:** {desc}",
                     f"- **معايير المنح:** {crit}",
                     f"- **الربط بالمهارات:** {'نعم: ' + '، '.join(a['targetName'] for a in align) if align else 'لا يوجد'}",
                     f"- **أدلة مرفقة:** {'نعم' if evidence else 'لا'} · **توقيع:** {'نعم' if signed else 'لا'} · **حالة إلغاء قابلة للفحص:** {'نعم' if has_status else 'لا'}",
                     f"- **صالحة من:** {frm}" + (f" · **حتى:** {until}" if until else " · **حتى:** غير محدد"), ""]
        meta.append([cid, issuer, atype or "work_record", "yes" if align else "no", "yes" if evidence else "no",
                     "yes" if signed else "no", "yes" if has_status else "no", frm, until or ""])
    write(FILES / "credentials_overview.md", "\n".join(overview))
    write_csv(FILES / "credentials_metadata.csv",
              ["credential", "issuer", "achievement_type", "skills_alignment", "evidence", "signed", "status_check", "valid_from", "valid_until"], meta)
    write_csv(FILES / "credential_map.csv",
              ["credential", "what_it_evidences", "how_verified", "may_honestly_claim", "over_claim", "note"],
              [[m[0], "", "", "", "", ""] for m in meta])
    return {"credentials": len(specs)}


# ---------------------------------------------------------------------------------------------
# 6. The evaluation data: rework before and after, with selection and a company-wide trend (lab 1.4)
# ---------------------------------------------------------------------------------------------
def evaluation(rng):
    rows = []
    n_part, n_comp = 60, 120
    true_effect, trend = -2.5, -3.0
    for i in range(n_part + n_comp):
        part = i < n_part
        base = rng.gauss(14.0 if part else 18.0, 3.0)  # managers nominated stronger staff
        before = max(1.0, base + rng.gauss(0, 1.5))
        after = max(0.5, base + trend + (true_effect if part else 0.0) + rng.gauss(0, 1.5))
        reaction = round(min(5.0, max(1.0, rng.gauss(4.6, 0.3))), 1) if part else ""
        rows.append([f"E-{1001 + i}", "participant" if part else "comparison",
                     "yes" if part else "no", round(before, 1), round(after, 1), reaction])
    rng.shuffle(rows)
    write_csv(FILES / "rework_panel.csv",
              ["staff_code", "group", "nominated_by_manager", "rework_before_pct", "rework_after_pct", "reaction_score"], rows)
    def mean(xs):
        return sum(xs) / len(xs)
    P = [r for r in rows if r[1] == "participant"]
    C = [r for r in rows if r[1] == "comparison"]
    pb, pa = mean([r[3] for r in P]), mean([r[4] for r in P])
    cb, ca = mean([r[3] for r in C]), mean([r[4] for r in C])
    summ = [["participant", len(P), round(pb, 1), round(pa, 1)], ["comparison", len(C), round(cb, 1), round(ca, 1)]]
    write_csv(FILES / "rework_summary.csv", ["group", "staff", "rework_before_pct", "rework_after_pct"], summ)
    # The estimates are taken from the rounded summary the participants see, so hand arithmetic agrees.
    pb, pa, cb, ca = summ[0][2], summ[0][3], summ[1][2], summ[1][3]
    return {"participants": len(P), "comparison": len(C),
            "p_before": pb, "p_after": pa, "c_before": cb, "c_after": ca,
            "post_only_gap": round(pa - ca, 1), "pre_post_participants": round(pa - pb, 1),
            "did": round((pa - pb) - (ca - cb), 1), "baseline_gap": round(pb - cb, 1),
            "reaction_mean": round(mean([r[5] for r in P]), 2),
            "planted": {"true_effect": true_effect, "trend": trend}}


# ---------------------------------------------------------------------------------------------
# 7. Figures for the slides that are not lab answers (parallel examples, simulations)
# ---------------------------------------------------------------------------------------------
def parallel_and_simulations(rng):
    # 7a. Parallel evaluation example on the slides: a forklift-safety refresher (different
    # department, numbers and outcome). Incidents per 100 operators per quarter.
    ex = {"trained": {"n": 40, "before": 6.0, "after": 3.5}, "untrained": {"n": 80, "before": 8.0, "after": 6.5}}
    ex["post_only_gap"] = round(ex["trained"]["after"] - ex["untrained"]["after"], 1)
    ex["pre_post_trained"] = round(ex["trained"]["after"] - ex["trained"]["before"], 1)
    ex["did"] = round((ex["trained"]["after"] - ex["trained"]["before"]) - (ex["untrained"]["after"] - ex["untrained"]["before"]), 1)

    # 7b. Detector arithmetic at cohort scale (parallel: a procurement-officer test).
    det = {"claimed_fpr": 0.02, "honest_submissions": 150}
    det["expected_false_flags"] = round(det["claimed_fpr"] * det["honest_submissions"], 1)
    det["p_at_least_one"] = round(1 - (1 - det["claimed_fpr"]) ** det["honest_submissions"], 3)

    # 7c. Cut score and reliability: 60 candidates on a 24-item supervised check, cut 17.
    n_items, cut = 24, 17
    diffs = [rng.uniform(-1.5, 1.5) for _ in range(n_items)]
    scores, item_cols = [], [[] for _ in range(n_items)]
    for _ in range(60):
        theta = rng.gauss(0.6, 1.0)
        s = 0
        for j, b in enumerate(diffs):
            x = 1 if rng.random() < 1 / (1 + math.exp(-(theta - b) * 1.2)) else 0
            item_cols[j].append(x)
            s += x
        scores.append(s)
    k = n_items
    pq = sum((sum(c) / len(c)) * (1 - sum(c) / len(c)) for c in item_cols)
    m = sum(scores) / len(scores)
    var = sum((s - m) ** 2 for s in scores) / (len(scores) - 1)
    kr20 = (k / (k - 1)) * (1 - pq / var)
    sem = math.sqrt(var) * math.sqrt(1 - kr20)
    near = sum(1 for s in scores if abs(s - cut) <= sem)
    passed = sum(1 for s in scores if s >= cut)
    cut_sim = {"candidates": 60, "items": n_items, "cut": cut, "mean": round(m, 1), "sd": round(math.sqrt(var), 2),
               "kr20": round(kr20, 2), "sem": round(sem, 2), "within_one_sem_of_cut": near, "passed": passed}
    return {"parallel_evaluation": ex, "detector": det, "cut_score_simulation": cut_sim}


def main():
    rng = random.Random(SEED)
    key = {"seed": SEED}
    key["history"] = programme_history(random.Random(SEED + 1))
    key["test"] = test_items()
    key["dispatch"] = dispatch(random.Random(SEED + 3))
    key["standin"] = standin(key["test"])
    key["credentials"] = credentials(random.Random(SEED + 4))
    key["evaluation"] = evaluation(random.Random(SEED + 5))
    key["slides"] = parallel_and_simulations(random.Random(SEED + 6))
    write(SOL / "key.json", json.dumps(key, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(key, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
