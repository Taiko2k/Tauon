// Phase vocoder time stretching: changes duration without changing pitch.
// Bins follow the nearest spectral peak and channels share one phase rotation,
// which keeps notes clean and the stereo image stable. Frames are split at
// attacks, which then play unstretched, so drums stay sharp and in time.
#ifndef PHAZOR_TEMPO_H
#define PHAZOR_TEMPO_H

#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "kissfft/kiss_fftr.h"
#include "pcm.h"

#define TEMPO_CAPACITY (1 << 17)
#define TEMPO_WRAP (TEMPO_CAPACITY - 1)
#define TEMPO_MAX_FFT 32768
#define TEMPO_FFT_SIZES 5
#define TEMPO_BINS (TEMPO_MAX_FFT / 2 + 1)
#define TEMPO_OUT_SIZE (TEMPO_MAX_FFT * 2)
#define TEMPO_OUT_WRAP (TEMPO_OUT_SIZE - 1)
#define TEMPO_MAX_ONSETS 64
#define TEMPO_PI 3.14159265358979f

#define TEMPO_FFT_MS 85
#define TEMPO_OVERLAP 4
// Attacks must rise this far in power above the recent peak. Sharp rises use
// 2.5 ms blocks. Level rises use 12.5 ms blocks, which span bass cycles. Both
// look back 75 ms.
#define TEMPO_SHARP_RATIO 4.0f
#define TEMPO_LEVEL_RATIO 3.0f
#define TEMPO_SHARP_BLOCKS 30
#define TEMPO_LEVEL_SPAN 5
#define TEMPO_LEVEL_BLOCKS 6
// A bin restarts its phase at an attack if it grew by this much
#define TEMPO_RISE_RATIO 1.6f

typedef struct {
	float audio[PCM_SPEAKERS][TEMPO_CAPACITY];
	uint16_t mask[TEMPO_CAPACITY];
	float output[PCM_SPEAKERS][TEMPO_OUT_SIZE];
	float norm[TEMPO_OUT_SIZE];
	float window[TEMPO_MAX_FFT];
	float analysis_window[TEMPO_MAX_FFT];
	float synthesis_window[TEMPO_MAX_FFT];
	float time[TEMPO_MAX_FFT];
	kiss_fft_cpx spectrum[PCM_SPEAKERS][TEMPO_BINS];
	kiss_fft_cpx previous[PCM_SPEAKERS][TEMPO_BINS];
	float magnitude[TEMPO_BINS];
	float before_attack[TEMPO_BINS];
	float rotation[TEMPO_BINS];
	float next_rotation[TEMPO_BINS];
	kiss_fftr_cfg forward[TEMPO_FFT_SIZES];
	kiss_fftr_cfg inverse[TEMPO_FFT_SIZES];
	int fft_index;
	int size;
	int sample_rate;
	float rate;
	int64_t written;
	double ideal;
	int64_t analysis;
	int64_t previous_analysis;
	int64_t last_split;
	bool previous_shaped;
	int analysis_hop;
	int synthesis_hop;
	int64_t emit;
	int64_t ready_end;
	int64_t region_start;
	double heard_base;
	uint16_t region_mask;
	bool started;
	bool finishing;
	bool drained;
	bool active[PCM_SPEAKERS];
	// Attack detector
	float last[PCM_SPEAKERS];
	float block_energy;
	float block_level;
	float sharp_history[TEMPO_SHARP_BLOCKS];
	float level_history[TEMPO_LEVEL_BLOCKS];
	int sharp_at;
	int level_at;
	int level_fill;
	int block_fill;
	int block_size;
	int64_t last_onset;
	int64_t onsets[TEMPO_MAX_ONSETS];
	int onset_read;
	int onset_write;
} tempo_stretcher;

static bool tempo_init(tempo_stretcher *t) {
	for (int i = 0; i < TEMPO_FFT_SIZES; i++) {
		int size = 2048 << i;
		if (t->forward[i] == NULL) t->forward[i] = kiss_fftr_alloc(size, 0, NULL, NULL);
		if (t->inverse[i] == NULL) t->inverse[i] = kiss_fftr_alloc(size, 1, NULL, NULL);
		if (t->forward[i] == NULL || t->inverse[i] == NULL) return false;
	}
	return true;
}

static void tempo_reset(tempo_stretcher *t, int sample_rate) {
	if (sample_rate < 8000) sample_rate = 44100;
	if (sample_rate != t->sample_rate) {
		t->sample_rate = sample_rate;
		int wanted = (int) (sample_rate * (double) TEMPO_FFT_MS / 1000.0);
		t->fft_index = 0;
		while (t->fft_index < TEMPO_FFT_SIZES - 1 && (2048 << t->fft_index) * 1.4 < wanted) t->fft_index++;
		t->size = 2048 << t->fft_index;
		for (int i = 0; i < t->size; i++) {
			float s = sinf(TEMPO_PI * i / t->size);
			t->window[i] = s * s;
		}
		t->block_size = sample_rate / 400;
	}
	int bins = t->size / 2 + 1;
	for (int c = 0; c < PCM_SPEAKERS; c++) {
		memset(t->output[c], 0, TEMPO_OUT_SIZE * sizeof(float));
		memset(t->previous[c], 0, bins * sizeof(kiss_fft_cpx));
	}
	memset(t->norm, 0, sizeof(t->norm));
	memset(t->rotation, 0, bins * sizeof(float));
	memset(t->last, 0, sizeof(t->last));
	memset(t->active, 0, sizeof(t->active));
	t->written = 0;
	t->ideal = 0;
	t->analysis = 0;
	t->previous_analysis = 0;
	t->last_split = -1;
	t->previous_shaped = false;
	t->analysis_hop = 0;
	t->synthesis_hop = 0;
	t->emit = 0;
	t->ready_end = 0;
	t->region_start = 0;
	t->heard_base = 0;
	t->region_mask = 0;
	t->started = false;
	t->finishing = false;
	t->drained = false;
	t->block_energy = 0;
	t->block_level = 0;
	memset(t->sharp_history, 0, sizeof(t->sharp_history));
	memset(t->level_history, 0, sizeof(t->level_history));
	t->sharp_at = 0;
	t->level_at = 0;
	t->level_fill = 0;
	t->block_fill = 0;
	t->last_onset = INT64_MIN / 2;
	t->onset_read = 0;
	t->onset_write = 0;
}

static bool tempo_wants_input(const tempo_stretcher *t) {
	if (t->finishing || t->drained) return false;
	if (t->emit < t->ready_end) return false;
	return t->written < t->analysis + t->size;
}

// Moves from the detection block to just before the first sample of the rise.
static int64_t tempo_refine_attack(const tempo_stretcher *t, int64_t block) {
	int64_t first = block - t->block_size;
	if (first < 1) first = 1;
	float largest = 0;
	for (int pass = 0; pass < 2; pass++) {
		for (int64_t i = first; i < t->written; i++) {
			float rise = 0;
			for (int c = 0; c < PCM_SPEAKERS; c++) {
				rise += fabsf(t->audio[c][i & TEMPO_WRAP] - t->audio[c][(i - 1) & TEMPO_WRAP]);
			}
			if (pass == 0) largest = fmaxf(largest, rise);
			else if (rise > largest * 0.25f) return i - t->sample_rate / 4000;
		}
	}
	return block;
}

// Compares short blocks with the loudest of the recent ones. An average would
// let the swing within a bass note's cycle pass for a stream of attacks.
static void tempo_detect_attack(tempo_stretcher *t, const float *frame) {
	float rise_energy = 0;
	float level = 0;
	for (int c = 0; c < PCM_SPEAKERS; c++) {
		float rise = frame[c] - t->last[c];
		rise_energy += rise * rise;
		level += frame[c] * frame[c];
		t->last[c] = frame[c];
	}
	t->block_energy += rise_energy;
	t->block_level += level;
	if (++t->block_fill < t->block_size) return;
	float sharp_block = t->block_energy / t->block_size;
	t->block_energy = 0;
	t->block_fill = 0;

	float recent_sharp = 0;
	for (int i = 0; i < TEMPO_SHARP_BLOCKS; i++) recent_sharp = fmaxf(recent_sharp, t->sharp_history[i]);
	t->sharp_history[t->sharp_at] = sharp_block;
	t->sharp_at = (t->sharp_at + 1) % TEMPO_SHARP_BLOCKS;
	bool sharp = sharp_block > 1e-6f && sharp_block > recent_sharp * TEMPO_SHARP_RATIO;

	bool heavy = false;
	if (++t->level_fill >= TEMPO_LEVEL_SPAN) {
		float level_block = t->block_level / (t->block_size * TEMPO_LEVEL_SPAN);
		t->block_level = 0;
		t->level_fill = 0;
		float recent_level = 0;
		for (int i = 0; i < TEMPO_LEVEL_BLOCKS; i++) recent_level = fmaxf(recent_level, t->level_history[i]);
		t->level_history[t->level_at] = level_block;
		t->level_at = (t->level_at + 1) % TEMPO_LEVEL_BLOCKS;
		heavy = level_block > 1e-4f && level_block > recent_level * TEMPO_LEVEL_RATIO;
	}

	int64_t at = t->written - t->block_size;
	if (at > t->sample_rate / 10 && (sharp || heavy) && at - t->last_onset > t->sample_rate / 25) {
		at = tempo_refine_attack(t, heavy && !sharp ? t->written - t->block_size * (TEMPO_LEVEL_SPAN - 1) : at);
		int next = (t->onset_write + 1) % TEMPO_MAX_ONSETS;
		if (next != t->onset_read && at > t->last_onset) {
			t->onsets[t->onset_write] = at;
			t->onset_write = next;
		}
		t->last_onset = at;
	}
}

static void tempo_push(tempo_stretcher *t, const float *frame, uint16_t mask) {
	int at = (int) (t->written & TEMPO_WRAP);
	for (int c = 0; c < PCM_SPEAKERS; c++) t->audio[c][at] = frame[c];
	t->mask[at] = mask;
	t->written++;
	tempo_detect_attack(t, frame);
}

static void tempo_finish(tempo_stretcher *t) {
	t->finishing = true;
	if (t->written == 0) t->drained = true;
}

static float tempo_wrap_phase(float phase) {
	return phase - 2 * TEMPO_PI * floorf(phase / (2 * TEMPO_PI) + 0.5f);
}

// Peak rotations advance by the frequency each peak really has, and the bins
// around a peak follow it, which keeps a partial's shape intact.
static void tempo_update_rotation(tempo_stretcher *t, int bins, int analysis_hop, int synthesis_hop) {
	const float omega_scale = 2 * TEMPO_PI / t->size;
	float hop_gap = (float) (synthesis_hop - analysis_hop);
	int region_start = 0;
	int last_peak = -1;
	float *next = t->next_rotation;
	for (int k = 2; k < bins - 2; k++) {
		float m = t->magnitude[k];
		if (!(m > t->magnitude[k - 1] && m >= t->magnitude[k + 1]
				&& m > t->magnitude[k - 2] && m >= t->magnitude[k + 2])) continue;
		int source = 0;
		float strongest = -1;
		for (int c = 0; c < PCM_SPEAKERS; c++) {
			if (!t->active[c]) continue;
			float power = t->spectrum[c][k].r * t->spectrum[c][k].r + t->spectrum[c][k].i * t->spectrum[c][k].i;
			if (power > strongest) {
				strongest = power;
				source = c;
			}
		}
		kiss_fft_cpx now = t->spectrum[source][k];
		kiss_fft_cpx before = t->previous[source][k];
		float real = now.r * before.r + now.i * before.i;
		float imag = now.i * before.r - now.r * before.i;
		float omega = omega_scale * k;
		float delta = tempo_wrap_phase(atan2f(imag, real) - omega * analysis_hop);
		float frequency = analysis_hop > 0 ? omega + delta / analysis_hop : omega;
		float rotated = tempo_wrap_phase(t->rotation[k] + frequency * hop_gap);
		int boundary = last_peak < 0 ? 0 : (last_peak + k + 1) / 2;
		if (last_peak >= 0) {
			for (int b = region_start; b < boundary; b++) next[b] = next[last_peak];
		}
		next[k] = rotated;
		region_start = boundary;
		last_peak = k;
	}
	if (last_peak >= 0) {
		for (int b = region_start; b < bins; b++) next[b] = next[last_peak];
		memcpy(t->rotation, next, bins * sizeof(float));
	}
}

// Shapes the windows so a frame hears nothing across an attack. Times are
// absolute source positions, or -1 when that side has no attack in reach.
static bool tempo_build_windows(tempo_stretcher *t, int64_t start, int64_t before, int64_t after) {
	int size = t->size;
	int half = size / 2;
	if (before < 0 && after < 0) {
		memcpy(t->analysis_window, t->window, size * sizeof(float));
		memcpy(t->synthesis_window, t->window, size * sizeof(float));
		return false;
	}
	float fade = (float) t->sample_rate / 1000.0f;
	int64_t centre = start + half;
	float rate = t->rate;
	float in_low = before >= 0 ? (float) (before - start) : -1e9f;
	float in_high = after >= 0 ? (float) (after - start) : 1e9f;
	float out_low = before >= 0 ? half + (float) (before - centre) / rate : -1e9f;
	float out_high = after >= 0 ? half + (float) (after - centre) / rate : 1e9f;
	for (int i = 0; i < size; i++) {
		float x = (float) i;
		// Both sides fade before the attack, so none of it lands in an earlier frame.
		float in_gain = fminf(fminf((x - in_low) / fade + 1.0f, (in_high - x) / fade), 1.0f);
		float out_gain = fminf(fminf((x - out_low) / fade + 1.0f, (out_high - x) / fade), 1.0f);
		in_gain = fmaxf(in_gain, 0.0f);
		out_gain = fmaxf(out_gain, 0.0f);
		t->analysis_window[i] = t->window[i] * in_gain;
		t->synthesis_window[i] = t->window[i] * out_gain;
	}
	return true;
}

static void tempo_transform(tempo_stretcher *t, int channel, int64_t start, kiss_fft_cpx *result) {
	int size = t->size;
	int half = size / 2;
	for (int i = 0; i < size; i++) {
		int64_t position = start + i;
		float value = position >= 0 && position < t->written ? t->audio[channel][position & TEMPO_WRAP] : 0;
		// Rotated so the window's centre is phase zero
		t->time[(i + half) & (size - 1)] = value * t->analysis_window[i];
	}
	kiss_fftr(t->forward[t->fft_index], t->time, result);
}

static void tempo_render(tempo_stretcher *t, int64_t start, int64_t output_start, int64_t before, int64_t after,
		int analysis_hop, int synthesis_hop, bool reset_rises) {
	int size = t->size;
	int half = size / 2;
	int bins = half + 1;
	bool shaped = tempo_build_windows(t, start, before, after);
	if (!t->started) {
		// Nothing overlaps the first frame's start, so it plays from full level.
		for (int i = 0; i < half; i++) {
			t->analysis_window[i] = 1.0f;
			t->synthesis_window[i] = 1.0f;
		}
		shaped = true;
	}

	memset(t->magnitude, 0, bins * sizeof(float));
	for (int c = 0; c < PCM_SPEAKERS; c++) {
		float peak = 0;
		for (int i = 0; i < size; i++) {
			int64_t position = start + i;
			if (position >= 0 && position < t->written) peak = fmaxf(peak, fabsf(t->audio[c][position & TEMPO_WRAP]));
		}
		bool was_active = t->active[c];
		t->active[c] = peak > 0;
		if (!t->active[c]) continue;
		tempo_transform(t, c, start, t->spectrum[c]);
		if (!was_active) memcpy(t->previous[c], t->spectrum[c], bins * sizeof(kiss_fft_cpx));
		// A shape change biases phase, so compare against the same shape one hop back
		else if ((shaped || t->previous_shaped) && analysis_hop > 0 && synthesis_hop != analysis_hop) {
			tempo_transform(t, c, start - analysis_hop, t->previous[c]);
		}
		for (int k = 0; k < bins; k++) {
			kiss_fft_cpx x = t->spectrum[c][k];
			t->magnitude[k] += sqrtf(x.r * x.r + x.i * x.i);
		}
	}

	if (t->started && synthesis_hop != analysis_hop) tempo_update_rotation(t, bins, analysis_hop, synthesis_hop);
	if (reset_rises) {
		// Only what the attack added restarts; held notes keep their phase.
		for (int k = 0; k < bins; k++) {
			if (t->magnitude[k] > t->before_attack[k] * TEMPO_RISE_RATIO) t->rotation[k] = 0;
		}
	}

	for (int c = 0; c < PCM_SPEAKERS; c++) {
		if (!t->active[c]) continue;
		memcpy(t->previous[c], t->spectrum[c], bins * sizeof(kiss_fft_cpx));
		int k = 0;
		while (k < bins) {
			float angle = t->rotation[k];
			float co = cosf(angle), si = sinf(angle);
			for (; k < bins && t->rotation[k] == angle; k++) {
				kiss_fft_cpx x = t->spectrum[c][k];
				t->spectrum[c][k].r = x.r * co - x.i * si;
				t->spectrum[c][k].i = x.r * si + x.i * co;
			}
		}
		kiss_fftri(t->inverse[t->fft_index], t->spectrum[c], t->time);
		float scale = 1.0f / size;
		for (int i = 0; i < size; i++) {
			t->output[c][(output_start + i) & TEMPO_OUT_WRAP] += t->time[(i + half) & (size - 1)] * t->synthesis_window[i] * scale;
		}
	}
	for (int i = 0; i < size; i++) t->norm[(output_start + i) & TEMPO_OUT_WRAP] += t->analysis_window[i] * t->synthesis_window[i];
	t->previous_shaped = shaped;
	t->started = true;
}

static void tempo_process_frame(tempo_stretcher *t) {
	int size = t->size;
	int half = size / 2;
	int64_t start = t->analysis;
	int64_t output_start = t->ready_end;

	// The next attack at or before this frame's centre pulls the frame onto it.
	int64_t split = -1;
	int64_t after = -1;
	while (t->onset_read != t->onset_write && t->onsets[t->onset_read] <= t->last_split) {
		t->onset_read = (t->onset_read + 1) % TEMPO_MAX_ONSETS;
	}
	if (t->started) {
		for (int i = t->onset_read; i != t->onset_write; i = (i + 1) % TEMPO_MAX_ONSETS) {
			int64_t onset = t->onsets[i];
			if (onset <= start + half) {
				if (split < 0) split = onset;
			} else {
				if (onset < start + size) after = onset;
				break;
			}
		}
	}
	if (split >= 0) {
		start = split - half;
		if (start < t->previous_analysis) start = t->previous_analysis;
		split = start + half;
	}
	int analysis_hop = (int) (start - t->previous_analysis);
	int synthesis_hop = t->synthesis_hop;
	int64_t before = t->last_split > start ? t->last_split : -1;

	if (split >= 0) {
		tempo_render(t, start, output_start, before, split, analysis_hop, synthesis_hop, false);
		memcpy(t->before_attack, t->magnitude, (half + 1) * sizeof(float));
		t->last_split = split;
		tempo_render(t, start, output_start, split, after, 0, 0, true);
		t->onset_read = (t->onset_read + 1) % TEMPO_MAX_ONSETS;
	} else {
		tempo_render(t, start, output_start, before, after, analysis_hop, synthesis_hop, false);
	}

	int hop = t->rate >= 1.0f ? (int) lround(size / (double) TEMPO_OVERLAP / t->rate) : size / TEMPO_OVERLAP;
	// Land the next attack exactly where the time map puts it, not on the hop grid.
	int upcoming = t->onset_read;
	while (upcoming != t->onset_write && t->onsets[upcoming] <= start + half) upcoming = (upcoming + 1) % TEMPO_MAX_ONSETS;
	if (upcoming != t->onset_write) {
		int64_t onset_start = t->onsets[upcoming] - half;
		double to_onset = ((double) onset_start - t->ideal) / t->rate;
		if (to_onset < hop) {
			hop = to_onset < 1 ? 1 : (int) lround(to_onset);
		}
	}
	double next_ideal = t->ideal + hop * (double) t->rate;
	t->region_start = output_start;
	t->ready_end = output_start + hop;
	t->heard_base = output_start > 0 ? start + half * (1.0 - t->rate) : 0;
	int64_t mask_at = start + half < t->written ? start + half : t->written - 1;
	t->region_mask = t->mask[mask_at & TEMPO_WRAP];
	t->synthesis_hop = hop;
	t->previous_analysis = start;
	t->ideal = next_ideal;
	int64_t next = llround(next_ideal);
	if (t->rate < 1.0f && next < start + hop) {
		if (t->last_split > start && start + hop - next_ideal <= half) {
			// Play through an attack unstretched so it isn't repeated, then catch up.
			next = start + hop;
		} else if (start > next) {
			next = start + (int64_t) (hop * t->rate * 0.5f) + 1;
			if (next < llround(next_ideal)) next = llround(next_ideal);
		}
	}
	t->analysis = next;
}

static double tempo_heard(const tempo_stretcher *t) {
	return t->heard_base + (double) (t->emit - t->region_start) * (t->region_start == 0 ? 1.0 : t->rate);
}

// Reads the next frame without consuming it. False means more input is needed,
// or after tempo_finish(), that everything has been played.
static bool tempo_peek(tempo_stretcher *t, float *frame, uint16_t *mask) {
	if (t->drained) return false;
	if (t->emit >= t->ready_end) {
		if (!t->finishing && t->written < t->analysis + t->size) return false;
		tempo_process_frame(t);
	}
	if (t->finishing && tempo_heard(t) >= t->written) {
		t->drained = true;
		return false;
	}
	int at = (int) (t->emit & TEMPO_OUT_WRAP);
	float norm = t->norm[at];
	float gain = norm > 1e-6f ? 1.0f / norm : 0;
	for (int c = 0; c < PCM_SPEAKERS; c++) frame[c] = t->output[c][at] * gain;
	*mask = t->region_mask;
	return true;
}

static void tempo_advance(tempo_stretcher *t) {
	int at = (int) (t->emit & TEMPO_OUT_WRAP);
	for (int c = 0; c < PCM_SPEAKERS; c++) t->output[c][at] = 0;
	t->norm[at] = 0;
	t->emit++;
}

// Source frames accepted but not heard yet.
static int tempo_lookahead(const tempo_stretcher *t) {
	if (!t->started) return (int) t->written;
	int64_t ahead = t->written - (int64_t) tempo_heard(t);
	return ahead > 0 ? (int) ahead : 0;
}

static void tempo_free(tempo_stretcher *t) {
	for (int i = 0; i < TEMPO_FFT_SIZES; i++) {
		kiss_fftr_free(t->forward[i]);
		kiss_fftr_free(t->inverse[i]);
		t->forward[i] = NULL;
		t->inverse[i] = NULL;
	}
}

static bool tempo_pending(const tempo_stretcher *t) {
	return t->written > 0 && !t->drained;
}

#endif
