#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import calendar
import copy
import datetime
import logging as log
import pathlib
import re
import string
import sys
from typing import *

import tomllib


__VERSION__: Final[str] = "0.0.2"


LOGGER: log.Logger = log.getLogger(__name__)


def write_file(file_name: str, dst_dir: pathlib.Path, contents: str):
    dst_dir.mkdir(parents=True, exist_ok=True)

    dst_file: pathlib.Path = dst_dir / file_name

    log.debug(f"Writing file: {file_name} to {dst_dir}")
    with open(dst_file, "w") as out_file:
        out_file.write(contents)


def generate_file(module_name: str, output_dir: pathlib.Path, recipe: Dict[str, Any], templates: Dict[str, Any]):
    #  file name and destination folder
    recipe["name"] = string.Template(recipe["name"]).safe_substitute(module_name=module_name)
    recipe["path"] = string.Template(recipe["path"]).safe_substitute(module_name=module_name)

    file_ext: str = recipe.get('ext')
    file_base_name: str = recipe.get('name')
    file_name: str = f"{file_base_name}{file_ext}"
    file_path: pathlib.Path = output_dir / recipe.get("path")

    file_variables: dict[str, str] = {
        "module_name": module_name,
        "file_name": file_name,
        "ext": file_ext,
        "base_name": file_base_name
    }

    # file contents
    file_contents: List[str] = list()
    for section in recipe.get("body"):
        section_string: str = templates[section]["str"]
        file_contents.append(string.Template(section_string).safe_substitute(**file_variables))

    file_contents: List[str] = "\n".join(file_contents)
    write_file(file_name, file_path, file_contents)


def generate_sources(module_name: str, output_dir: pathlib.Path, source_files: List[Dict[str, Any]], templates: Dict[str, Any], **kwargs):
    for src in source_files:
        src["body"]: List[str] = ["src_header"] + src["body"] + ["src_footer"]
        generate_file(module_name, output_dir, src, templates)


def generate_headers(module_name: str, output_dir: pathlib.Path, header_files: List[Dict[str, Any]], templates: Dict[str, Any], **kwargs):
    for src in header_files:
        src["body"]: List[str] = ["inc_header"] + src["body"] + ["inc_footer"]
        generate_file(module_name, output_dir, src, templates)


def generate_tests(module_name: str, output_dir: pathlib.Path, test_files: List[Dict[str, Any]], templates: Dict[str, Any], **kwargs):
    for src in test_files:
        src["body"]: List[str] = ["test_header"] + src["body"] + ["test_footer"]
        generate_file(module_name, output_dir, src, templates)


def expand_template(tmp_name: str, templates: Dict[str, Any]) -> str:
    tmp_vars: Dict[str, Any] = templates.get(tmp_name, None)
    if tmp_vars is None:
        return f"${{{tmp_name}}}"
    
    tmp_str: str = tmp_vars.get("str", None)
    if tmp_str is None:
        return f"${{{tmp_name}}}"

    template: string.Template = string.Template(tmp_str)
    expansions: Dict[str, str] = dict()
    for ident in template.get_identifiers():
        expanded_str = expand_template(ident, templates)
        identifier_template: Dict[str, Any] | None = templates.get(ident)
        
        if identifier_template is None:
            continue
        
        for substitution_rule in identifier_template.get("sub", []):
            pattern: str = substitution_rule.get("pattern")
            replace: str = substitution_rule.get("replace")
            expanded_str: str = re.sub(pattern, replace, expanded_str)

        expansions[ident] = expanded_str

    return template.safe_substitute(expansions)


def expand_templates(templates: Dict[str, Dict[str, str]], **kwargs) -> Dict[str, str]:
    for (tmp_name, tmp_vars) in templates.items():
        tmp_str = tmp_vars.get("str", None)
        if not tmp_str:
            continue
        
        template = string.Template(tmp_str)
        
        if not template.is_valid():
            continue
        
        # expand kwargs in all valid templates
        templates[tmp_name]["str"] = template.safe_substitute(kwargs)

        # expand template using other templates (if necessary)
        templates[tmp_name]["str"] = expand_template(tmp_name, templates)

    return templates


def main():

    arg_parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Generate files according to template file",
        epilog=f"%(prog)s version {__VERSION__}",
    )

    arg_parser.add_argument(
        "module_names",
        help="list of module names for which the files are generated",
        nargs="+"
    )

    arg_parser.add_argument(
        "-t",
        "--template_file",
        help="path to template file, default: ./template.toml",
        type=pathlib.Path,
        default=pathlib.Path("./template.toml")
    )

    arg_parser.add_argument(
        "-o",
        "--output_dir",
        help="output directory where generated files will be written, default is current directory",
        type=pathlib.Path,
        default=pathlib.Path.cwd()
    )

    arg_parser.add_argument(
        "-v",
        dest="verbose",
        help="output debugging messages to console, disabled by default to outputs errors only, "
             "use -vv, -vvv, -vvvv, -vvvv for more verbosity",
        action="count",
        default=0
    )

    arg_parser.add_argument(
        "--version",
        help="print current program's version",
        action="version",
        version=f"%(prog)s version {__VERSION__}"
    )

    parsed_args: argparse.Namespace = arg_parser.parse_args()
    template_file: pathlib.Path = parsed_args.template_file.absolute()
    output_dir: pathlib.Path = parsed_args.output_dir.absolute()
    module_names: List[str] = parsed_args.module_names
    verbosity: int = parsed_args.verbose

    # setup logging verbosity
    if verbosity == 0:
        log.basicConfig(level=log.CRITICAL)
    elif verbosity == 1:
        log.basicConfig(level=log.ERROR)
    elif verbosity == 2:
        log.basicConfig(level=log.WARNING)
    elif verbosity == 3:
        log.basicConfig(level=log.INFO)
    else:
        log.basicConfig(level=log.DEBUG)

    # load templates from file
    if not template_file.is_file():
        log.critical(f"Failed to open template file: {template_file!s}")
        sys.exit(-1)

    log.info(f"Loading templates from: {template_file.name}")

    with open(template_file, "rb") as conf_file:
        config = tomllib.load(conf_file)
    
    template_name = config.get("name", None)
    inherits_from = config.get("inherit", None)
    merge_with = config.get("merge", None)
    
    special_variables = config.get("special_variables", None)

    today = datetime.datetime.today()
    calendar.setfirstweekday(calendar.MONDAY)
    special_variables["day"]        = today.day
    special_variables["day_abbr"]   = calendar.day_abbr[today.weekday()]
    special_variables["day_name"]   = calendar.day_name[today.weekday()]
    special_variables["month"]      = today.month
    special_variables["month_abbr"] = calendar.month_abbr[today.month]
    special_variables["month_name"] = calendar.month_name[today.month]
    special_variables["year"]       = today.year
    special_variables["date"]       = today.strftime("%Y/%m/%d")

    # generate files for each module, using extracted templates
    for module_name in module_names:

        module_config: Dict[Any, Any] = copy.deepcopy(config)
        general: Dict[Any, Any] = module_config.get("general", None)
        templates: Dict[Any, Any] = module_config.get("templates", None)
        special_variables["module_name"] = module_name

        log.info(f"Generating files for module: {module_name}")

        # expand templates
        expanded_templates: Dict[str, Any] = expand_templates(templates, **special_variables)

        # source files
        source_files: List[Dict[str, str]] = general.get("sources", None)
        if source_files is not None:
            generate_sources(module_name, output_dir, source_files, expanded_templates)

        log.info(f"Generated source files for module {module_name}")

        # header files
        header_files: List[Dict[str, str]] = general.get("headers", None)
        if header_files is not None:
            generate_headers(module_name, output_dir, header_files, expanded_templates)

        log.info(f"Generated header files for module {module_name}")

        # test files
        test_files: List[Dict[str, str]] = general.get("test", None)
        if test_files is not None:
            generate_tests(module_name, output_dir, test_files, expanded_templates)

        log.info("-------------------")

    log.info("Done!")


if __name__ == "__main__":
    main()
