#!/usr/bin/env python3
import asyncio
import sys

sys.path.insert(0, ".")

EXAMPLES = [
    {
        "name": "PT Initial Evaluation",
        "discipline": "PT",
        "regulation": "Documentation must include history, systems review, tests and measures.",
        "common_pitfalls": "Missing treatment plan, lack of goal specificity.",
        "best_practice": "Use SMART goals and link impairments to function.",
        "category": "evaluation",
    },
    {
        "name": "OT Daily Note",
        "discipline": "OT",
        "regulation": "Daily note must support medical necessity and progress.",
        "common_pitfalls": "Copy-paste notes, no measurable progress.",
        "best_practice": "Tie interventions to functional outcomes; quantify assistance levels.",
        "category": "treatment",
    },
    {
        "name": "SLP Plan of Care",
        "discipline": "SLP",
        "regulation": "Plan of care must be signed and include frequency/duration.",
        "common_pitfalls": "Unsigned POC, missing frequency, vague goals.",
        "best_practice": "Ensure MD signature; specify frequency/duration; objective goals.",
        "category": "plan_of_care",
    },
]


async def main() -> int:
    from src.database import init_db
    from src.database.database import get_async_db
    from src.database import crud, schemas

    await init_db()
    async for session in get_async_db():
        created = 0
        for item in EXAMPLES:
            # Idempotent create: check by name
            existing = [r for r in await crud.get_rubrics(session, limit=1000) if r.name == item["name"]]
            if existing:
                continue
            rubric = schemas.RubricCreate(**item)
            await crud.create_rubric(session, rubric)
            created += 1
        print(f"Seeded {created} rubrics (skipped existing)")
        break
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
