# Generate C Module

Generate C source and header files, with boilerplate code for a module


## Usage

```shell

python generate_c_module.py [-t|--template PATH_TO_TEMPLATE_FILE] [-s|--source_dir PATH_TO_SOURCE_DIRECTORY] [-h|--header_dir PATH_TO_HEADER_DIRECTORY] [-d|--output_dir PATH_TO_OUTPUT_DIR] module_name

```

Will generate module_name.h, module_name.c in the given output directories for source and header files. Specified source and header directories take precedence over output directory, when all 3 are specified. Specifying only one is the same as using `-d`. 


## Template File

A template file is a TOML files that defines how the files are files and their content. The file is split into 2 main sections. General configurations, and template.

```toml

# -----------------------------------------------------------------------------
# default configuration file
# -----------------------------------------------------------------------------

name = "default configurations"

# -----------------------------------------------------------------------------
# path to other configuration files to inherit [general], [template] and
# [special_variables] sections from. 
# 
# -----------------------------------------------------------------------------
inherits = []

# -----------------------------------------------------------------------------
# path to other configuration files to merge [general], [template] and
# [special_variables] sections with.
# 
# -----------------------------------------------------------------------------
merge = []


# -----------------------------------------------------------------------------
# general sectioon defines what files are generated for the module,
# file contents are divided into header, body and footer templates
# 
# The files are split in 3 types:
# - source_files: 
#       contain source code for the module, source files implicity contain
#       src_header and src_footer templates
# 
# - header_files: 
#       contains module's header files, header_files implicaitly contain
#       inc_header and inc_footer templates
# 
# - test_files:   
#       contains module's test files, test_files implicitly contain
#       test_header and test_footer templates
# 
# The distinction between types is made, so that templates can be resued
# between different types while having using deifferent templates for each 
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
#       - id:   used to look up the file's template from the template sections
#       - ext:  output file extension
#       - name: output file name template, ${module_name} is replaced by the module name, all text surrounding ${module_name} is preserved
#       - path: path to directory where the generated file will be placed, relative paths will be expanded to absolute paths relative to root directory
#       - body: list of `id`s of templates that will be added to the file's body
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
    {id="unityRunner", ext=".c", name="${module_name}TestRunner", path="./Test/TestRunners", body=["std_inc", "unity_inc", "unity_main"]},
]


# -----------------------------------------------------------------------------
# define special variables used in templates
# each variable has a place holder ${variable_name},
# for example ${author} in template will be replaced by the value of author
# if a varible doesn't exist, it will be replaced by an empty string
# -----------------------------------------------------------------------------
[special_variables]

author    = "Author name"
email     = "email@org.com"
signature = "${author} <${email}>"

licence   = """Copyright ${year} ${signature}>
Permission is hereby granted, free of charge, 
to any person obtaining a copy of this software 
and associated documentation files (the "Software"), 
to deal in the Software without restriction, 
including without limitation the rights to use, 
copy, modify, merge, publish, distribute, sublicense, 
and/or sell copies of the Software, and to permit persons 
to whom the Software is furnished to do so, 
subject to the following conditions:
    - The above copyright notice and this permission notice 
    shall be included in all copies or substantial 
    portions of the Software.
    - THE SOFTWARE IS PROVIDED "AS IS", 
    WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
    INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE 
    AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS 
    OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES 
    OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, 
    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
    WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


# -----------------------------------------------------------------------------
# template section define templates used to create files for the module
# -----------------------------------------------------------------------------
[templates]

# file header added to the start of files
file_header = """
/******************************************************************************
 * @file    ${module_name}${ext}
 * @brief   
 * @author  ${signature}
 * @date    ${date}
 * @licence ${licence}
 * 
 ******************************************************************************/
"""

# added to expanded variables in place of new line characters
header_expansion = [
    {"\n"=" *          \n"},
]

# file footer added to the end of files
file_footer="""
/* ------------------------------------------------------------------------- */
/*  End of File  */
/* ------------------------------------------------------------------------- */
"""

# added to the start of all source files
src_header = "${file_header}"

# added at the end of all source files
src_footer = "${file_footer}"

# added to the start of all header files
inc_header = """${file_header}
#ifndef _${module_name}_H_
#define _${module_name}_H_

#ifdef __cplusplus
extern "C" 
{
#endif /* __cplusplus */
"""

# added at the end of all header files
inc_footer = """#ifdef __cplusplus
}
#endif /* __cplusplus */
#endif /* _${module_name}_H_ */
${file_footer}
"""

# added to the start of all test files
test_header = """
/******************************************************************************
 * @file    ${module_name}${ext}
 * @brief   unit test for ${module_name}
 * @author  ${signature}
 * @date    ${date}
 * @licence ${licence}
 * 
 ******************************************************************************/
"""

# added at the end of all test files
test_footer = "${file_footer}"


# standard includes
std_inc = """
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
"""

empty_main = """
int main(void)
{
    return 0;
}
"""

unity_inc = """
#include "unity.h"
"""

unity_main = """
int main(void)
{
    UNITY_BEGIN();
    return UNITY_END();
}
"""

```
