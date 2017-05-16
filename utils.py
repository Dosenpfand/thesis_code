""" Various uncomplex functionality"""

import sys
import time
import smtplib
from email.mime.text import MIMEText
import socket
import getpass
import gzip
import os
import pickle
import logging
import scipy.special as spc
import scipy.stats as st
import numpy as np


def string_to_filename(string):
    """ Cleans a string up to be used as a filename"""

    keepcharacters = ('_', '-')
    filename = ''.join(c for c in string if c.isalnum()
                       or c in keepcharacters).rstrip()
    filename = filename.lower()
    return filename


def print_nnl(text, file=sys.stdout):
    """Print without adding a new line """

    print(text, file=file, end='', flush=True)


def debug(time_start=None, text=None):
    """ Times execution and outputs log messages"""

    if time_start is None:
        if text is not None:
            logging.info(text)
        time_start = time.process_time()
        return time_start
    else:
        time_diff = time.process_time() - time_start
        logging.debug('Finished in {:.3f} s'.format(time_diff))
        return time_diff


def square_to_condensed(idx_i, idx_j, size_n):
    """Converts the squareform indices i and j of the condensed vector with size n to the
    condensed index k. See also: scipy.spatial.distance.squareform"""

    if idx_i == idx_j:
        raise ValueError('Diagonal entries are not defined')
    if idx_i < idx_j:
        idx_i, idx_j = idx_j, idx_i
    k = size_n * idx_j - idx_j * (idx_j + 1) / 2 + idx_i - 1 - idx_j
    return int(k)


def condensed_to_square(index_k, size_n):
    """Converts the condensed index k of the condensed vector with size n to the square indicies i
    and j. See also scipy.spatial.distance.squareform"""

    def calc_row_idx(index_k, size_n):
        """Determines the row index"""
        return int(
            np.ceil((1 / 2.) *
                    (- (-8 * index_k + 4 * size_n**2 - 4 * size_n - 7)**0.5
                     + 2 * size_n - 1) - 1))

    def elem_in_i_rows(index_i, size_n):
        """Determines the number of elements in the i-th row"""
        return index_i * (size_n - 1 - index_i) + (index_i * (index_i + 1)) / 2

    def calc_col_idx(index_k, index_i, size_n):
        """Determines the column index"""
        return int(size_n - elem_in_i_rows(index_i + 1, size_n) + index_k)

    i = calc_row_idx(index_k, size_n)
    j = calc_col_idx(index_k, i, size_n)

    return i, j


def net_connectivity_stats(net_connectivities, confidence=0.95):
    """Calculates the means and confidence intervals for network connectivity results"""

    means = np.mean(net_connectivities, axis=0)
    conf_intervals = np.zeros([np.size(means), 2])

    for index, mean in enumerate(means):
        conf_intervals[index] = st.t.interval(confidence, len(
            net_connectivities[:, index]) - 1, loc=mean, scale=st.sem(net_connectivities[:, index]))

    return means, conf_intervals


def send_mail_finish(recipient=None, time_start=None):
    """Sends an email to notify someone about the finished simulation"""

    if time_start is None:
        msg = MIMEText('The simulation is finished.')
    else:
        msg = MIMEText('The simulation started at {:.0f} is finished.'.format(
            time_start))

    msg['Subject'] = 'Simulation finished'
    msg['From'] = getpass.getuser() + '@' + socket.getfqdn()
    if recipient is None:
        msg['To'] = msg['From']
    else:
        msg['To'] = recipient

    try:
        smtp = smtplib.SMTP('localhost')
    except ConnectionRefusedError:
        logging.error('Connection to mailserver refused')
    else:
        smtp.send_message(msg)
        smtp.quit()


def save(obj, file_path, protocol=4, compression_level=1):
    """Saves an object using gzip compression"""

    with gzip.open(file_path, 'wb', compresslevel=compression_level) as file:
        pickle.dump(obj, file, protocol=protocol)


def load(file_path):
    """Loads and decompresses a saved object"""

    with gzip.open(file_path, 'rb') as file:
        return pickle.load(file)


def compress_file(file_in_path, protocol=4, compression_level=1, delete_uncompressed=True):
    """Loads an uncompressed file and saves a compressed copy of it"""

    file_out_path = file_in_path + '.gz'
    with open(file_in_path, 'rb') as file_in:
        obj = pickle.load(file_in)
        save(obj, file_out_path, protocol=protocol,
             compression_level=compression_level)

    if delete_uncompressed:
        os.remove(file_in_path)


def fill_config(config):
    """ Set unset SUMO settings to sane defaults"""

    if config['distribution_veh'] == 'SUMO':
        if 'tls_settings' not in config['sumo']:
            config['sumo']['tls_settings'] = None
        if 'fringe_factor' not in config['sumo']:
            config['sumo']['fringe_factor'] = None
        if 'max_speed' not in config['sumo']:
            config['sumo']['max_speed'] = None
        if 'intermediate_points' not in config['sumo']:
            config['sumo']['intermediate_points'] = None
        if 'warmup_duration' not in config['sumo']:
            config['sumo']['warmup_duration'] = None
        if 'abort_after_sumo' not in config['sumo']:
            config['sumo']['abort_after_sumo'] = False

    return config


def convert_config_densities(config_densities):
    """Converts the density parameters from the configuration to a simple array"""

    if isinstance(config_densities, (list, tuple)):
        densities = np.zeros(0)
        for density_in in config_densities:
            if isinstance(density_in, dict):
                density = np.linspace(**density_in)
            else:
                density = density_in
            densities = np.append(densities, density)

    else:
        densities = config_densities

    return densities
