#! /usr/bin/python
#
# This script builds an OpenDSA textbook according to a specified configuration file
#   - Creates an ODSA_Config object from the specified configuration file
#     - Validates the configuration file and sets appropriate defaults for omitted fields (see ODSA_Config.py for more information)
#     - Makes it easy to reference configuration options
#   - Optionally builds JSAV to make sure the library is up-to-date, if specified in the configuration file
#   - Initializes the output directory
#     - Creates the output directory and a source directory inside it
#     - Copies _static directory to the source directory
#     - Creates a copy of the config file in the _static directory for use by the gradebook page
#   - Generates an index.html file in the output directory of the new book which redirects (via JavaScript) to the book_output_dir (html/)
#   - Traverses the 'chapters' section of the configuration file
#     - For each chapter and module, maps the name to its chapter or module number (used for numbering during postprocessing)
#     - Keeps track of modules encountered and prints an error message if a duplicate module name is detected
#     - Creates an ODSA_RST_Module object for each module (see ODSA_RST_Module for more information)
#     - Keeps track of the ToDo directives, images, and missing exercises encountered, as well as requirements that are satisfied
#     - Maps the module name and number to the chapter its part of (used for correcting the chapter number during postprocessing)
#   - Prints out a list of any exercises encountered in RST source files that did not appear in the config file
#   - Generates ToDo.rst, if any TODO directives were encountered when processing the book AND if the configuration file does not suppress them
#   - Creates table.json and page_chapter.json which are used by Sphinx during the building process
#   - Generates a Makefile and conf.py based on templates found in config_templates.py
#     - conf.py is configured to point to the original ODSAextensions and _themes directories
#     - CONTROLLING INCLUSION OF GLOBAL JS AND CSS FILES - conf.py contains a dictionary called html_context
#       which controls what JS and CSS files are included on ALL module pages, please see the assoicated comment
#       for more information
#   - Copies the images encountered while processing the book to the output source directory
#   - Runs 'make' on the output directory to build the book using Sphinx
#   - Calls update_TOC in postprocessor.py to update the chapter, section and module numbers

import sys
import os
import shutil
import distutils.dir_util
import distutils.file_util
import json
import collections
import re
import subprocess
import codecs
import datetime
import threading
import requests

from collections import Iterable
from optparse import OptionParser
from config_templates import *
from ODSA_RST_Module import ODSA_RST_Module
from ODSA_Config import ODSA_Config
from postprocessor import update_TOC, update_TermDef, make_lti
from urlparse import urlparse
from canvas_sdk.methods import accounts, courses, external_tools, modules, assignments
from canvas_sdk import RequestContext

# List of exercises encountered in RST files that do not appear in the
# configuration file
missing_exercises = []

# List of modules that have been processed, do not allow multiple modules
# with the same name (would cause a conflict in the database)
processed_modules = []

# List of images encountered while processing module files, these will be
# copied from the RST/Images to Images in the output source directory
images = []

# Stores information about ToDo directives
todo_list = []

# List of fulfilled prerequisite topics
satisfied_requirements = []

# Maps the chapter name and number to each module, used for correcting the
# numbers during postprocessing
module_chap_map = {}

# Dictionary which stores a mapping of sections to modules, modules to
# their numbers, and figures, tables, theorems, and equations to their
# numbers
num_ref_map = {}

# Prints the given string to standard error


def print_err(err_msg):
    sys.stderr.write('%s\n' % err_msg)

# Processes a chapter or section of the book
#   - config - a dictionary containing all the configuration options
#   - section - a dictionary where all the keys are sections or modules
#   - index_rst - the index.rst file being generated
#   - depth - the depth of the recursion; 0 for the main chapters, 1 for any subsections, ..., N for the modules
#   - current_section_numbers - a list that contains the numbering scheme for each section or module ([chapter].[section].[...].[module])
#   - section_name - a string passed to modules for inclusion in the RST header that specifies which chapter / section the module belongs to


def process_section(config, section, index_rst, depth, current_section_numbers=[], section_name=''):
    # Initialize the section number for the current depth
    if depth >= len(current_section_numbers):
        current_section_numbers.append(config.start_chap_num)

    for subsect in section:
        # Parse the subsection name by eliminating the path and file extension
        # if its a module
        subsect_name = os.path.splitext(os.path.basename(subsect))[0]
        num_ref_map[subsect_name] = -1  # Add the section name to num_ref_map

        if not isinstance(section[subsect], Iterable):
            continue

        if 'exercises' in section[subsect]:
            process_module(config, index_rst, subsect, section[
                           subsect], depth, current_section_numbers, section_name)
        else:
            # List of characters Sphinx uses for headers, the depth of a
            # section header determines which character to use
            sphinx_header_chars = ['=', '-', '`', "'", '.', '*', '+', '^']

            print("  " * depth) + subsect
            index_rst.write(subsect + '\n')
            index_rst.write(
                (sphinx_header_chars[depth] * len(subsect)) + "\n\n")
            # if the chapter is hidden we use odsatoctree
            # the div wrapping the chapter and module will have the
            # 'hide-from-toc' class and will be deleted from the TOC
            if 'hidden' in section[subsect]:
                index_rst.write(".. odsatoctree::\n")
            else:
                index_rst.write(".. toctree::\n")
            index_rst.write("   :numbered:\n")
            index_rst.write("   :maxdepth: 3\n\n")
            process_section(config, section[
                            subsect], index_rst, depth + 1, current_section_numbers, subsect_name)

        # Increments the section count at the current depth
        current_section_numbers[depth] += 1

    # Reset the section number when done processing the current level
    if depth >= 0:
        current_section_numbers[depth] = config.start_chap_num

    index_rst.write("\n")

# Processes a module
#   - config - a dictionary containing all the configuration options
#   - index_rst - the index.rst file being generated
#   - mod_path - the path to the module relative to the RST/<lang> directory
#   - mod_attrib - dictionary containing the module data, 'exercises' is a mandatory field (even if its empty)
#   - depth - the depth of the recursion, used to determine the number of spaces to print before the module name to ensure proper indentation
#   - current_section_numbers - a list that contains the numbering scheme for each section or module ([chapter].[section].[...].[module])
#   - section_name - a string passed to modules for inclusion in the RST header that specifies which chapter / section the module belongs to


def process_module(config, index_rst, mod_path, mod_attrib={'exercises': {}}, depth=0, current_section_numbers=[], section_name=''):
    global todo_list
    global images
    global missing_exercises
    global satisfied_requirements
    global module_chap_map
    global num_ref_map
    global cmap_map

    # Parse the name of the module from mod_path and remove the file extension
    # if it exists
    mod_name = os.path.splitext(os.path.basename(mod_path))[0]

    # Update the reference for each section to point to the first module in
    # the section
    if section_name != '' and num_ref_map[section_name] == -1:
        num_ref_map[section_name] = mod_name

    # Print error message and exit if duplicate module name is detected
    if mod_name in processed_modules:
        print_err(
            'ERROR: Duplicate module name detected, module: %s' % mod_name)
        sys.exit(1)

    # Add module to list of modules processed
    processed_modules.append(mod_name)

    print("  " * depth) + mod_name
    index_rst.write("   %s\n" % mod_name)

    # Initialize the module
    module = ODSA_RST_Module(
        config, mod_path, mod_attrib, satisfied_requirements, section_name, depth, current_section_numbers)

    # Append data from the processed module to the global variables
    todo_list += module.todo_list
    images += module.images
    missing_exercises += module.missing_exercises
    satisfied_requirements += module.requirements_satisfied
    num_ref_map = dict(num_ref_map.items() + module.num_ref_map.items())
    if len(module.cmap_dict['concepts']) > 0:
        cmap_map = module.cmap_dict

    # Maps the chapter name and number to each module, used for correcting the numbers during postprocessing
    # Have to ignore the last number because that is the module number (which
    # is already provided by Sphinx)
    module_chap_map[mod_name] = [
        section_name, '.'.join(str(i) for i in current_section_numbers[:-1])]

    # Hack to maintain the same numbering scheme as the old preprocessor
    mod_num = ''
    if len(current_section_numbers) > 0:
        mod_num = '%s.%d' % ('.'.join(
            str(j) for j in current_section_numbers[:-1]), (current_section_numbers[-1] + 1))

    num_ref_map[mod_name] = mod_num


def generate_index_rst(config, slides=False):
    """Generates the index.rst file, calls process_section() on config.chapters to recursively process all the modules in the book (in order), as each is processed it is added to the index.rst"""

    print "Generating index.rst\n"
    print "Processing..."

    header_data = {}
    header_data['mod_name'] = 'index'
    header_data['dispModComp'] = 'false'
    header_data['long_name'] = 'Contents'
    header_data['mod_chapter'] = ''
    header_data['mod_date'] = str(datetime.datetime.now()).split('.')[0]
    header_data['mod_options'] = ''
    header_data['build_cmap'] = str(config.build_cmap).lower()
    header_data['unicode_directive'] = rst_header_unicode if not slides else ''

    # Generate the index.rst file
    with codecs.open(config.book_src_dir + 'index.rst', 'w+', "utf-8") as index_rst:
        index_rst.write(index_header.format(config.start_chap_num))
        index_rst.write(rst_header % header_data)

        # Process all the chapter and module information
        process_section(config, config.chapters, index_rst, 0)

        index_rst.write(".. toctree::\n")
        index_rst.write("   :maxdepth: 3\n\n")

        # Process the Gradebook and Registerbook as well
        if not slides:
            process_module(config, mod_path='Gradebook', index_rst=index_rst)
            process_module(
                config, mod_path='RegisterBook', index_rst=index_rst)
            process_module(
                config, mod_path='CreateCourse', index_rst=index_rst)

        # If a ToDo file will be generated, append it to index.rst
        if len(todo_list) > 0:
            index_rst.write("   ToDo\n")

        index_rst.write("\n")
        index_rst.write("* :ref:`genindex`\n")
        index_rst.write("* :ref:`search`\n")


def generate_todo_rst(config, slides=False):
    """Sorts the list of ToDo directives (generated while recursively processing each module) by type and writes them all out to a file"""
    print '\nGenerating ToDo file...'

    # Sort the list of todo items by type (module_name, type, todo_directive)
    sorted_todo_list = sorted(todo_list, key=lambda todo: todo[2])

    with open(''.join([config.book_src_dir, 'ToDo.rst']), 'w') as todo_file:
        header_data = {}
        header_data['mod_name'] = 'ToDo'
        header_data['long_name'] = 'ToDo'
        header_data['dispModComp'] = False
        header_data['mod_chapter'] = ''
        header_data['mod_date'] = str(datetime.datetime.now()).split('.')[0]
        header_data['mod_options'] = ''
        header_data['build_cmap'] = str(config.build_cmap).lower()
        header_data[
            'unicode_directive'] = rst_header_unicode if not slides else ''
        todo_file.write(rst_header % header_data)
        todo_file.write(todo_rst_template)

        current_type = ''

        for (todo_id, mod_name, todo_type, todo_directive) in sorted_todo_list:
            if todo_type == '':
                todo_type = 'No Category'

            # Whenever a new type is encountered, print a header for that type
            if current_type != todo_type:
                todo_file.write(
                    '.. raw:: html\n\n   <hr /><h1>%s</h1><hr />\n\n' % todo_type)
                current_type = todo_type

            # Write a header with the name of the file where the ToDo
            # originated that hyperlinks directly to the original ToDo
            todo_file.write('.. raw:: html\n\n   <h2><a href="' + mod_name +
                            '.html#' + todo_id + '">source: ' + mod_name + '</a></h2>\n\n')

            # Clean up and write the TODO directive itself
            todo_file.write(
                '\n'.join(todo_directive).encode('utf-8').strip() + '\n\n')


def initialize_output_directory(config):
    """Creates the output directory (if applicable) and copies the necesssary files to it"""
    # Create the output directory if it doesn't exist
    # Will actually create '<build_dir>/<book_name>/source/Images/'
    distutils.dir_util.mkpath(config.book_src_dir + 'Images/')

    # Copy _static from RST/ to the book source directory
    distutils.dir_util.copy_tree(
        config.odsa_dir + 'RST/_static/', config.book_src_dir + '_static', update=1)

    # Copy config file to _static directory
    distutils.file_util.copy_file(
        config.config_file_path, config.book_src_dir + '_static/')

    # Copy translation file to _static directory
    distutils.file_util.copy_file(
        config.lang_file, config.book_src_dir + '_static/')

    # Create source/_static/config.js in the output directory
    # Used to set global settings for the client-side framework
    with open(config.book_src_dir + '_static/config.js', 'w') as config_js:
        config_js.writelines(config_js_template % config)

    # Create an index.html page in the book directory that redirects the user
    # to the book_output_dir
    with open(config.book_dir + 'index.html', 'w') as index_html:
        index_html.writelines(
            index_html_template % config.rel_book_output_path)


def initialize_conf_py_options(config, slides):
    """Initializes the options used to generate conf.py"""
    options = {}
    options['title'] = config.title
    options['book_name'] = config.book_name
    options['exercise_server'] = config.exercise_server
    options['logging_server'] = config.logging_server
    options['score_server'] = config.score_server
    options['module_origin'] = config.module_origin
    options['theme_dir'] = config.theme_dir
    options['theme'] = config.theme
    options['odsa_dir'] = config.odsa_dir
    options['book_dir'] = config.book_dir
    options['code_dir'] = config.code_dir
    options['tabbed_code'] = config.tabbed_codeinc
    options['code_lang'] = json.dumps(config.code_lang)
    options['text_lang'] = json.dumps(config.lang)
    # convert the translation text into unicode sstrings
    tmpSTR = ''
    for k, v in config.text_translated.iteritems():
        tmpSTR = tmpSTR + '"%s":u"%s",' % (k, v)
    options['text_translated'] = tmpSTR
    options['av_root_dir'] = config.av_root_dir
    options['exercises_root_dir'] = config.exercises_root_dir
    # The relative path between the ebook output directory (where the HTML
    # files are generated) and the root ODSA directory
    options['eb2root'] = config.rel_build_to_odsa_path
    options['rel_book_output_path'] = config.rel_book_output_path
    options['slides_lib'] = 'hieroglyph' if slides else ''

    return options


def create_chapter(request_ctx, config, course_id, course_code, module_id, module_position, chapter_name, chapter_obj, LTI_url, **kwargs):
    """ Create canvas module that corresponds to OpenDSA chapter """

    module_item_position = 1

    for module in chapter_obj:
        module_obj = chapter_obj[str(module)]
        module_name = module_obj.get("long_name")
        module_name_url = module.split('/')[1] if '/' in module else module

        # OpenDSA module header will map to canvas text header
        results = modules.create_module_item(
            request_ctx, course_id, module_id, 'SubHeader',
            module_item_content_id=None,
            module_item_title=str(module_position) + "." + str(module_item_position) + ". " + module_name,
            module_item_indent=0)

        module_item_position += 1
        # exercises = module_obj.get("exercises")
        sections = module_obj.get("sections")
        if bool(sections):
            section_couter = 1
            # for exercise in exercises:
            for section in sections:
                section_obj = sections[section]
                section_name = section
                showsection = section_obj.get("showsection")
                no_exercise = 1
                for attr in section_obj:
                    if isinstance(section_obj[attr], dict):
                        # if len(section_obj[attr] > 0):
                        exercise_obj = section_obj[attr]
                        exercise_name = attr
                        long_name = exercise_obj.get("long_name")
                        required = exercise_obj.get("required")
                        points = exercise_obj.get("points")
                        threshold = exercise_obj.get("threshold")
                        if long_name is not None and required is not None and points is not None and threshold is not None:
                            # print(str(section_couter).zfill(2)) + " " + long_name
                            # OpenDSA exercises will map to canvas assignments
                            if showsection is None or (showsection is not None and showsection == True):
                                results = assignments.create_assignment(
                                    request_ctx,
                                    course_id,
                                    section_name,
                                    assignment_submission_types="external_tool",
                                    assignment_external_tool_tag_attributes={
                                        "url": LTI_url + "/lti_tool?problem_type=module&problem_url=" + course_code + "&short_name=" + module_name_url + "-" + str(section_couter).zfill(2)},
                                    assignment_points_possible=points,
                                    assignment_description=section_name)
                                assignment_id = results.json().get("id")

                                config.chapters[chapter_name][str(module)]["sections"][section_name]["item_id"] = assignment_id
                                # add assignment to module
                                results = modules.create_module_item(
                                    request_ctx,
                                    course_id,
                                    module_id,
                                    'Assignment',
                                    module_item_content_id=assignment_id,
                                    module_item_indent=1)
                            section_couter += 1
                            no_exercise = 0
                if no_exercise == 1:
                    if showsection is None or (showsection is not None and showsection == True):
                        results = assignments.create_assignment(
                            request_ctx,
                            course_id,
                            section_name,
                            assignment_submission_types="external_tool",
                            assignment_external_tool_tag_attributes={
                                "url": LTI_url + "/lti_tool?problem_type=module&problem_url=" + course_code + "&short_name=" + module_name_url + "-" + str(section_couter).zfill(2)},
                            assignment_points_possible=0,
                            assignment_description=section_name)
                        assignment_id = results.json().get("id")

                        config.chapters[chapter_name][str(module)]["sections"][section_name]["item_id"] = assignment_id
                        # add assignment to module
                        results = modules.create_module_item(
                            request_ctx,
                            course_id,
                            module_id,
                            'Assignment',
                            module_item_content_id=assignment_id,
                            module_item_indent=1)
                    section_couter += 1
        else:
            results = assignments.create_assignment(
                request_ctx,
                course_id,
                module_name,
                assignment_submission_types="external_tool",
                assignment_external_tool_tag_attributes={
                    "url": LTI_url + "/lti_tool?problem_type=module&problem_url=" + course_code + "&short_name=" + module_name_url},
                assignment_points_possible=0,
                assignment_description=module_name)
            assignment_id = results.json().get("id")
            config.chapters[chapter_name][str(module)]["item_id"] = assignment_id
            # add assignment to module
            results = modules.create_module_item(
                request_ctx,
                course_id,
                module_id,
                'Assignment',
                module_item_content_id=assignment_id,
                module_item_indent=1)
    # publish the module
    results = modules.update_module(request_ctx, course_id, module_id,
                                    module_published=True)

    # print(json.dumps(config.__dict__))


def create_course(config):
    """Create course on target LMS (e.g. canvas)"""

    # load LMS config file
    # Throw an error if the specified LMS config files doesn't exist
    LMS_config = config.config_file_path[:-5] + '_LMSconf.json'
    if not os.path.exists(LMS_config):
        print_err("ERROR: File %s doesn't exist\n" % LMS_config)
        sys.exit(1)

    # Try to read the configuration file data as JSON
    try:
        with open(LMS_config) as config_file:
            LMS_conf_data = json.load(config_file, object_pairs_hook=collections.OrderedDict)
    except ValueError, err:
        # Error message handling based on validate_json.py (https://gist.github.com/byrongibson/1921038)
        msg = err.message
        print_err(msg)

    for attr in LMS_conf_data:
        config[attr] = LMS_conf_data[attr]

    course_code = config['course_code']
    privacy_level = "public"  # should be public
    config_type = "by_url"
    LTI_url = config["LTI_url"]

    print "\nCreating course in " + config.target_LMS + " LMS " + config.LMS_url + '\n'
    # init the request context
    request_ctx = RequestContext(config['access_token'], config['LMS_url'] + "/api")

    # get course_id
    results = courses.list_your_courses(request_ctx,
                                        'total_scores')
    # TODO: Proper error message when the course is not created yet.
    for i, course in enumerate(results.json()):
        if course.get("course_code") == course_code:
            course_id = course.get("id")

    # save course_id
    config['course_id'] = course_id

    # configure the course external_tool
    results = external_tools.create_external_tool_courses(
        request_ctx, course_id, "OpenDSA-LTI",
        privacy_level, config["LTI_consumer_key"], config["LTI_secret"],
        config_type=config_type, config_url=LTI_url + "/tool_config.xml")

    # update the course name
    course_name = config.title
    results = courses.update_course(
        request_ctx, course_id, course_name=course_name)

    chapters = config.chapters

    module_position = 1
    # create course modules and assignments
    for chapter in chapters:
        chapter_name = str(chapter)
        chapter_obj = chapters[str(chapter)]
        # OpenDSA chapters will map to canvas modules
        results = modules.create_module(
            request_ctx, course_id, "Chapter " + str(module_position - 1) + " " + str(chapter), module_position=module_position)
        module_id = results.json().get("id")
        t = threading.Thread(target=create_chapter, args=(request_ctx, config, course_id, course_code, module_id, module_position - 1, chapter_name, chapter_obj, LTI_url))
        t.start()
        module_position += 1


def register_book(config):
    """Register Book in OpenDSA-server"""

    url = config.logging_server + '/api/v1/module/loadbook/'
    headers = {'content-type': 'application/json'}

    print "\nRegistring Book in OpenDSA-server " + config.logging_server + '\n'
    response = requests.post(url, data=json.dumps(config.__dict__), headers=headers, verify=False)
    response_obj = json.loads(response.content)

    if response_obj['saved']:
      print "\nBook was registered successfully\n"
    else:
      print "\nSomthing wrong happened ...\n"


def configure(config_file_path, options):
    """Configure an OpenDSA textbook based on a validated configuration file"""
    global satisfied_requirements

    slides = options.slides

    print "Configuring OpenDSA, using " + config_file_path

    # Load and validate the configuration
    config = ODSA_Config(config_file_path, options.output_directory)

    # Register book in OpenDSA-server and create course in target LMS
    if options.create_course=='True':
        create_course(config)
        register_book(config)

    # Delete everything in the book's HTML directory, otherwise the
    # post-processor can sometimes append chapter numbers to the existing HTML
    # files, making the numbering incorrect
    html_dir = config.book_dir + config.rel_book_output_path
    if os.path.isdir(html_dir):
        print "Clearing HTML directory"
        shutil.rmtree(html_dir)

    # Add the list of topics the book assumes students know to the list of
    # fulfilled prereqs
    if config.assumes:
        satisfied_requirements += [a.strip()
                                   for a in config.assumes.split(';')]

    # Optionally rebuild JSAV
    if config.build_JSAV:
        print "Building JSAV\n"
        status = 0

        with open(os.devnull, "w") as fnull:
            status = subprocess.check_call(
                'make -s -C %s' % (config.odsa_dir + 'JSAV/'), shell=True, stdout=fnull)

        if status != 0:
            print_err("JSAV make failed")
            print_err(status)
            sys.exit(1)

    print "Writing files to " + config.book_dir + "\n"

    # Initialize output directory, create index.rst, and process all of the
    # modules
    initialize_output_directory(config)
    generate_index_rst(config, slides)

    # Print out a list of any exercises found in RST files that do not appear
    # in the config file
    if len(missing_exercises) > 0:
        print_err("\nExercises Not Listed in Config File:")

        for exercise in missing_exercises:
            print_err('  ' + exercise)

        # Print an extra line to separate this section from any additional
        # errors
        print_err('')

    # Stop if we are just running a dry-run
    if options.dry_run:
        return

    # Entries are only added to todo_list if config.suppress_todo is False
    if len(todo_list) > 0:
        generate_todo_rst(config, slides)

    # Dump num_ref_map to table.json to be used by the Sphinx directives
    with open(config.book_dir + 'table.json', 'w') as num_ref_map_file:
        json.dump(num_ref_map, num_ref_map_file)

    # Dump module_chap_map to page_chapter.json to be used by the avmetadata directive
    # NOTE: avmetadata is deprecated (it was used to generate the concept map but is no longer used)
    # If avmetadata is eventually removed, we can stop writing this file
    with open(config.book_dir + 'page_chapter.json', 'w') as page_chapter_file:
        json.dump(module_chap_map, page_chapter_file)

    # Initialize options for conf.py
    options = initialize_conf_py_options(config, slides)

    # Create a Makefile in the output directory
    with open(config.book_dir + 'Makefile', 'w') as makefile:
        makefile.writelines(makefile_template % options)

    # Create conf.py file in output source directory
    with codecs.open(config.book_src_dir + 'conf.py', 'w', "utf-8") as conf_py:
        conf_py.writelines(conf % options)

    # Copy only the images used by the book from RST/Images/ to the book
    # source directory
    for image in images:
        distutils.file_util.copy_file(
            '%sRST/Images/%s' % (config.odsa_dir, image), config.book_src_dir + 'Images/')

    # Run make on the output directory
    print '\nBuilding textbook...'

    if slides:
        proc = subprocess.Popen(
            ['make', '-C', config.book_dir, 'slides'], stdout=subprocess.PIPE)
    else:
        proc = subprocess.Popen(
            ['make', '-C', config.book_dir], stdout=subprocess.PIPE)
    for line in iter(proc.stdout.readline, ''):
        print line.rstrip()

    # Calls the postprocessor to update chapter, section, and module numbers,
    # and glossary terms definition
    update_TOC(config.book_src_dir, config.book_dir +
               config.rel_book_output_path, module_chap_map)
    if 'Glossary' in processed_modules:
        update_TermDef(
            config.book_dir + config.rel_book_output_path + 'Glossary.html', cmap_map['concepts'])

        # Create the concept map definition file in _static html directory
        with codecs.open(config.book_dir + 'html/_static/GraphDefs.json', 'w', 'utf-8') as graph_defs_file:
            json.dump(cmap_map, graph_defs_file)
    make_lti(config)

# Code to execute when run as a standalone program
if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-s", "--slides", help="Causes configure.py to create slides",
                      dest="slides", action="store_true", default=False)
    parser.add_option("--dry-run", help="Causes configure.py to configure the book but stop before compiling it",
                      dest="dry_run", action="store_true", default=False)
    parser.add_option("-o", help="Accepts a custom directory name instead of using the config file's name.",
                      dest="output_directory", default=None)
    parser.add_option("-c", "--create_course", help="Causes configure.py to create course in target LMS", default=False)
    (options, args) = parser.parse_args()

    if options.slides:
        os.environ['SLIDES'] = 'yes'
    else:
        os.environ['SLIDES'] = 'no'

    # Process script arguments
    if len(args) != 1:
        print_err(
            "Usage: " + sys.argv[0] + " [-s] [--dry-run] config_file_path [-c]")
        sys.exit(1)

    configure(args[0], options)
