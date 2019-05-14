from multiprocessing import Pool
from utils.classes import local_breach_target
from utils.colors import colors as c
from utils.localsearch import raw_in_count, progress
import gzip
import os
import sys


def progress_gzip(count):
    """
    Prints count without rewriting to stdout
    """
    sys.stdout.write("Lines checked:%i\r" % (count))
    sys.stdout.write("\033[K")


def gzip_worker(filepath, target_list):
    """
    Searches for every email from target_list in every line of filepath.
    Uses python native gzip lib to decompress file line by line.
    Archives with multiple files are read as long single files. 
    Attempts to decode line using utf-8. If it fails, catch and use raw data.
    """
    try:
        found_list = []
        size = os.stat(filepath).st_size
        with gzip.open(filepath, "r") as gzipfile:
            c.info_news(
                c,
                "Worker [{PID}] is searching for targets in {filepath} ({size} bytes)".format(
                    PID=os.getpid(), filepath=filepath, size=size
                ),
            )
            for cnt, line in enumerate(gzipfile):
                for t in target_list:
                    if t in str(line):
                        try:
                            decoded = str(line, "utf-8")
                            found_list.append(
                                local_breach_target(t, filepath, cnt, decoded)
                            )
                            c.good_news(
                                c,
                                f"Found occurrence [{filepath}] Line {cnt}: {decoded}",
                            )
                        except Exception as e:
                            c.bad_news(
                                c, f"Got a decoding error line {cnt} - file: {filepath}"
                            )
                            c.good_news(
                                c, f"Found occurrence [{filepath}] Line {cnt}: {line}"
                            )
                            found_list.append(
                                local_breach_target(t, filepath, cnt, str(line))
                            )
        return found_list
    except Exception as e:
        c.bad_news(c, "Something went wrong with gzip worker")
        print(e)


def local_gzip_search(files_to_parse, target_list):
    """
    Receives list of all files to check for target_list.
    Starts a worker pool, one worker per file.
    Return list of local_breach_targets objects to be tranformed in target objects.
    """
    pool = Pool()
    found_list = []
    # Launch
    async_results = [
        pool.apply_async(gzip_worker, args=(f, target_list))
        for i, f in enumerate(files_to_parse)
    ]
    for r in async_results:
        if r.get() is not None:
            found_list.extend(r.get())
    pool.close()
    pool.join()
    return found_list


def local_search_single_gzip(files_to_parse, target_list):
    """
    Single process searching of every target_list emails, in every files_to_parse list.
    To be used when stability for big files is a priority
    Return list of local_breach_target objects to be tranformed in target objects
    """
    found_list = []
    for file_to_parse in files_to_parse:
        with gzip.open(file_to_parse, "r") as fp:
            size = os.stat(file_to_parse).st_size
            c.info_news(
                c,
                "Searching for targets in {file_to_parse} ({size} bytes)".format(
                    file_to_parse=file_to_parse, size=size
                ),
            )
            for cnt, line in enumerate(fp):
                progress_gzip(cnt)
                for t in target_list:
                    if t in str(line):
                        try:
                            decoded = str(line, "utf-8")
                            found_list.append(
                                local_breach_target(t, file_to_parse, cnt, decoded)
                            )
                            c.good_news(
                                c,
                                f"Found occurrence [{file_to_parse}] Line {cnt}: {decoded}",
                            )
                        except Exception as e:
                            c.bad_news(
                                c,
                                f"Got a decoding error line {cnt} - file: {file_to_parse}",
                            )
                            c.good_news(
                                c,
                                f"Found occurrence [{file_to_parse}] Line {cnt}: {line}",
                            )
                            found_list.append(
                                local_breach_target(t, file_to_parse, cnt, str(line))
                            )
    return found_list
