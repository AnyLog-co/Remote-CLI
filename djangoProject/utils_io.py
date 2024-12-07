"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/
"""

import sys
import os
import shutil

from fpdf import FPDF

def get_files_in_dir(path, size_flag):
    '''
    Return the list of files:
    path - path to directory
    size_flag - if True - returns a list of lists - every list include file name + size
    '''

    files_info = []
    try:
        files_list = os.listdir(path)
    except:
        files_list = None
    else:
        for file_name in files_list:
            if  size_flag:
                try:
                    file_size = os.path.getsize(path + file_name)
                except:
                    file_size = 0
            else:
                file_size = 0
            files_info.append([file_name, file_size])


    return files_info

def delete_file( file_path_name ):
    ret_val = True

    try:
        os.remove(file_path_name)
    except:
        ret_val = False

    return ret_val


def copy_file(des_file, source_file):

    ret_val = True

    try:
        shutil.copyfile(source_file, des_file)
    except:
        ret_val = False

    return ret_val

def read_file(file_name):
    '''
    file_name - pathe + file name
    '''

    try:
        with open(file_name) as f:
            data = f.read()
    except:
        errno, value = sys.exc_info()[:2]
        data = None

    return data

# -----------------------------------------------------------------------------------
# Write output as PDF file
# -----------------------------------------------------------------------------------
def to_pdf(path, filename, output):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Courier", size=12)
        pdf.multi_cell(0, 10, output)
        pdf.output(path + filename + ".pdf")

    except:
        errno, value = sys.exc_info()[:2]
        pass

