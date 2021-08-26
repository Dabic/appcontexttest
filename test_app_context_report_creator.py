from os import listdir
from os.path import isfile, join
from xml.dom import minidom
import time
import argparse

SYSTEM_OUT_TAG_NAME = "system-out"
NEW_APPLICATION_CONTEXT_INDICATOR = "Storing ApplicationContext in cache under key"
APPLICATION_CONTEXT_STATISTICS_INDICATOR = "Spring test ApplicationContext cache statistics"
MISS_COUNT_INDICATOR = "missCount = "
LIMIT_POSITION = 0
COUNT_POSITION = 1
REPORT_FILE_NAME = "app_context_test_report.txt"
TEST_RESULTS_PATH = "./build/test-results/test/" # run tests using gradle in order to generate test reports on this path 
COUNT_AND_LIMIT_DELIMITER = "="
LIMIT_KEY = "limit"
COUNT_KEY = "count"
LIMIT = 3
DEFAULT_MODE = 1
CREATE_REPORT_MODE = 2
LOG_DIFF_MODE = 3
ARGS_MODE_KEY = "mode"

def parse_test_results_and_populate_report():
    test_files = [f for f in listdir(TEST_RESULTS_PATH) if isfile(join(TEST_RESULTS_PATH, f))]
    for xml_test_file in test_files:
        print(xml_test_file)
        xmldoc = minidom.parse(TEST_RESULTS_PATH + xml_test_file)
        sysout_node = xmldoc.getElementsByTagName(SYSTEM_OUT_TAG_NAME)
        if is_log_empty(sysout_node) is True:
            continue
        sysout_text = sysout_node[0].firstChild.nodeValue
        if is_context_created(sysout_text) is True:
            write_test_name_to_file(get_class_name_from_xml_file_name(xml_test_file))
    set_app_context_count(quick_parse_app_context_count_from_statistics())

# Untested
def parse_test_results_and_populate_report_performant():
    test_files = [f for f in listdir(TEST_RESULTS_PATH) if isfile(join(TEST_RESULTS_PATH, f))]
    for xml_test_file in test_files:
        if is_context_created_performant(xml_test_file) is True:
            write_test_name_to_file(get_class_name_from_xml_file_name(xml_test_file))
    set_app_context_count(quick_parse_app_context_count_from_statistics())

def is_log_empty(sysout_node):
    return sysout_node[0].firstChild is None

def is_context_created(test_log):
    print("ALO")
    if NEW_APPLICATION_CONTEXT_INDICATOR in test_log:
        return True
    return False

# Untested
def is_context_created_performant(test_file):
    with open(TEST_RESULTS_PATH + test_file, encoding="utf8") as f:
        for index, line in enumerate(f): # Performance issue, do not read the whole file, iterate through file reference instead
            if NEW_APPLICATION_CONTEXT_INDICATOR in line.strip():
                return True
    return False

def write_test_name_to_file(test_name):
    report_file = open(REPORT_FILE_NAME, "a+")
    report_file.write(test_name + "\n")
    report_file.close()

def set_app_context_count(count):
    report_file = open(REPORT_FILE_NAME, "r+")
    lines = report_file.readlines()
    lines[COUNT_POSITION] = "{}{}{}\n".format(COUNT_KEY, COUNT_AND_LIMIT_DELIMITER, count)
    report_file.close()
    report_file = open(REPORT_FILE_NAME, "w+")
    report_file.writelines(lines)
    report_file.close()

def quick_parse_app_context_count_from_statistics():
    test_files = [f for f in listdir(TEST_RESULTS_PATH) if isfile(join(TEST_RESULTS_PATH, f))]
    last_position = len(test_files) - 1
    for xml_test_file_pos in range(last_position, -1, -1):
        xmldoc = minidom.parse(TEST_RESULTS_PATH + test_files[xml_test_file_pos]) # bad for performance, iterate through file reference instead
        sysout_node = xmldoc.getElementsByTagName(SYSTEM_OUT_TAG_NAME)
        if is_log_empty(sysout_node) is True:
            continue
        sysout_lines = sysout_node[0].firstChild.nodeValue.split("\n")
        sysout_line_pos = len(sysout_lines) - 1
        for line_pos in range(sysout_line_pos, -1, -1):
            line = sysout_lines[line_pos]
            if APPLICATION_CONTEXT_STATISTICS_INDICATOR in line:
                miss_count_indicator_index = line.index(MISS_COUNT_INDICATOR)
                miss_count_rest = [line[w] for w in range(miss_count_indicator_index + len(MISS_COUNT_INDICATOR), len(line))]
                count = ''
                for char in miss_count_rest:
                    if char.isnumeric() is True:
                        count += char
                return count
    return 0

def create_app_context_report_file():
    report_file = open(REPORT_FILE_NAME, "w+")
    report_file.write("{}{}{}\n".format(LIMIT_KEY, COUNT_AND_LIMIT_DELIMITER, LIMIT))
    report_file.write("{}{}{}\n".format(COUNT_KEY, COUNT_AND_LIMIT_DELIMITER, 0))
    report_file.close()
    

def get_class_name_from_xml_file_name(xml_file_name):
    return xml_file_name[5:-4]

def is_limit_exceeded():
    report_file = open(REPORT_FILE_NAME, "r")
    lines = report_file.readlines()
    current_context_count = int(lines[COUNT_POSITION].strip().split(COUNT_AND_LIMIT_DELIMITER)[1])
    current_limit = int(lines[LIMIT_POSITION].strip().split(COUNT_AND_LIMIT_DELIMITER)[1])
    report_file.close()
    if current_context_count > current_limit:
        return True
    return False

def compare_test_reports_and_show_diff(old_report_text_lines, new_report_text_lines):
    print("\nNew Problematic Tests:")
    for line in new_report_text_lines:
        if line.startswith(LIMIT_KEY) or line.startswith(COUNT_KEY):
            continue
        if line not in old_report_text_lines:
            print(line.strip())
            
    print("\nResolved Tests:")
    for line in old_report_text_lines:
        if line.startswith(LIMIT_KEY) or line.startswith(COUNT_KEY):
            continue
        if line not in new_report_text_lines:
            print(line.strip())

def main():
    parser = argparse.ArgumentParser(description="Report execution mode")
    parser.add_argument(ARGS_MODE_KEY, metavar="{}".format(ARGS_MODE_KEY), type=int, default=1, help="1 - only get quick results from script execution; 2 - create report file and get result from script execution; 3 - log diff and get result from script execution\n")
    args = parser.parse_args()
    start_time = time.time()

    if int(args.mode) == DEFAULT_MODE:
        print("Geting quick results...")
        current_count = quick_parse_app_context_count_from_statistics()
        print("Current count: " + str(current_count))
        print("Limit: " + str(LIMIT))
        if int(current_count) > LIMIT:
            print("Limit exceeded! Build will fail!")
        else:
            print("You are cool!")

    elif int(args.mode) == CREATE_REPORT_MODE:
        print("Creating report...")
        create_app_context_report_file()
        parse_test_results_and_populate_report_performant()
        if is_limit_exceeded() is True:
            print("Limit exceeded! Build will fail!")
        else:
            print("Limit not exceeded! Build will succeed!")

    elif int(args.mode) == LOG_DIFF_MODE:
        previous_test_report = open(REPORT_FILE_NAME, "r+")
        previous_test_report_text_lines = previous_test_report.readlines()
        previous_test_report.close()
        print("Creating report...")
        create_app_context_report_file()
        parse_test_results_and_populate_report_performant()
        current_test_report = open(REPORT_FILE_NAME, "r+")
        current_test_report_text_lines = current_test_report.readlines()
        current_test_report.close()
        print("Calculating diff...")
        compare_test_reports_and_show_diff(previous_test_report_text_lines, current_test_report_text_lines)
        if is_limit_exceeded() is True:
            print("Limit exceeded! Build will fail!")
        else:
            print("Limit not exceeded! Build will succeed!")
    print("Done. Process took {:.3f}s to finish.".format(time.time() - start_time))

main()