from pathlib import Path
from typing import List, Dict, Set
import re


class Schema:
    """
    Loads and prepares a XML Schema for validation.

    Handles schema dependencies programatically.
    Does not modify the original files.
    """

    def __init__(self, schema_folder: str):
        """
        Initialize the Schema.

        Args:
            schema_folder: Path to folder containing the Schema XSD files.
        """
        self.schema_folder = Path(schema_folder)
        self.schema: Path = None
        self.dependencies: List[Path] = []
        # TODO: Load Schema

        self._validate_folder()
        self._analyze_schemas(self._discover_schemas())

    def _validate_folder(self) -> None:
        """Validate that the schema folder exists."""
        if not self.schema_folder.exists():
            raise FileNotFoundError(
                f"Schema folder not found: {self.schema_folder}"
            )

        if not self.schema_folder.is_dir():
            raise ValueError(f"Path is not a directory: {self.schema_folder}")

        try:
            list(self.schema_folder.iterdir())
        except PermissionError:
            raise PermissionError(
                f"Cannot access schema folder: {self.schema_folder}"
            )

    def _discover_schemas(self) -> List[Path]:
        """
        Discover all .xsd files in the folder.

        Returns:
            List of schema paths contained within the folder
        """
        all_schemas = list(self.schema_folder.glob("*.xsd"))

        if not all_schemas:
            raise FileNotFoundError(
                f"No .xsd files found in folder: {self.schema_folder}"
            )
        else:
            return all_schemas

    def _extract_dependencies(self, schema_path: Path) -> Set[str]:
        """
        Extract dependencies from a schema file.

        Args:
            schema_path: Path to the schema file

        Returns:
            Set of dependency filenames referenced by this schema
        """
        dependencies = set()

        try:
            with open(schema_path, 'r', encoding="utf-8") as file:
                content = file.read()

            # Find import and include statements with schemaLocation attributes
            import_patterns = [
                r'<xs:import[^>]+schemaLocation="([^"]+)"',
                r'<xs:include[^>]+schemaLocation="([^"]+)"',
                r'<xsd:import[^>]+schemaLocation="([^"]+)"',
                r'<xsd:include[^>]+schemaLocation="([^"]+)"',
            ]

            for pattern in import_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    dep_path = Path(match)
                    # Only add if it's a .xsd file that exists in our folder
                    if (dep_path.suffix == ".xsd") and dep_path.exists():
                        # Add only the filename
                        dependencies.add(dep_path.name)

        except Exception:
            # Continue if we can't read a file
            pass

        return dependencies

    def _build_dep_tree(
            self,
            schema_path: Path,
            existing_trees: Dict[str, Dict],
            analyzed_schemas: Set[str]
    ) -> Dict[str, Dict]:
        """
        Build complete dependency tree for a schema.

        Args:
            schema_path: Path to the schema to analyze
            existing_trees: Already built dependency trees
            analyzed_schemas: Set of schema names already analyzed

        Returns:
            Complete dependency tree for this schema
        """
        # Mark this schema as being analyzed
        analyzed_schemas.add(schema_path.name)

        # Get direct dependencies
        direct_dependencies = self._extract_dependencies(schema_path)

        # Build tree recursively
        dep_tree = {}

        for dep_filename in direct_dependencies:
            if dep_filename in existing_trees:
                # Reuse existing tree
                dep_tree[dep_filename] = existing_trees[dep_filename]
            elif dep_filename not in analyzed_schemas:
                # Need to analyze this dependency
                dep_path = self.schema_folder / dep_filename
                if dep_path.exists():
                    dep_tree[dep_filename] = self._build_dep_tree(
                            dep_path, existing_trees, analyzed_schemas
                    )
                    # Store the tree for reuse
                    existing_trees[dep_filename] = dep_tree[dep_filename]
            # If in analyzed_schemas but not in existing_trees,
            # it's being analyzed (circular reference)
            # We'll handle this by not including it to avoid infinite recursion

        return dep_tree

    def _analyze_schemas(self, all_schemas: List[Path]) -> None:
        """
        Analyze all schema files to build complete dependency trees.

        Builds dependency trees for each schema, reusing analyzed schemas.
        """
        dependency_trees = {}
        analyzed_schemas = set()

        for schema_path in all_schemas:
            if schema_path.name not in analyzed_schemas:
                dependency_trees[schema_path.name] = self._build_dep_tree(
                        schema_path, dependency_trees, analyzed_schemas
                )

        self._determine_main_schema(all_schemas, dependency_trees)

    def _determine_main_schema(
            self,
            all_schemas: List[Path],
            dep_trees: Dict[str, Dict]
    ) -> None:
        """
        Determine which schema is the main schema based on dependency analysis.

        Args:
            dep_trees: Mapping of schema names to their dependency trees

        Uses heuristic: The main schema is the one with the largest dep_tree.
        """
        if not all_schemas:
            raise RuntimeError("No schemas found to analyze.")

        # Find schema with the largest dependency tree
        max_deps = -1
        main_schema = all_schemas[0]

        for schema_path in all_schemas:
            tree = dep_trees.get(schema_path.name, {})
            dep_count = len(self._get_all_deps_from_tree(tree))
            if dep_count > max_deps:
                max_deps = dep_count
                main_schema = schema_path.name

        self.schema = main_schema
        # Setup dependency list (all other schemas)
        self.dependencies = [
                s for s in all_schemas if s != self.schema
        ]

    def _get_all_deps_from_tree(self, tree: Dict[str, Dict]) -> Set[str]:
        """
        Recursively extract all dependency names from a dependency tree.

        Args:
            tree: Dependency tree (nested dictionaries)

        Returns:
            Set of all dependency schema names in the tree
        """
        dependencies = set()

        for dep_name, sub_tree in tree.items():
            dependencies.add(dep_name)
            # Recursively get dependencies from sub-trees
            dependencies.update(self._get_all_deps_from_tree(sub_tree))

        return dependencies
