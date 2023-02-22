# Generate C Module

Generate files (text, C, C++, etc) with optional boilerplate, according to a template file


## Why?

When starting a new project, I need to create multiple source and header files and add some comments. It gets a bit boring copying and pasting all the comments from one file to the others, and it's easy to make some mistakes, so I decided to automate that. It's quite handy and saves time (like 5 minutes?) off each project. Something a little like [Jinja](https://jinja.palletsprojects.com/en/3.1.x/), but lighter and suitable for smaller files.


## Usage

```shell
usage: GenerateFiles.py [-h] [-t TEMPLATE_FILE] [-o OUTPUT_DIR] [-v] [--version] module_names [module_names ...]

Generate files according to template file

positional arguments:
  module_names          list of module names for which the files are generated

options:
  -h, --help            show this help message and exit
  -t TEMPLATE_FILE, --template_file TEMPLATE_FILE
                        path to template file, default: ./template.toml
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        output directory where generated files will be written, default is current directory
  -v                    output debugging messages to console, disabled by default to outputs errors only, use -vv, -vvv, -vvvv, -vvvv for more verbosity
  --version             print current program's version
```

Will generate module_name.h, module_name.c in the given output directories for source and header files. Specified source and header directories take precedence over output directory, when all 3 are specified. Specifying only one is the same as using `-d`. 


## Template File

A template file is a TOML files that defines how the files are files and their content. The file is split into 2 main sections. General configurations, and template.


```toml

# -----------------------------------------------------------------------------
# default template file
# -----------------------------------------------------------------------------

name = "default template"

# -----------------------------------------------------------------------------
# path to other template files to inherit [general], [template] and
# [special_variables] sections from. 
# 
# -----------------------------------------------------------------------------
inherits = []

# -----------------------------------------------------------------------------
# path to other template files to merge [general], [template] and
# [special_variables] sections with.
# 
# -----------------------------------------------------------------------------
merge = []


# -----------------------------------------------------------------------------
# general section defines what files are generated for the module,
# file contents are divided into header, body and footer templates
# 
# The files are split in 3 types:
# - source_files: 
#       contain source code for the module, source files implicitly contain
#       src_header and src_footer templates
# 
# - header_files: 
#       contains module's header files, header_files implicitly contain
#       inc_header and inc_footer templates
# 
# - test_files:   
#       contains module's test files, test_files implicitly contain
#       test_header and test_footer templates
# 
# The distinction between types is made, so that templates can be reused
# between different types while having using different templates for each 
# file type
# 
# -----------------------------------------------------------------------------
[general]


# -----------------------------------------------------------------------------
# define generated source files 
# 
# each file is defined by a mapping
#   {id="id", ext="ext", name="name", body=["item1", "item2"]}
# 
#       - id:   ID of the file being generated, must be unique for each file
#       - ext:  output file extension
#       - name: output file name template, ${module_name} is replaced by the module name, all text surrounding ${module_name} is preserved as is
#       - path: path to directory where the generated file will be placed, relative paths will be expanded to absolute paths relative to root directory
#       - body: list of `ID`s of templates that will be added to the file's body
# 
# there can be multiple source files
# -----------------------------------------------------------------------------
sources = [
    {id="C_Src", ext=".c", name="${module_name}", path="./Src", body=["std_inc", "empty_main"]},
]

# -----------------------------------------------------------------------------
# define generated header files 
# -----------------------------------------------------------------------------
headers = [
    {id="C_Inc", ext=".h", name="${module_name}", path="./Inc", body=[]},
]

# -----------------------------------------------------------------------------
# define generated test files 
# -----------------------------------------------------------------------------
test = [
    {id="unity",       ext=".c", name="${module_name}Test",       path="./Test",             body=["std_inc", "unity_inc"]},
    {id="unityRunner", ext=".c", name="${module_name}TestRunner", path="./Test/TestRunners", body=["std_inc", "unity_inc"]},
]


# -----------------------------------------------------------------------------
# define special variables used in templates
# each variable has a place holder ${variable_name},
# for example ${author} in template will be replaced by the value of author
# if a variable doesn't exist, it will be kept as is
# The script provides the following special variables:
# day        : current's day (1-31)
# day_abbr   : current day's abbreviated name (Sat, Sun, Mon, etc)
# day_name   : current day's full name (Saturday, Sunday, Monday, etc)
# month      : current month (1-12)
# month_abbr : current month's abbreviated name (Jan, Feb, Mar, etc)
# month_name : current month's full name (January, February, etc)
# year       : current year
# date       : current date as a string in the format YYYY/MM/DD
# module_name: module's name
#
# in addition to the previous variables, the following variables are 
# added per file
# base_name  : current file's base name
# ext        : current file's extension (.c, .cpp, .h, etc)
# file_name  : current file's name (base name + extension, eg: foo.c, bar.cpp, etc)
# 
# -----------------------------------------------------------------------------
[special_variables]

author    = "Author name"
email     = "email@org.com"

# -----------------------------------------------------------------------------
# template section define templates used to create files for the module
# templates can be plain text, or contain the `ID` of one or more special 
# variables or other templates. A template must not include itself 
# (either directly, or indirectly)
# -----------------------------------------------------------------------------
[templates]

# signature
[templates.signature]
str = "${author} <${email}>"

# license template
[templates.license]
str   = """
Copyright ${year}, ${signature}

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

# file header added to the start of files
[templates.file_header]
str = """
/******************************************************************************
 * @file      ${file_name}
 * @brief     
 * @author    ${signature}
 * @date      ${date}
 * @copyright ${license}
 *            
 ******************************************************************************/
"""

# added to expanded variables in place of new line characters
sub = [
    {pattern='\n\n', replace='\n *            '},
]

format = {width = 80}

# file footer added to the end of files
[templates.file_footer]
str="""

/* ------------------------------------------------------------------------- */
/*  End of File  */
/* ------------------------------------------------------------------------- */

"""

# added to the start of all source files
[templates.src_header]
str = "${file_header}"

# added at the end of all source files
[templates.src_footer]
str = "${file_footer}"

# added to the start of all header files
[templates.inc_header]
str = """${file_header}

#ifndef _${base_name}_H_
#define _${base_name}_H_

#ifdef __cplusplus
extern "C" 
{
#endif /* __cplusplus */

"""

# added at the end of all header files
[templates.inc_footer]
str = """

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif /* _${base_name}_H_ */
${file_footer}
"""

# added to the start of all test files
[templates.test_header]
str = "${file_header}"


# added at the end of all test files
[templates.test_footer]
str = "${file_footer}"


# standard includes
[templates.std_inc]
str = """
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
"""

[templates.empty_main]
str = """
int main(void)
{
    return 0;
}
"""

[templates.unity_inc]
str = """
#include "unity.h"
#include "unity_fixture.h"
"""

```


## In progress

Some features that are not implemented yet:
- Inherit templates from other template files
- Merge current template file with other template files
- Formatting in templates
