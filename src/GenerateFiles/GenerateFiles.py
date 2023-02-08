#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import calendar
import datetime
import json
import logging as log
import pathlib
import re
import string
import sys
from pprint import pprint as pp
from typing import *

import tomllib


def write_file(file_name: str, dst_dir: pathlib.Path, contents: str):
    dst_dir.mkdir(parents=True, exist_ok=True)

    dst_file: pathlib.Path = dst_dir / file_name
    with open(dst_file, "w") as out_file:
        out_file.write(contents)


def generate_file(module_name: str, output_dir: pathlib.Path, recipe: Dict[str, Any], templates: Dict[str, Any]):
    #  file name and destination folder
    recipe["name"] = string.Template(recipe["name"]).safe_substitute(module_name=module_name)
    recipe["path"] = string.Template(recipe["path"]).safe_substitute(module_name=module_name)
    
    file_name: str = f"{recipe.get('name')}{recipe.get('ext')}"
    file_path: pathlib.Path = output_dir / recipe.get("path")

    # file contents
    file_contents: List[str] = list()
    for section in recipe.get("body"):
        str: str = templates[section]["str"]
        file_contents.append(string.Template(str).safe_substitute(file_name=file_name, module_name=module_name))

    file_contents: List[str] = "\n".join(file_contents)
    
    # pp(file_name)
    # pp(recipe)
    # print(f"{file_contents=}")
    # pp("")

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
        description="Generate files according to template file"
    )

    arg_parser.add_argument(
        "module_name",
        help="name of the module for which the files are generated"
    )

    arg_parser.add_argument(
        "template_file",
        help="path to template file"
    )

    arg_parser.add_argument(
        "-o",
        "--output_dir",
        help="output directory where generated files will be written, default is current directory",
        type=str,
        default="./"
    )

    parsed_args: argparse.Namespace = arg_parser.parse_args()
    template_file: pathlib.Path = pathlib.Path(parsed_args.template_file).absolute()
    output_dir: pathlib.Path = pathlib.Path(parsed_args.output_dir).absolute()
    module_name: str = parsed_args.module_name

    if not template_file.is_file():
        sys.exit(-1)

    #  load configuration file
    with open(template_file, "rb") as conf_file:
        config = tomllib.load(conf_file)
    
    # with open("config.json", "w") as out_file:
    #     out_file.write(json.dumps(config))
    
    config_name = config.get("name", None)
    inherits_from = config.get("inherit", None)
    merge_with = config.get("merge", None)
    
    general = config.get("general", None)
    special_variables = config.get("special_variables", None)
    templates = config.get("templates", None)

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

    special_variables["module_name"] = module_name
    
    # expand templates
    templates: Dict[str, Any] = expand_templates(templates, **special_variables)

    # with open("templates.json", "w") as out_file:
    #     out_file.write(json.dumps(templates))
    
    # source files
    source_files: List[Dict[str, str]] = general.get("sources", None)
    if source_files is not None:
        generate_sources(module_name, output_dir, source_files, templates)

    # header files
    header_files: List[Dict[str, str]] = general.get("headers", None)
    if header_files is not None:
        generate_headers(module_name, output_dir, header_files, templates)

    # test files
    test_files: List[Dict[str, str]] = general.get("test", None)
    if test_files is not None:
        generate_tests(module_name, output_dir, test_files, templates)


if __name__ == "__main__":
    main()
