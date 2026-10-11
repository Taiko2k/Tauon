// Speaker-labelled PCM shared by the decoders and output backends.
#ifndef PHAZOR_PCM_H
#define PHAZOR_PCM_H

#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#define PCM_MAX_CHANNELS 8
// Nine positions cover standard surround layouts, including 6.1's rear centre.
enum pcm_speaker { PCM_FL, PCM_FR, PCM_FC, PCM_LFE, PCM_RL, PCM_RR, PCM_SL, PCM_SR, PCM_RC,
	PCM_SPEAKERS, PCM_MONO, PCM_UNKNOWN };
#define PCM_STEREO_MASK ((1u << PCM_FL) | (1u << PCM_FR))

static const int pcm_flac_layout[PCM_MAX_CHANNELS + 1][PCM_MAX_CHANNELS] = {
	{0}, {PCM_MONO}, {PCM_FL, PCM_FR}, {PCM_FL, PCM_FR, PCM_FC},
	{PCM_FL, PCM_FR, PCM_RL, PCM_RR}, {PCM_FL, PCM_FR, PCM_FC, PCM_RL, PCM_RR},
	{PCM_FL, PCM_FR, PCM_FC, PCM_LFE, PCM_RL, PCM_RR},
	{PCM_FL, PCM_FR, PCM_FC, PCM_LFE, PCM_RC, PCM_SL, PCM_SR},
	{PCM_FL, PCM_FR, PCM_FC, PCM_LFE, PCM_RL, PCM_RR, PCM_SL, PCM_SR},
};

// Vorbis order is also used by Opus channel mapping family 1.
static const int pcm_vorbis_layout[PCM_MAX_CHANNELS + 1][PCM_MAX_CHANNELS] = {
	{0}, {PCM_MONO}, {PCM_FL, PCM_FR}, {PCM_FL, PCM_FC, PCM_FR},
	{PCM_FL, PCM_FR, PCM_RL, PCM_RR}, {PCM_FL, PCM_FC, PCM_FR, PCM_RL, PCM_RR},
	{PCM_FL, PCM_FC, PCM_FR, PCM_RL, PCM_RR, PCM_LFE},
	{PCM_FL, PCM_FC, PCM_FR, PCM_SL, PCM_SR, PCM_RC, PCM_LFE},
	{PCM_FL, PCM_FC, PCM_FR, PCM_SL, PCM_SR, PCM_RL, PCM_RR, PCM_LFE},
};

static uint16_t pcm_layout_mask(int channels) {
	if (channels < 1 || channels > PCM_MAX_CHANNELS) return 0;
	if (channels == 1) return PCM_STEREO_MASK;
	uint16_t mask = 0;
	for (int c = 0; c < channels; c++) mask |= 1u << pcm_flac_layout[channels][c];
	return mask;
}

static bool pcm_valid_layout(int channels, const int *map) {
	if (channels < 1 || channels > PCM_MAX_CHANNELS) return false;
	unsigned int seen = 0;
	for (int c = 0; c < channels; c++) {
		if (map[c] == PCM_MONO) return channels == 1;
		if (map[c] < 0 || map[c] >= PCM_SPEAKERS || (seen & (1u << map[c]))) return false;
		seen |= 1u << map[c];
	}
	return true;
}

typedef struct {
	int channels;
	int map[PCM_MAX_CHANNELS];
	int source_mask;
	float weights[PCM_MAX_CHANNELS][PCM_SPEAKERS];
} pcm_mixer;

static void pcm_mixer_set_layout(pcm_mixer *mixer, int channels, const int *map) {
	if (!pcm_valid_layout(channels, map)) {
		channels = 2;
		map = pcm_flac_layout[2];
	}
	mixer->channels = channels;
	memcpy(mixer->map, map, channels * sizeof(*map));
	mixer->source_mask = -1;
}

static int pcm_find_speaker(const pcm_mixer *mixer, int speaker) {
	for (int c = 0; c < mixer->channels; c++) if (mixer->map[c] == speaker) return c;
	return -1;
}

static int pcm_surround_partner(int speaker) {
	if (speaker == PCM_RL) return PCM_SL;
	if (speaker == PCM_RR) return PCM_SR;
	if (speaker == PCM_SL) return PCM_RL;
	if (speaker == PCM_SR) return PCM_RR;
	return PCM_UNKNOWN;
}

// True when a back/side pair is both present and folded onto one speaker.
static bool pcm_pair_shared(const pcm_mixer *mixer, uint16_t mask, int speaker) {
	int partner = pcm_surround_partner(speaker);
	if (partner == PCM_UNKNOWN || !(mask & (1u << partner))) return false;
	return (pcm_find_speaker(mixer, speaker) >= 0) != (pcm_find_speaker(mixer, partner) >= 0);
}

static void pcm_mixer_build(pcm_mixer *mixer, uint16_t mask) {
	memset(mixer->weights, 0, sizeof(mixer->weights));
	int left = pcm_find_speaker(mixer, PCM_FL);
	int right = pcm_find_speaker(mixer, PCM_FR);
	for (int s = 0; s < PCM_SPEAKERS; s++) {
		if (!(mask & (1u << s))) continue;
		int dest = pcm_find_speaker(mixer, s);
		if (dest >= 0) {
			// A shared pair is power summed so it does not force the whole
			// mix down by 6 dB to make headroom.
			mixer->weights[dest][s] = pcm_pair_shared(mixer, mask, s) ? 0.70710678f : 1.0f;
			continue;
		}
		// LFE is retained only when the device has an LFE speaker. Bass
		// management belongs to the system/receiver, not this PCM remixer.
		if (s == PCM_LFE) continue;
		if (mixer->channels == 1 && mixer->map[0] == PCM_MONO) {
			mixer->weights[0][s] = (s == PCM_FL || s == PCM_FR) ? 0.5f : 0.70710678f;
			continue;
		}
		dest = pcm_find_speaker(mixer, pcm_surround_partner(s));
		if (dest >= 0) {
			mixer->weights[dest][s] = pcm_pair_shared(mixer, mask, s) ? 0.70710678f : 1.0f;
		} else if (s == PCM_RL || s == PCM_SL) {
			if (left >= 0) mixer->weights[left][s] = 0.70710678f;
		} else if (s == PCM_RR || s == PCM_SR) {
			if (right >= 0) mixer->weights[right][s] = 0.70710678f;
		} else if (s == PCM_RC) {
			int rear_l = pcm_find_speaker(mixer, PCM_RL);
			int rear_r = pcm_find_speaker(mixer, PCM_RR);
			if (rear_l < 0) rear_l = pcm_find_speaker(mixer, PCM_SL);
			if (rear_r < 0) rear_r = pcm_find_speaker(mixer, PCM_SR);
			if (rear_l < 0) rear_l = left;
			if (rear_r < 0) rear_r = right;
			if (rear_l >= 0) mixer->weights[rear_l][s] = 0.70710678f;
			if (rear_r >= 0) mixer->weights[rear_r][s] = 0.70710678f;
		} else {
			if (left >= 0) mixer->weights[left][s] = 0.70710678f;
			if (right >= 0) mixer->weights[right][s] = 0.70710678f;
		}
	}
	// One shared gain preserves balance and reserves headroom for a downmix.
	float max_sum = 1.0f;
	for (int c = 0; c < mixer->channels; c++) {
		float sum = 0.0f;
		for (int s = 0; s < PCM_SPEAKERS; s++) sum += mixer->weights[c][s];
		if (sum > max_sum) max_sum = sum;
	}
	for (int c = 0; c < mixer->channels; c++)
		for (int s = 0; s < PCM_SPEAKERS; s++) mixer->weights[c][s] /= max_sum;
	mixer->source_mask = mask;
}

static void pcm_mixer_process(pcm_mixer *mixer, const float *in, uint16_t mask, float *out) {
	if (mixer->source_mask != mask) pcm_mixer_build(mixer, mask);
	for (int c = 0; c < mixer->channels; c++) {
		out[c] = 0.0f;
		for (int s = 0; s < PCM_SPEAKERS; s++) out[c] += in[s] * mixer->weights[c][s];
	}
}

#endif
