#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A hearing group read off its guidance is a group its lookups take, for mypy too.

The lookups of the marine-mammal weighting take a hearing group typed as the
thirteen codes the three guidance versions use, so a misspelt code is caught
before it runs. The codes a guidance lists, and the group a criteria record
holds, were typed ``str``, so looping over :func:`hearing_groups` into
:func:`weighting_parameters`, or reading a record's group back into
:func:`exposure_criteria`, was a type error although every value is right. The
suite checks the values at run time; this file holds the typing, because CI
type checks every file in this directory alongside ``src`` and ``scripts``.
"""

from __future__ import annotations

from phonometry import underwater


def test_every_group_of_a_guidance_is_a_group_its_lookups_take() -> None:
    for group in underwater.hearing_groups("southall-2019"):
        parameters = underwater.weighting_parameters(group, guidance="southall-2019")
        criteria = underwater.exposure_criteria(group, guidance="southall-2019")
        assert parameters.group == group
        assert criteria.group == group


def test_a_record_hands_its_group_back_to_the_lookup() -> None:
    criteria = underwater.exposure_criteria("PCW", guidance="southall-2019")
    again = underwater.exposure_criteria(criteria.group, guidance=criteria.guidance)
    assert again == criteria
