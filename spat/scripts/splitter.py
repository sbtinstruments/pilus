from spat import seed
from spat.seed.formats import open_iqs, write_iqs_v1, to_IQSv1
import os
from copy import deepcopy
import click


dir_path = os.path.dirname(os.path.realpath(__file__))

def add_site_to_path(path: str, site: int):
  return click.format_filename(path).strip('.iqs')+'-site'+str(site)+'.iqs'

def split_iqs_file(site, src : str):
  if src.endswith(".iqs"):
    print(f'Opening .iqs file...')
    incoming = open_iqs(src)
    # sites: 0, 1, or both
    sites = [site]
    if site is None:
      print(f'Extracting all sites')
      sites = [0, 1]
    for i in sites:
      print(f'Extracting site {i}...')
      outgoing = to_IQSv1(incoming, i)
      write_iqs_v1(outgoing, add_site_to_path(src, i))
  else:
    print("Please supply a file with the .iqs extension!")

@click.command()
@click.argument('filename', type=click.Path(exists=True, resolve_path=True))
@click.option('--site', type=int)
def split_file(filename, site):
  if site not in (None, 0, 1):
    print("Site must be 0 or 1, if provided.")
    return
  split_iqs_file(site, filename)


# def split_iqs_files(src_dir, dest_dir=None):
#   if dest_dir is None:
#     dest_dir = src_dir
#   for file in os.listdir(src_dir):
#     if file.endswith(".iqs"):
#       split_iqs_file(os.path.join(src_dir, file), dest_dir)    



if __name__ == "__main__":
  split_file()
