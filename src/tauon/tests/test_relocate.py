from __future__ import annotations

from typing import TYPE_CHECKING

from tauon.t_modules.t_relocate import LibTrack, build_plan, infer_mapping, remainder, widen

if TYPE_CHECKING:
	from pathlib import Path


def ident(s: str) -> str:
	return s


def make(root: Path, rel: str, size: int = 10) -> str:
	p = root / rel
	p.parent.mkdir(parents=True, exist_ok=True)
	p.write_bytes(b"x" * size)
	return str(p)


LAYOUT = {
	"Boards of Canada/Geogaddi/03 Music Is Math.flac": 11,
	"Boards of Canada/Geogaddi/04 Beware the Friendly Stranger.flac": 12,
	"Aphex Twin/SAW 85-92/01 Xtal.flac": 13,
	"Bonobo/Black Sands/01 Prelude.flac": 14,
}


def library(old_root: str) -> list[LibTrack]:
	return [LibTrack(i, f"{old_root}/{rel}", size, None) for i, (rel, size) in enumerate(LAYOUT.items())]


def populate(new_root: Path) -> None:
	for rel, size in LAYOUT.items():
		make(new_root, rel, size)


def test_album_drop_relocates_whole_library_across_renamed_root(tmp_path: Path) -> None:
	old = str(tmp_path / "A" / "Music")
	new = tmp_path / "B" / "Tunes"
	populate(new)
	tracks = library(old)

	plan = build_plan(tracks, tracks[0].path, str(new / "Boards of Canada" / "Geogaddi"), fold=ident)

	assert plan.mapping.old_root == old
	assert plan.mapping.new_root == str(new)
	assert plan.mapping.base_old == f"{old}/Boards of Canada/Geogaddi"
	assert {i: n for i, (_o, n) in plan.moves.items()} == {
		t.id: str(new / rel) for t, rel in zip(tracks, LAYOUT, strict=True)
	}
	assert plan.unresolved == 0


def test_root_drop_same_name(tmp_path: Path) -> None:
	old = str(tmp_path / "A" / "Music")
	new = tmp_path / "B" / "Music"
	populate(new)
	tracks = library(old)

	plan = build_plan(tracks, tracks[2].path, str(new), fold=ident)

	assert plan.mapping.base_old == old
	assert plan.mapping.base_new == str(new)
	assert len(plan.moves) == len(LAYOUT)


def test_root_drop_renamed(tmp_path: Path) -> None:
	old = str(tmp_path / "A" / "Music")
	new = tmp_path / "B" / "Tunes"
	populate(new)
	tracks = library(old)

	plan = build_plan(tracks, tracks[1].path, str(new), fold=ident)

	assert (plan.mapping.old_root, plan.mapping.new_root) == (old, str(new))
	assert len(plan.moves) == len(LAYOUT)


def test_file_drop(tmp_path: Path) -> None:
	old = str(tmp_path / "A" / "Music")
	new = tmp_path / "B" / "Tunes"
	populate(new)
	tracks = library(old)

	plan = build_plan(tracks, tracks[3].path, str(new / "Bonobo/Black Sands/01 Prelude.flac"), fold=ident)

	assert plan.mapping.new_root == str(new)
	assert len(plan.moves) == len(LAYOUT)


def test_file_drop_with_different_name_gives_no_mapping(tmp_path: Path) -> None:
	other = make(tmp_path / "B", "elsewhere/other.flac")
	tracks = library(str(tmp_path / "A" / "Music"))

	assert infer_mapping(tracks[0].path, other, ident) is None


def test_tracks_still_present_are_left_alone(tmp_path: Path) -> None:
	old_root = tmp_path / "A" / "Music"
	new = tmp_path / "B" / "Tunes"
	populate(new)
	still_there = make(old_root, "Aphex Twin/SAW 85-92/01 Xtal.flac", 13)
	tracks = library(str(old_root))

	plan = build_plan(tracks, tracks[0].path, str(new), fold=ident)

	assert 2 not in plan.moves
	assert tracks[2].path == still_there
	assert len(plan.moves) == len(LAYOUT) - 1


def test_tracks_outside_old_root_are_not_touched(tmp_path: Path) -> None:
	old = str(tmp_path / "A" / "Music")
	new = tmp_path / "B" / "Tunes"
	populate(new)
	outsider = LibTrack(99, str(tmp_path / "C" / "Podcasts" / "ep1.mp3"), 5, None)
	make(new, "../Podcasts/ep1.mp3", 5)  # Coincidental match outside the rule
	tracks = [*library(old), outsider]

	plan = build_plan(tracks, tracks[0].path, str(new), fold=ident)

	assert 99 not in plan.moves


def test_restructured_folders_found_by_name_and_size(tmp_path: Path) -> None:
	old = str(tmp_path / "A" / "Music")
	new = tmp_path / "B" / "Tunes"
	populate(new)
	# Flattened Artist/Album into "Artist - Album" for one album
	(new / "Aphex Twin" / "SAW 85-92" / "01 Xtal.flac").unlink()
	make(new, "Aphex Twin - SAW 85-92/01 Xtal.flac", 13)
	tracks = library(old)

	plan = build_plan(tracks, tracks[0].path, str(new), fold=ident)

	assert plan.moves[2][1] == str(new / "Aphex Twin - SAW 85-92" / "01 Xtal.flac")
	assert plan.unresolved == 0


def test_name_collisions_resolved_by_size_then_parent(tmp_path: Path) -> None:
	new = tmp_path / "B" / "Tunes"
	make(new, "X/Album One/01 Intro.flac", 20)
	make(new, "X/Album Two/01 Intro.flac", 30)
	make(new, "Y/Album Three/01 Intro.flac", 40)
	make(new, "Y/Copy/Album Three/01 Intro.flac", 40)
	old = str(tmp_path / "A" / "Old")
	tracks = [
		LibTrack(1, f"{old}/old1/01 Intro.flac", 30, None),          # Unique size
		LibTrack(2, f"{old}/Album Three/01 Intro.flac", 40, None),   # Same size twice, both same parent name
		LibTrack(3, f"{old}/Album One/01 Intro.flac", 0, None),      # No size, parent name decides
	]

	plan = build_plan(tracks, tracks[0].path, str(new), fold=ident)

	assert plan.mapping is None
	assert plan.moves[1][1] == str(new / "X/Album Two/01 Intro.flac")
	assert 2 not in plan.moves
	assert plan.moves[3][1] == str(new / "X/Album One/01 Intro.flac")
	assert plan.unresolved == 1


def test_unrelated_drop_falls_back_to_scanning_whole_library(tmp_path: Path) -> None:
	old = str(tmp_path / "A" / "Music")
	new = tmp_path / "B" / "Reorganised"
	make(new, "Electronic/03 Music Is Math.flac", 11)
	tracks = library(old)

	plan = build_plan(tracks, tracks[0].path, str(new), fold=ident)

	assert plan.mapping is None
	assert plan.moves == {0: (tracks[0].path, str(new / "Electronic/03 Music Is Math.flac"))}
	assert plan.unresolved == len(LAYOUT) - 1


def test_already_reimported_copies_are_reported_as_duplicates(tmp_path: Path) -> None:
	old = str(tmp_path / "A" / "Music")
	new = tmp_path / "B" / "Tunes"
	populate(new)
	tracks = library(old)
	reimported = LibTrack(50, str(new / "Bonobo/Black Sands/01 Prelude.flac"), 14, None)

	plan = build_plan([*tracks, reimported], tracks[0].path, str(new), fold=ident)

	assert plan.duplicates == {50: 3}
	assert 50 not in plan.moves


def test_cue_tracks_sharing_a_file_move_together(tmp_path: Path) -> None:
	new = tmp_path / "B"
	make(new, "Live/whole.flac", 99)
	old = str(tmp_path / "A")
	tracks = [LibTrack(1, f"{old}/Live/whole.flac", 99, 0.0), LibTrack(2, f"{old}/Live/whole.flac", 99, 300.0)]
	dup = LibTrack(3, str(new / "Live/whole.flac"), 99, 300.0)

	plan = build_plan([*tracks, dup], tracks[0].path, str(new), fold=ident)

	assert plan.moves[1][1] == plan.moves[2][1] == str(new / "Live/whole.flac")
	assert plan.duplicates == {3: 2}


def test_case_insensitive_names(tmp_path: Path) -> None:
	new = tmp_path / "B" / "Tunes"
	make(new, "Artist/Album/01 TRACK.FLAC", 5)
	tracks = [LibTrack(1, str(tmp_path / "A/Music/Artist/Album/01 track.flac"), 5, None)]

	plan = build_plan(tracks, tracks[0].path, str(new / "Artist" / "Album"), fold=str.casefold)

	assert plan.moves[1][1] == str(new / "Artist/Album/01 TRACK.FLAC")


def test_missing_target(tmp_path: Path) -> None:
	plan = build_plan(library(str(tmp_path / "A")), "/x/y.flac", str(tmp_path / "nope"), fold=ident)
	assert plan.error == "not_found"
	assert not plan.moves


def test_filesystem_root_is_not_searched() -> None:
	plan = build_plan(library("/nonexistent/A"), "/nonexistent/A/x.flac", "/", fold=ident)
	assert plan.mapping is None
	assert not plan.moves
	assert not plan.error


def test_cancel(tmp_path: Path) -> None:
	populate(tmp_path / "B")
	tracks = library(str(tmp_path / "A"))
	assert build_plan(tracks, tracks[0].path, str(tmp_path / "B"), fold=ident, cancelled=lambda: True) is None


def test_widen_and_remainder() -> None:
	assert widen("/a/Music/Art/Alb", "/b/Tunes/Art/Alb", ident) == ("/a/Music", "/b/Tunes")
	assert widen("/a/Music", "/b/Music", ident) == ("/a", "/b")
	assert widen("D:/Music", "E:/Music", ident) == ("D:", "E:")
	assert remainder("/a/Music/x/y", "/a/Music", ident) == "x/y"
	assert remainder("/a/Music", "/a/Music", ident) == ""
	assert remainder("/a/Musicals/x", "/a/Music", ident) is None
	assert remainder("/A/music/x", "/a/Music", str.casefold) == "x"
