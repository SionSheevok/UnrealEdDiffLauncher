"""This module contains an implementation of an application that can a) infer which which Unreal 
project file and editor binary should be used to open an Unreal asset and b) invoke the Unreal 
asset diffing/merging mode of the editor and project."""
import argparse
import pathlib
import subprocess
import sys
from . import try_infer_editor_and_project


def main() -> int:
    """The main CLI implementation. This function returns the same return code that the invoked
     Unreal Editor returns, unless an unhandled error is encountered."""

    arg_parser = argparse.ArgumentParser(description="""This application that infers which
                                            Unreal project file and editor binary should be
                                            used to open an Unreal asset and b) invoke the
                                            Unreal asset diffing/merging mode of the editor
                                            and project.""")
    subparsers = arg_parser.add_subparsers(
        dest="mode", required=True, description="The mode of diffing/merging to use.")

    diff_arg_parser = subparsers.add_parser(
        "diff", description="Specifies the diff mode, comparing two files.")
    diff_arg_parser.add_argument(
        "left", type=pathlib.Path, help="""The file to be compared, typically displayed for 
            visual comparison on the left.""")
    diff_arg_parser.add_argument(
        "right", type=pathlib.Path, help="""Another file to be compared, typically displayed for
            visual comparison on the right.""")

    merge_arg_parser = subparsers.add_parser(
        "merge", description="""Specifies the merge mode, three-way comparing files and 
            producing a fourth containing the merge result.""")
    merge_arg_parser.add_argument(
        "remote", type=pathlib.Path, help="""The remote version of the file to be merged into
            the local version.""")
    merge_arg_parser.add_argument(
        "local", type=pathlib.Path, help="""The local version of the file to merge the remote
            version into.""")
    merge_arg_parser.add_argument(
        "base", type=pathlib.Path, help="""The base version of the file. Ideally, a common
            ancestor revision of 'local' and 'remote'.""")
    merge_arg_parser.add_argument(
        "result", type=pathlib.Path, help="The path to the file to write the merge result to.")

    parsed_args = arg_parser.parse_args()

    match parsed_args.mode:
        case "diff":
            # NOTE: The paths could both be temporary files, in which case we have no clear way of
            # detecting which engine binary to use or what project.
            editor_and_project_paths = (
                try_infer_editor_and_project(arg)
                for arg in [parsed_args.left, parsed_args.right]
            )
            for element in editor_and_project_paths:
                if element is None:
                    raise RuntimeError(f"""Failed to find an Unreal project and/or Unreal editor to
                                         use to diff files, based on the "left" file
                                         ({parsed_args.left}) or "right" file ({parsed_args.right}).
                                         """)

                (editor_binary_path, project_file_path) = element
                process_result = subprocess.run(
                    [
                        editor_binary_path,
                        project_file_path,
                        "-diff",
                        parsed_args.left,
                        parsed_args.right,
                    ],
                    check=False,
                )
                return process_result.returncode

        case "merge":
            # NOTE: There is always a local file when merging, which we can use to detect the
            # executable to use and project.
            editor_and_project_paths = try_infer_editor_and_project(
                parsed_args.local)
            if editor_and_project_paths is None:
                raise RuntimeError(f"""Failed to find an Unreal project and/or Unreal editor to
                                    use to merge files, based on the "local" file
                                    ({parsed_args.local}).""")

            (editor_binary_path, project_file_path) = editor_and_project_paths
            process_result = subprocess.run(
                [
                    editor_binary_path,
                    project_file_path,
                    "-diff",
                    parsed_args.remote,
                    parsed_args.local,
                    parsed_args.base,
                    parsed_args.result,
                ],
                check=False,
            )
            return process_result.returncode


if __name__ == "__main__":
    sys.exit(main())
