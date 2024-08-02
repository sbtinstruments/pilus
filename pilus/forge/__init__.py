# Make sure that the basics have registered all their registration funcs in
# the global forge.
from . import _on_demand
from ._forge import Forge
from ._forge_io import ForgeIO
from ._global_forge import FORGE
from ._morph import Morpher, Shape
