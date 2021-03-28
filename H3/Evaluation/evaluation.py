import os
import subprocess
import filecmp
import time

from google.cloud import datastore
from google.cloud import storage

GPC_DATASTORE_KIND_EVALUATION = 'Evaluation'
GPC_DATASTORE_KIND_PROBLEM = 'Problem'

GPC_STORAGE_TESTS_BUCKET = 'problems-test-cases'
GPC_STORAGE_EVALUATIONS_BUCKET = 'evaluation-submissions'

WORK_DIRECTORY_PREFIX = 'evaluations'

CORRECT_ANSWER_FLAG = 0
WRONG_ANSWER_FLAG = 1
TIME_LIMIT_EXCEEDED_FLAG = 2
OUTPUT_FILE_MISSING_FLAG = 3


def get_delimiter():
    if os.name == 'nt':
        return '\\'
    else:
        return '/'


def process_files(files):
    names = []
    for blob in files:
        names.append(str(blob.name))
    return sorted(names)


def create_working_directory(evaluation_id):
    dir_path = '.' + get_delimiter() + WORK_DIRECTORY_PREFIX + get_delimiter() + evaluation_id
    if os.path.exists(dir_path):
        return
    try:
        os.mkdir(dir_path)
    except Exception as e:
        print(e)


def download_file_from_storage(storage_client, bucket, file_name, file_path):
    blob = storage.Blob(file_name, bucket)
    with open(file_path, "wb") as file_out:
        storage_client.download_blob_to_file(blob, file_out)
    return file_path


def download_source_code(storage_client, sources_bucket, evaluation_id):
    source_code_file_name = str(evaluation_id) + '.cpp'
    source_code_file_path = '.' + get_delimiter() + WORK_DIRECTORY_PREFIX + \
        get_delimiter() + evaluation_id + get_delimiter() + source_code_file_name

    return download_file_from_storage(storage_client, sources_bucket,
                                      source_code_file_name, source_code_file_path)


def compile_source_code(source_code_file_path, evaluation_id):
    source_code_executable_path = '.' + get_delimiter() + \
        WORK_DIRECTORY_PREFIX + get_delimiter() + evaluation_id + get_delimiter() + evaluation_id + '.exe'

    command_parts = [
        'g++',
        '-std=c++1y',
        '-o',
        source_code_executable_path,
        source_code_file_path
    ]
    exit_code = subprocess.run(command_parts)

    return (exit_code.returncode, source_code_executable_path)


def create_evaluation_file(storage_client, test_cases_bucket, evaluation_id,
                           remote_file_name, file_name_prefix, file_prefix):
    source_file_in_path = '.' + get_delimiter() + WORK_DIRECTORY_PREFIX + \
        get_delimiter() + evaluation_id + get_delimiter() + file_name_prefix + file_prefix

    download_file_from_storage(storage_client, test_cases_bucket,
                               remote_file_name, source_file_in_path)
    return source_file_in_path


def execute_source_code(source_code_executable_path, time_limit):
    command_parts = [
        source_code_executable_path
    ]

    p = subprocess.Popen(command_parts, shell=True)
    print('Process started: {}'.format(time.time()))
    time.sleep(time_limit)
    print('Process finished: {}'.format(time.time()))

    if p.poll() == None:
        # The process hasn't finished
        p.terminate()
        return TIME_LIMIT_EXCEEDED_FLAG

    # The execution has finished successfully
    return True


def evaluate_executable_output(ok_file_path, evaluation_id, file_name_prefix):
    out_file_path = '.' + get_delimiter() + WORK_DIRECTORY_PREFIX + \
        get_delimiter() + evaluation_id + get_delimiter() + file_name_prefix + '.out'

    if not os.path.exists(out_file_path):
        return OUTPUT_FILE_MISSING_FLAG

    if not filecmp.cmp(ok_file_path, out_file_path, shallow=False):
        return WRONG_ANSWER_FLAG

    return CORRECT_ANSWER_FLAG


def evaluate_source_code(storage_client, test_cases_bucket, evaluation_obj, source_code_executable_path,
                         input_file_names, output_file_names, evaluation_id, file_name_prefix):
    time_limit = 1.0
    score = 0.0
    score_per_test = 100.0 / \
        (min(len(input_file_names), len(output_file_names)))
    for (inp, outp) in zip(input_file_names, output_file_names):
        create_evaluation_file(
            storage_client, test_cases_bucket, evaluation_id, inp, file_name_prefix, '.in')
        ok_file_path = create_evaluation_file(
            storage_client, test_cases_bucket, evaluation_id, outp, file_name_prefix, '.ok')

        if execute_source_code(source_code_executable_path, time_limit) == TIME_LIMIT_EXCEEDED_FLAG:
            # Time limit exceeded
            pass
        else:
            evaluation_stats = evaluate_executable_output(
                ok_file_path, evaluation_id, file_name_prefix)
            if evaluation_stats == WRONG_ANSWER_FLAG:
                # Wrong answer
                pass
            elif evaluation_stats == OUTPUT_FILE_MISSING_FLAG:
                # Output file missing
                pass
            elif evaluation_stats == CORRECT_ANSWER_FLAG:
                # Correct answer
                score += score_per_test
            else:
                raise "Internal server error!"
    evaluation_obj['verdict'] = str(score)


def evaluate(evaluation_id):
    datastore_client = datastore.Client()

    evaluation_obj_key = datastore_client.key(
        GPC_DATASTORE_KIND_EVALUATION, int(evaluation_id))
    evaluation_obj = datastore_client.get(evaluation_obj_key)
    if evaluation_obj is None:
        return ("Invalid evaluation_id in body! The evaluation doesn't exist!", 400)

    problem_id = int(evaluation_obj['problemId'])
    problem_obj_key = datastore_client.key(
        GPC_DATASTORE_KIND_PROBLEM, problem_id)
    problem_obj = datastore_client.get(problem_obj_key)
    if problem_obj is None:
        return ("Internal logic error! The evaluation contains an invalid problem_id!", 500)

    evaluation_obj['status'] = 'Evaluating'
    datastore_client.put(evaluation_obj)

    storage_client = storage.Client()
    test_cases_bucket = storage_client.get_bucket(GPC_STORAGE_TESTS_BUCKET)
    input_files = list(storage_client.list_blobs(
        test_cases_bucket, prefix=str(problem_id) + '/input'))
    output_files = list(storage_client.list_blobs(
        test_cases_bucket, prefix=str(problem_id) + '/output'))

    input_file_names = process_files(input_files)
    output_file_names = process_files(output_files)

    create_working_directory(evaluation_id)

    sources_bucket = storage_client.get_bucket(GPC_STORAGE_EVALUATIONS_BUCKET)
    source_code_file_path = download_source_code(
        storage_client, sources_bucket, evaluation_id)

    compilation_info = compile_source_code(
        source_code_file_path, evaluation_id)
    if compilation_info[0] != 0:
        evaluation_obj['verdict'] = 'Compilation failed!'
    else:
        evaluate_source_code(storage_client, test_cases_bucket, evaluation_obj, compilation_info[1],
                             input_file_names, output_file_names, evaluation_id, problem_obj['file'])

    evaluation_obj['status'] = 'Completed'
    datastore_client.put(evaluation_obj)
    return ("The evaluation was completed successfully!", 200)
