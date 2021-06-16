import os
import re
from subprocess import Popen, PIPE
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from spat.scripts.splitter import split_iqs_file
import click

@dataclass
class ProcessConfig:
    """A configuration for the entire processing pipeline"""
    labqt_path: Path
    labqt_config: Path
    site: Optional[int] = None
    dest_dir: Optional[str] = None
    make_nested_dirs: bool = True
    delete_site_iqs: bool = False

def process_iqs_file(filename, config : ProcessConfig):
    # Sites to extract and process
    sites = [config.site]
    if config.site is None:
      sites = [0, 1]
    # If no destination directory is given, use the path of 'filename' 
    dest_root = config.dest_dir
    if dest_root is None:
        dest_root = os.path.dirname(os.path.realpath(filename))
    # Prepare destination_dirs
    site_dirs = []
    for s in sites:
        if config.make_nested_dirs:
            dir_path = dest_root + '/site' + str(s)
            site_dirs.append(dir_path)
            try:
                os.mkdir(dir_path)
            except FileExistsError as exc:
                pass
        else:
            site_dirs.append(dest_root)
    # Split IQS file if it is not split already (TODO)
    split_iqs_file(sites, filename, site_dirs)
    # Process each site in turn
    for s, d in zip(sites, site_dirs):
        site_path = os.path.join(d, 'site' + str(s) + '.iqs')
        print('Processing ' + site_path)
        process = Popen([config.labqt_path, '-i', site_path, '--export-transitions-csv', '--config', config.labqt_config], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
    # Clean-up
    if config.delete_site_iqs == True:
        for d in site_dirs:
            iqs_files = [f for f in os.listdir(d) if f.endswith('.iqs')]
            for f in iqs_files:
                os.remove(os.path.join(d, f))

def process_iqs_dir(root_dir: Path, config: ProcessConfig):
    """Processes an entire directory"""
    for root, dirs, files in os.walk(root_dir, topdown=False):
        for file in files:
            # Only process iqs-files
            if file.endswith(".iqs"):
                # Don't process files with 'site' in their name, to avoid any already split iqs-files
                if re.match(r'.*site.*', os.path.basename(file)) is None:
                    if config.make_nested_dirs == True:
                        file_path = os.path.join(root, file)
                        new_dir_path = os.path.join(root_dir, "processed_lower_min", file.strip('.iqs'))
                        # Make containing folder
                        try:
                            print('Making ' + new_dir_path)
                            os.makedirs(new_dir_path)
                        except FileExistsError as exc:
                            print(new_dir_path + ' already created')
                        config.dest_dir = new_dir_path
                    process_iqs_file(file_path, config)

if __name__ == "__main__":
    labqt_path = '/home/jonatan/dev/labqt/debug/SBT LabQt'
    conf_path = os.path.dirname(os.path.realpath(__file__)) + '/labqt_config.json'
    config = ProcessConfig(labqt_path, conf_path)
    config.delete_site_iqs = False
    file_path = os.path.dirname(os.path.realpath(__file__)) + "/2um_100e5-20210203-102759-A94.iqs"
    #root_dir = "/media/jonatan/20BCC727BCC6F5F6/FromUbuntu/pump_speeds/2021-06-04 Pump speed listeria coli 1;10 PBS"
    root_dir = "/media/jonatan/20BCC727BCC6F5F6/FromUbuntu/pump_speeds/2021-06-03 Underestimation investigation with beads"
    # process_iqs_file(file_path, config)
    process_iqs_dir(root_dir, config)
