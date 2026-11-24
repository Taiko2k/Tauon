// Bauer stereophonic-to-binaural (bs2b) headphone crossfeed filter.
// Two first-order IIR filters per channel (low-pass crossfeed + high-shelf
// direct path) with gain normalization and a short dry/wet ramp on toggle.
#ifndef PHAZOR_BS2B_H
#define PHAZOR_BS2B_H

#include <math.h>
#include <stdbool.h>

#define BS2B_MIN_SRATE 1920
#define BS2B_MAX_SRATE 384000
#define BS2B_DEFAULT_SRATE 44100

#define BS2B_MIN_FCUT 300
#define BS2B_MAX_FCUT 2000
#define BS2B_DEFAULT_FCUT 700

#define BS2B_MIN_FEED_DB 1.0f
#define BS2B_MAX_FEED_DB 15.0f
#define BS2B_DEFAULT_FEED_DB 4.5f

#define BS2B_RAMP_MS 20.0f
#define BS2B_PI 3.14159265358979323846

typedef struct {
	int enabled;
	int fcut;
	float feed_db;
	int sample_rate;
	bool dirty;
	double a0_lo;
	double b1_lo;
	double a0_hi;
	double a1_hi;
	double b1_hi;
	double gain;
	double lo[2];
	double hi[2];
	double prev[2];
	float mix;
	float ramp_step;
} bs2b_state;

static inline void bs2b_state_reset(bs2b_state *s) {
	s->lo[0] = 0.0;
	s->lo[1] = 0.0;
	s->hi[0] = 0.0;
	s->hi[1] = 0.0;
	s->prev[0] = 0.0;
	s->prev[1] = 0.0;
}

static inline int bs2b_clamp_fcut(int fcut) {
	if (fcut < BS2B_MIN_FCUT) return BS2B_MIN_FCUT;
	if (fcut > BS2B_MAX_FCUT) return BS2B_MAX_FCUT;
	return fcut;
}

static inline float bs2b_clamp_feed_db(float feed_db) {
	if (!isfinite(feed_db)) return BS2B_DEFAULT_FEED_DB;
	if (feed_db < BS2B_MIN_FEED_DB) return BS2B_MIN_FEED_DB;
	if (feed_db > BS2B_MAX_FEED_DB) return BS2B_MAX_FEED_DB;
	return feed_db;
}

static inline void bs2b_state_init(bs2b_state *s) {
	s->enabled = 0;
	s->fcut = BS2B_DEFAULT_FCUT;
	s->feed_db = BS2B_DEFAULT_FEED_DB;
	s->sample_rate = 0;
	s->dirty = true;
	s->a0_lo = 0.0;
	s->b1_lo = 0.0;
	s->a0_hi = 1.0;
	s->a1_hi = 0.0;
	s->b1_hi = 0.0;
	s->gain = 1.0;
	s->mix = 0.0f;
	s->ramp_step = 1.0f;
	bs2b_state_reset(s);
}

static inline void bs2b_state_update_coefficients(bs2b_state *s, int sample_rate, bool reset_state) {
	if (sample_rate < BS2B_MIN_SRATE || sample_rate > BS2B_MAX_SRATE) {
		sample_rate = BS2B_DEFAULT_SRATE;
	}

	double fc_lo = (double) bs2b_clamp_fcut(s->fcut);
	double level = (double) bs2b_clamp_feed_db(s->feed_db);

	double gb_lo = level * -5.0 / 6.0 - 3.0;
	double gb_hi = level / 6.0 - 3.0;

	double g_lo = pow(10.0, gb_lo / 20.0);
	double g_hi = 1.0 - pow(10.0, gb_hi / 20.0);
	double fc_hi = fc_lo * pow(2.0, (gb_lo - 20.0 * log10(g_hi)) / 12.0);

	double x_lo = exp(-2.0 * BS2B_PI * fc_lo / (double) sample_rate);
	s->b1_lo = x_lo;
	s->a0_lo = g_lo * (1.0 - x_lo);

	double x_hi = exp(-2.0 * BS2B_PI * fc_hi / (double) sample_rate);
	s->b1_hi = x_hi;
	s->a0_hi = 1.0 - g_hi * (1.0 - x_hi);
	s->a1_hi = -x_hi;

	s->gain = 1.0 / (1.0 - g_hi + g_lo);

	float ramp_samples = ((float) sample_rate * BS2B_RAMP_MS) / 1000.0f;
	s->ramp_step = ramp_samples > 1.0f ? (1.0f / ramp_samples) : 1.0f;

	s->sample_rate = sample_rate;
	s->dirty = false;
	if (reset_state) {
		bs2b_state_reset(s);
	}
}

static inline void bs2b_state_set_enable(bs2b_state *s, int enabled) {
	int next = enabled != 0;
	if (next && !s->enabled && s->mix <= 0.0f) {
		bs2b_state_reset(s);
	}
	s->enabled = next;
	if (next) {
		s->dirty = true;
	}
}

static inline void bs2b_state_set_params(bs2b_state *s, int fcut, float feed_db) {
	s->fcut = bs2b_clamp_fcut(fcut);
	s->feed_db = bs2b_clamp_feed_db(feed_db);
	s->dirty = true;
}

static inline bool bs2b_is_active(const bs2b_state *s) {
	return s->enabled != 0 || s->mix > 0.0f;
}

static inline void bs2b_process_frame(bs2b_state *s, float *out, int channels, int sample_rate) {
	if (channels != 2 || !bs2b_is_active(s)) return;
	if (sample_rate <= 0) return;

	if (s->dirty || s->sample_rate != sample_rate) {
		bool rate_changed = s->sample_rate != sample_rate;
		bs2b_state_update_coefficients(s, sample_rate, rate_changed);
	}

	double in_l = (double) out[0];
	double in_r = (double) out[1];

	s->lo[0] = s->a0_lo * in_l + s->b1_lo * s->lo[0];
	s->lo[1] = s->a0_lo * in_r + s->b1_lo * s->lo[1];

	s->hi[0] = s->a0_hi * in_l + s->a1_hi * s->prev[0] + s->b1_hi * s->hi[0];
	s->hi[1] = s->a0_hi * in_r + s->a1_hi * s->prev[1] + s->b1_hi * s->hi[1];
	s->prev[0] = in_l;
	s->prev[1] = in_r;

	float wet_l = (float) ((s->hi[0] + s->lo[1]) * s->gain);
	float wet_r = (float) ((s->hi[1] + s->lo[0]) * s->gain);

	if (s->enabled) {
		if (s->mix < 1.0f) {
			s->mix += s->ramp_step;
			if (s->mix > 1.0f) s->mix = 1.0f;
		}
	} else if (s->mix > 0.0f) {
		s->mix -= s->ramp_step;
		if (s->mix <= 0.0f) {
			s->mix = 0.0f;
			bs2b_state_reset(s);
		}
	}

	float mix = s->mix;
	if (mix >= 1.0f) {
		out[0] = wet_l;
		out[1] = wet_r;
	} else if (mix > 0.0f) {
		float dry = 1.0f - mix;
		out[0] = out[0] * dry + wet_l * mix;
		out[1] = out[1] * dry + wet_r * mix;
	}
}

#endif
