# Make sure that the basics have registered all their registration funcs in
# the global forge.
from . import _on_demand as _on_demand
from ._forge import Forge as Forge
from ._forge_io import ForgeIO as ForgeIO
from ._global_forge import FORGE as FORGE
from ._morph import Morpher as Morpher
from ._morph import Shape as Shape
