import re
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Set
from lxml import etree


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
        self.schema: Optional[etree.XMLSchema] = None
        self.schema_doc: Optional[etree._ElementTree] = None
        self.temp_folder: Optional[Path] = None

        self._validate_folder()

        schema, dependencies = self._analyze_schemas(self._discover_schemas())
        self._load_schema(schema, dependencies)
        self._clean_temp_files()

    def _validate_folder(self) -> None:
        """
        Validate that the schema folder exists.

        Raises:
            FileNotFoundError: If folder is not found
            ValueError: If the path is not a folder
            PermissionError: If user has doesn't have access to the folder
        """
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

        Raises:
            FileNotFoundError: If no .xsd files are found in the folder
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

    def _analyze_schemas(self, all_schemas: List[Path]) -> (Path, List[Path]):
        """
        Analyze all schema files to build complete dependency trees.

        Builds dependency trees for each schema, reusing analyzed schemas.

        Args:
            all_schemas: All schemas to be considered for analysis

        Returns:
            A tuple of the main schema and it's dependencies
        """
        dependency_trees = {}
        analyzed_schemas = set()

        for schema_path in all_schemas:
            if schema_path.name not in analyzed_schemas:
                dependency_trees[schema_path.name] = self._build_dep_tree(
                        schema_path, dependency_trees, analyzed_schemas
                )
        return self._determine_main_schema(all_schemas, dependency_trees)

    def _determine_main_schema(
            self,
            all_schemas: List[Path],
            dep_trees: Dict[str, Dict]
    ) -> (Path, List[Path]):
        """
        Determine which schema is the main schema based on dependency analysis.

        Args:
            all_schemas: All schemas to be considered
            dep_trees: Mapping of schema names to their dependency trees

        Returns:
            A tuple of the main schema and it's dependencies

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

        # Setup dependency list (all other schemas)
        dependencies = [
                s.name for s in all_schemas if s.name != main_schema
        ]

        return (main_schema, dependencies)

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

    def _load_schema(self, schema: Path, dependencies: List[Path]) -> None:
        """
        Load the main XML Schema for validation.

        Creates temporary copies with fixed imports and loads the schema.

        Args:
            schema: The main schema to be loaded
            dependencies: The schemas that the main schema depends on

        Raises:
            etree.XMLSchemaParseError: If schema cannot be parsed
            RuntimeError: If schema loading fails
        """
        if schema is None:
            raise RuntimeError(
                "Main schema is not determined. Dependency analysis failed."
            )

        try:
            # Create temporary schema files with fixed imports
            temp_schema = self._create_temp_schema_copy(schema, dependencies)

            # Parse and load the schema
            with open(temp_schema, 'r', encoding="utf-8") as file:
                self.schema_doc = etree.parse(file)

            # Create XMLSchema object and store it
            self.schema = etree.XMLSchema(self.schema_doc)

        except etree.XMLSchemaParseError as e:
            raise etree.XMLSchemaParseError(
                    f"Failed to parse main schema '{self.schema.name}': {e}"
            )

        except Exception as e:
            raise RuntimeError(f"Failed to load schema: {e}")

    def _create_temp_schema_copy(
            self,
            schema: Path,
            dependencies: List[Path],
    ) -> Path:
        """
        Create temporary copies of all schemas with fixed import paths.

        Returns:
            Path to the temporary main schema file with corrected imports
        """
        # Create temporary folder
        self.temp_folder = Path(tempfile.mkdtemp())

        # Copy and fix all schemas (main + dependencies)
        all_schema_files = [schema] + dependencies

        for schema_path in all_schema_files:
            schema_path = self.schema_folder / schema_path

            # Read original schema content
            with open(schema_path, 'r', encoding="utf-8") as file:
                content = file.read()

            # Fix import/include paths
            fixed_content = self._fix_schema_imports(content, dependencies)

            # Write fixed schema to temp folder
            temp_schema_file = self.temp_folder / schema_path.name
            with open(temp_schema_file, 'w', encoding="utf-8") as file:
                file.write(fixed_content)

        # Return path to the main schema in temp directory
        return self.temp_folder / schema

    def _fix_schema_imports(
            self,
            schema_content: str,
            dependencies: List[Path]
    ) -> str:
        """
        Fix schema import/include statements to work with local file structure.

        Args:
            schema_content: Original schema content

        Returns:
            Fixed schema content with corrected import paths
        """
        fixed_content = schema_content

        # Get list of all dependency filenames for reference
        dep_filenames = [dep for dep in dependencies]

        # Fix each dependency reference
        for dep_filename in dep_filenames:
            base_name = dep_filename.replace("-Schema.xsd", '')
            base_name = base_name.replace(".xsd", '')

            # Patterns to fix various forms of import/include statements
            patterns = [
                # Fix complex paths and version folders
                (rf'schemaLocation="[^"]*{re.escape(dep_filename)}"',
                 f'schemaLocation="{dep_filename}"'),
                (rf'schemaLocation="[^"]*/{re.escape(base_name)}[^"]*\.xsd"',
                 f'schemaLocation="{dep_filename}"'),
                # Fix paths that end with the dep_filename
                (rf'schemaLocation="[^"]*/{re.escape(dep_filename)}"',
                 f'schemaLocation="{dep_filename}"'),
                # Fix paths with /CommonTypes/v14/ style version folders
                (rf'schemaLocation="[^"]*/{re.escape(base_name)}/[^"]*"',
                 f'schemaLocation="{dep_filename}"')
            ]

            for pattern, replacement in patterns:
                fixed_content = re.sub(pattern, replacement, fixed_content)

        return fixed_content

    def _clean_temp_files(self) -> None:
        """Clean up temporary schema files."""
        if hasattr(self, "temp_folder"):
            if self.temp_folder and self.temp_folder.exists():
                shutil.rmtree(self.temp_folder)
                self.temp_folder = None

