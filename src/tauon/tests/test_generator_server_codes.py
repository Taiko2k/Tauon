# Copyright © 2026, Tauon contributors

from __future__ import annotations

import builtins

import pytest

from tauon.t_modules import t_generator as gen

builtins.__dict__.setdefault("_", lambda text: text)

SERVER_CODES = (
	"jellyfav", "jellyfavalb", 'jellylib"id"', "airfav", "airfavalb", 'airlib"id"',
	'plexlib"1"', 'plexpl"1"', 'tau"id"',
)


@pytest.mark.parametrize("code", SERVER_CODES)
def test_server_code_is_a_known_take_step(code: str) -> None:
	step = gen.parse_step(code)
	assert step.known
	assert gen.lane_of(step) == gen.TAKE
	assert gen.problem([step]) == ""
	assert step.rebuilt() == code


@pytest.mark.parametrize("code", SERVER_CODES)
def test_adding_a_step_keeps_all_tracks_out(code: str) -> None:
	steps = [gen.parse_step(code)]
	lanes = gen.split_lanes(steps)
	tokens = {lane: [code for _i in indices] for lane, indices in lanes.items()}
	tokens[gen.THEN].append("l")
	assert gen.arrange(tokens, []) == [code, "l"]


def test_similar_codes_stay_apart() -> None:
	assert gen.parse_step("jelly").kind.id == "jelly"
	assert gen.parse_step('jelly"id"').kind.id == "jelly_pl"
	assert gen.parse_step('jellylib"id"').kind.id == "jelly_lib"
	assert gen.parse_step("tau").kind.id == "tau"
	assert gen.parse_step('tau"id"').kind.id == "tau_pl"
	assert gen.parse_step("jellyfavalb").kind.id == "jelly_favalb"
