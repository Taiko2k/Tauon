"""Track, folder, and playlist-generator template helpers."""

from __future__ import annotations

import os

from tauon.t_modules.t_extra import filename_safe
from tauon.t_modules.t_models import TrackClass


def encode_track_name(track_object: TrackClass) -> str:
	if track_object.is_cue or not track_object.filename:
		out_line = str(track_object.track_number) + ". "
		out_line += track_object.artist + " - " + track_object.title
		return filename_safe(out_line)
	return os.path.splitext(track_object.filename)[0]


def encode_folder_name(track_object: TrackClass) -> str:
	folder_name = track_object.artist + " - " + track_object.album

	if folder_name == " - ":
		folder_name = track_object.parent_folder_name

	folder_name = filename_safe(folder_name).strip()

	if not folder_name:
		folder_name = str(track_object.index)

	if "cd" not in folder_name.lower() or "disc" not in folder_name.lower():
		if track_object.disc_total not in ("", "0", 0, "1", 1) or (
				str(track_object.disc_number).isdigit() and int(track_object.disc_number) > 1):
			folder_name += " CD" + str(track_object.disc_number)

	return folder_name


def unique_template(string: str) -> bool:
	return "<t>" in string or \
		"<title>" in string or \
		"<n>" in string or \
		"<number>" in string or \
		"<tracknumber>" in string or \
		"<tn>" in string or \
		"<sn>" in string or \
		"<singlenumber>" in string or \
		"<s>" in string or "%t" in string or "%tn" in string


def re_template_word(word: str, tr: TrackClass) -> str:
	if word == "aa" or word == "albumartist":

		if tr.album_artist:
			return tr.album_artist
		return tr.artist

	if word == "a" or word == "artist":
		return tr.artist

	if word == "t" or word == "title":
		return tr.title

	if word == "n" or word == "number" or word == "tracknumber" or word == "tn":
		if len(str(tr.track_number)) < 2:
			return "0" + str(tr.track_number)
		return str(tr.track_number)

	if word == "sn" or word == "singlenumber" or word == "singletracknumber" or word == "s":
		return str(tr.track_number)

	if word == "d" or word == "date" or word == "year":
		return str(tr.date)

	if word == "b" or "album" in word:
		return str(tr.album)

	if word == "g" or word == "genre":
		return tr.genre

	if word == "x" or "ext" in word or "file" in word:
		return tr.file_ext.lower()

	if word == "ux" or "upper" in word:
		return tr.file_ext.upper()

	if word == "c" or "composer" in word:
		return tr.composer

	if "comment" in word:
		return tr.comment.replace("\n", "").replace("\r", "")
	return ""


def parse_template2(string: str, track_object: TrackClass, strict: bool = False) -> str:
	temp = ""
	out = ""

	mode = 0

	for c in string:
		if mode == 0:
			if c == "<":
				mode = 1
			else:
				out += c

		elif c == ">":
			test = re_template_word(temp, track_object)
			if strict:
				assert test
			out += test

			mode = 0
			temp = ""

		else:
			temp += c

	if "<und" in string:
		out = out.replace(" ", "_")
	return parse_template(out, track_object, strict=strict)


def parse_template(string: str, track_object: TrackClass, up_ext: bool = False, strict: bool = False) -> str:
	set = 0
	underscore = False
	output = ""

	while set < len(string):
		if string[set] == "%" and set < len(string) - 1:
			set += 1
			if string[set] == "n":
				if len(str(track_object.track_number)) < 2:
					output += "0"
				if strict:
					assert str(track_object.track_number)
				output += str(track_object.track_number)
			elif string[set] == "a":
				if up_ext and track_object.album_artist:
					output += track_object.album_artist
				else:
					if strict:
						assert track_object.artist
					output += track_object.artist
			elif string[set] == "t":
				if strict:
					assert track_object.title
				output += track_object.title
			elif string[set] == "c":
				if strict:
					assert track_object.composer
				output += track_object.composer
			elif string[set] == "d":
				if strict:
					assert track_object.date
				output += track_object.date
			elif string[set] == "b":
				if strict:
					assert track_object.album
				output += track_object.album
			elif string[set] == "x":
				if up_ext:
					output += track_object.file_ext.upper()
				else:
					output += "." + track_object.file_ext.lower()
			elif string[set] == "u":
				underscore = True
		else:
			output += string[set]
		set += 1

	output = output.rstrip(" -").lstrip(" -")

	if underscore:
		output = output.replace(" ", "_")

	return filename_safe(output)


def parse_generator(string: str) -> tuple[list[str], list[str], bool]:
	cmds: list[str] = []
	quotes: list[str] = []
	current = ""
	q_string = ""
	inquote = False
	for cha in string:
		if not inquote and cha == " ":
			if current:
				cmds.append(current)
				quotes.append(q_string)
			q_string = ""
			current = ""
			continue
		if cha == "\"":
			inquote ^= True

		current += cha

		if inquote and cha != "\"":
			q_string += cha

	if current:
		cmds.append(current)
		quotes.append(q_string)

	return cmds, quotes, inquote


def add_pl_tag(text: str) -> str:
	return f" <{text}>"
