import os
import random
import copy

from src.issue_similarity import extract_max_match


SIMILARITY_THRESHOLD = .50
SIMILARITY_THRESHOLD2 = .80


def get_random_report(reports):
    return random.choice(list(reports.keys()))


def find_report_with_max_issues(reports):
    max_issues = -1
    reports_with_max_issues = []
    for key, report in reports.items():
        issue_count = len(report.issues)
        if issue_count > max_issues:
            max_issues = issue_count
            reports_with_max_issues = [key]
        elif issue_count == max_issues:
            reports_with_max_issues.append(key)

    # Check if a file was found with issues
    if not reports_with_max_issues:
        return get_random_report(reports)

        # Return a random file from the files with the maximum number of issues
    return random.choice(reports_with_max_issues)


def find_report_with_min_issues(reports):
    min_issues = 10000
    reports_with_min_issues = []
    for key, report in reports.items():
        issue_count = len(report.issues)
        if issue_count < min_issues:
            min_issues = issue_count
            reports_with_min_issues = [report]
        elif issue_count == min_issues:
            reports_with_min_issues.append(report)

    # Check if a file was found with issues
    if not reports_with_min_issues:
        return get_random_report()

        # Return a random file from the files with the maximum number of issues
    return random.choice(reports_with_min_issues)


def extract_matching_issue(compared_issue, original_issues):
    text_to_compare = extract_text(compared_issue)

    for original_issue in original_issues:
        original_text = extract_text(original_issue)
        if text_to_compare == original_text:
            return original_issue


def remove_duplicates(file, issues):
    i = 0
    while i < len(issues):
        issue = issues[i]
        # print(issue['issue_title'])
        comparing_issues = issues[i + 1:]
        # print_titles(comparing_issues)
        if len(comparing_issues) == 0:
            break

        base_text = extract_text(issue)
        texts_to_compare = [extract_text(comparing_issue) for comparing_issue in comparing_issues]
        max_score, similarity_scores = extract_max_match(base_text, texts_to_compare)

        if max_score >= SIMILARITY_THRESHOLD2:
            max_score_index = similarity_scores.index(max_score)
            matching_issue = extract_matching_issue(comparing_issues[max_score_index], issues)
            # print(f"{issue['issue_title']} <{max_score}> {matching_issue['issue_title']}")
            issues.remove(matching_issue)
            if 'matching_issues' not in issue:
                issue['matching_issues'] = []
            issue['matching_issues'].append({file, max_score_index, max_score})
        i += 1


def extract_text(issue):
    return f"Title: {issue['issue_title']}\nDescription: {issue['issue_description']}"


def compare_files(file, all_issues, new_issues):
    for existing_issue in all_issues:
        base_text = extract_text(existing_issue)
        texts_to_compare = [extract_text(issue) for issue in new_issues]
        max_score, similarity_scores = extract_max_match(base_text, texts_to_compare)

        if max_score >= SIMILARITY_THRESHOLD:
            max_score_index = similarity_scores.index(max_score)
            matching_issue = new_issues[max_score_index]
            new_issues.remove(matching_issue)
            if 'matching_issues' not in existing_issue:
                existing_issue['matching_issues'] = []
            existing_issue['matching_issues'].append({file, max_score_index, max_score})

        if len(new_issues) == 0:
            break

    for remaining_issue in new_issues:
        all_issues.append(remaining_issue)


def find_all_unique_issues(reports, report_max):
    first_report = reports.pop(report_max)

    all_issues = first_report.issues
    remove_duplicates(first_report, all_issues)

    for report in reports:
        new_issues = report.issues
        # remove_duplicates(file, new_issues)
        compare_files(report, all_issues, new_issues)

    remove_duplicates('all', all_issues)
    return all_issues


def calculate_occurences(issue):
    if 'matching_issues' not in issue:
        return 1
    return len(issue['matching_issues'])+1


def find_common_issues(report_num, all_issues):
    # print(report_num)
    common_issues = []
    for issue in all_issues:
        if calculate_occurences(issue) >= report_num-1:
            common_issues.append(issue)
    return common_issues


def create_new_report(issues, filename, project):
    keys_to_extract = ['issue_title', 'issue_description', 'timestamps']
    dest_filepath = "model-outputs/" + project

    if not os.path.exists(dest_filepath):
        os.makedirs(dest_filepath)

    with open(os.path.join(dest_filepath, filename), 'w') as file:
        for item in issues:
            for key in keys_to_extract:
                value = item.get(key, 'N/A')  # 'N/A' will be used if the key does not exist
                file.write(f"{key}: {str(value).replace('[', '').replace(']', '')}\n")
            file.write("\n")  # Separate each dictionary's data with a newline


def run_report_selection(reports, session, project):
    report_random = get_random_report(reports)
    report_max = find_report_with_max_issues(reports)
    report_min = find_report_with_min_issues(reports)

    issues_all = find_all_unique_issues(copy.deepcopy(reports), report_max)
    issues_common = find_common_issues(len(reports.items()), copy.deepcopy(issues_all))

    ## save these files in another folder with similar structure

    create_new_report(report_random.issues, f"{session}-random.txt", project)
    create_new_report(report_max.issues, f"{session}-max.txt", project)
    create_new_report(report_min.issues, f"{session}-min.txt", project)
    create_new_report(issues_all, f"{session}-all.txt", project)
    create_new_report(issues_common, f"{session}-common.txt", project)
