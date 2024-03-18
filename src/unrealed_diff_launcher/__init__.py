"""This module contains functions useful for inferring which Unreal project and Unreal editor 
binary should be used to execute asset diffing/merging mode of the editor and project."""
import pathlib
from collections.abc import Sequence


def detect_binaries_from_engine_or_project_root(
    engine_or_project_root: pathlib.Path,
) -> Sequence[pathlib.Path] | None:
    """Attempts to find a Binaries directory within the specified directory, assuming it is the
     Unreal Engine directory or the root directory of an Unreal project, containing"""
    platform_binaries_dir = engine_or_project_root.joinpath(
        "Binaries", "Win64")
    if not platform_binaries_dir.exists():
        return None

    # Generate the list of possible binary names.
    candidate_binary_filenames = []
    for target_name in ["UnrealEditor"]:
        for platform in ["Win64"]:
            for build_configuration in ["Development", "DebugGame"]:
                candidate_binary_filenames.append(
                    f"{target_name}-{platform}-{build_configuration}.exe"
                )

    # Check for the existence of any of these binaries.
    return (
        file_path
        for file_path in (
            platform_binaries_dir.joinpath(filename)
            for filename in candidate_binary_filenames
        )
        if file_path.exists() and file_path.is_file()
    )


def try_infer_editor_and_project(
    test_path: pathlib.Path,
) -> tuple[pathlib.Path, pathlib.Path | None] | None:
    """Attempts to find a Binaries directory within the specified directory, assuming it is the
     Unreal Engine directory or the root directory of an Unreal project, containing"""
    # Resolve the path, so we can access the parent paths reliably.
    test_path = test_path.resolve()

    # Iterate the file system upwards, tracking the project file path and root directory, if any.
    for dir_path in test_path.parents:
        # Check if we're in the Engine directory.
        if dir_path.name == "Engine":
            unreal_binaries = detect_binaries_from_engine_or_project_root(
                dir_path)
            if unreal_binaries is not None and len(unreal_binaries) > 0:
                # TODO: Pick one of the binaries based on the latest.
                return (unreal_binaries[0], None)

        # Otherwise if it's not an Engine directory, it might be a project directory.
        else:
            # Check for *.uproject files within this directory
            project_file_paths = list(
                path for path in dir_path.glob("*.uproject") if path.is_file()
            )

            # Otherwise, if there are multiple, raise an error, as we cannot disambiguate.
            match len(project_file_paths):
                case 0:
                    continue
                case 1:
                    project_file_path: pathlib.Path = project_file_paths[0]
                    project_root_dir = dir_path

                    # Try to find binaries in the project path.
                    unreal_binaries = list(
                        detect_binaries_from_engine_or_project_root(
                            project_root_dir)
                    )

                    if unreal_binaries is not None and len(unreal_binaries) > 0:
                        # TODO: Pick one of the binaries based on the latest.
                        return (unreal_binaries[0], project_file_path)
                    # If there aren't any, try to find an adjacent Engine directory.
                    else:
                        engine_dir_path = project_root_dir.parent.joinpath(
                            "Engine")
                        if engine_dir_path.exists():
                            unreal_binaries = list(
                                detect_binaries_from_engine_or_project_root(
                                    engine_dir_path
                                )
                            )
                            if unreal_binaries is not None and len(unreal_binaries) > 0:
                                # Return the editor binary and project path.
                                return (unreal_binaries[0], project_file_path)
                case _:
                    raise RuntimeError(
                        f'''Could not deduce Unreal editor to use from file path "{test_path}" -
                         multiple *.uproject files found in {dir_path}''')
