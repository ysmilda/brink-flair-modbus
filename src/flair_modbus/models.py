"""Brink Flair models and their airflow limits."""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class FlairModel:
    """A Flair model, with the airflow range its installer menu allows."""

    name: str
    min_flow: int
    """Lowest airflow for levels 1 to 3, in m3/h. Level 0 may also be 0."""
    max_flow: int
    """Highest airflow, in m3/h."""


# Flair 300, 325, 400, 450 and 600 come from their installation manuals, and
# 350 from its Modbus documentation. The others are the nominal capacity in
# the model name and still need checking.
FLAIR_200 = FlairModel(name="Flair 200", min_flow=50, max_flow=200)
FLAIR_225 = FlairModel(name="Flair 225", min_flow=50, max_flow=225)
FLAIR_300 = FlairModel(name="Flair 300", min_flow=50, max_flow=300)
FLAIR_325 = FlairModel(name="Flair 325", min_flow=50, max_flow=325)
FLAIR_350 = FlairModel(name="Flair 350", min_flow=50, max_flow=350)
FLAIR_400 = FlairModel(name="Flair 400", min_flow=50, max_flow=400)
FLAIR_450 = FlairModel(name="Flair 450", min_flow=75, max_flow=450)
FLAIR_600 = FlairModel(name="Flair 600", min_flow=100, max_flow=600)

# Used when the appliance type is not (yet) in APPLIANCE_TYPES. The unit
# itself rejects a flow outside its own range.
UNKNOWN_MODEL = FlairModel(name="Flair", min_flow=50, max_flow=600)

# Register 4004 holds an internal appliance type number that Brink does not
# document. Entries are added here as they are confirmed on real units.
APPLIANCE_TYPES: dict[int, FlairModel] = {
    24: FLAIR_300,
}


def model_for_appliance_type(appliance_type: int) -> FlairModel | None:
    """Return the model behind an appliance type, or None if it is unknown."""
    return APPLIANCE_TYPES.get(appliance_type)
