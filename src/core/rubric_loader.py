import asyncio
import logging
from pathlib import Path

from rdflib import Graph, Namespace
from rdflib.namespace import RDF
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import AsyncSessionLocal, Base
from ..database import engine as async_engine
from ..database.models import Rubric

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
# Define the namespace from the TTL files
NS = Namespace("http://example.com/speckit/ontology#")


async def parse_and_load_rubrics(db_session: AsyncSession, rubric_files: list[Path]):
    """Parses TTL files, extracts compliance rules, and loads them into the database.
    It checks for existing rules by name to prevent duplicates.
    """
    logger.info("Starting rubric loading from %s files...", len(rubric_files))

    g = Graph()
    for file_path in rubric_files:
        try:
            g.parse(str(file_path), format="turtle")
            logger.info("Successfully parsed %s", file_path.name)
        except (FileNotFoundError, PermissionError, OSError):
            logger.error("Failed to parse %s: {e}", file_path.name, exc_info=True)
            continue

    # SPARQL query to find all subjects that are of type :ComplianceRule
    rules = g.subjects(predicate=RDF.type, object=NS.ComplianceRule)

    rules_to_add = []
    names_to_add = set()  # Track names to prevent duplicates within the same batch

    for rule_uri in rules:
        # Extract properties for each rule
        name_node = g.value(subject=rule_uri, predicate=NS.hasIssueTitle)
        content_node = g.value(subject=rule_uri, predicate=NS.hasIssueDetail)
        category_node = g.value(subject=rule_uri, predicate=NS.hasDiscipline)

        if not all([name_node, content_node]):
            logger.warning("Skipping rule %s due to missing name or content.", rule_uri)
            continue

        name = str(name_node)

        # Skip if this name is already in the current batch to be added
        if name in names_to_add:
            logger.info("Rubric '%s' is a duplicate in this batch. Skipping.", name)
            continue

        # Check if a rubric with the same name already exists in the database
        result = await db_session.execute(select(Rubric).filter_by(name=name))
        if result.scalars().first():
            logger.info("Rubric '%s' already exists in the database. Skipping.", name)
            continue

        # If it's a new, unique rule, prepare it for addition
        new_rubric = Rubric(
            name=name, content=str(content_node), category=str(category_node) if category_node else None
        )
        rules_to_add.append(new_rubric)
        names_to_add.add(name)
        logger.info("Prepared new rubric for addition: '%s'", name)

    if rules_to_add:
        db_session.add_all(rules_to_add)
        await db_session.commit()
        logger.info("Successfully added %s new rubrics to the database.", len(rules_to_add))
    else:
        logger.info("No new rubrics to add. Database is up-to-date.")


async def main():
    """Main function to initialize the database schema and run the loading process."""
    logger.info("Initializing database schema...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized.")

    # Find all .ttl files in the 'src' directory, which is the parent of 'core'
    src_path = Path(__file__).parent.parent
    ttl_files = list(src_path.glob("*.ttl"))

    if not ttl_files:
        logger.warning("No .ttl files found in the 'src' directory. Exiting.")
        return

    logger.info("Found %s TTL files to process.", len(ttl_files))

    # Create a new session and run the loader
    async with AsyncSessionLocal() as session:
        await parse_and_load_rubrics(session, ttl_files)


if __name__ == "__main__":
    logger.info("Running rubric loader script...")
    asyncio.run(main())
    logger.info("Rubric loader script finished.")
