import pytest

from vm_stand_reaper.domain.model import VirtualMachineLabels


@pytest.mark.parametrize(
    "labels",
    [("stand-01", "pe_team", "bender"), ("stand-01", "pe_team", "bender", "2h")],
)
def test_all_required_labels_have_values(labels):
    assert VirtualMachineLabels(*labels).has_required_labels()


@pytest.mark.parametrize(
    "labels",
    [
        (None, "pe_team", "bender"),
        ("stand-01", None, "bender"),
        ("stand-01", "pe_team", None),
    ],
)
def test_not_all_required_labels_have_values(labels):
    assert VirtualMachineLabels(*labels).has_required_labels() is False
