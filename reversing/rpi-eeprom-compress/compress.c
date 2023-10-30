// SPDX-License-Identifier: LGPL-3.0-or-later

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <errno.h>
#include <string.h>

static ssize_t read_data(FILE *in, uint8_t **pdata) {
	size_t alloc = 4096;
	uint8_t *data = malloc(alloc);
	if(!data) return -1;

	size_t len = 0;
	while(1) {
		size_t n = fread_unlocked(data + len, 1, alloc - len, in);
		if(n == 0) break;
		len += n;
		size_t want_min = len + (len >> 2);
		if(alloc < want_min) {
			size_t a2 = len + (len >> 1);
			uint8_t *r = realloc(data, a2);
			if(!r) goto fail;
			data = r;
			alloc = a2;
		}
	}
	if(ferror_unlocked(in)) goto fail;

	uint8_t *r = realloc(data, len);
	if(len && !r) goto fail;
	data = r;

	*pdata = data;
	return len;

fail:;
	int e = errno;
	free(data);
	errno = e;
	return -1;
}

struct backref {
	size_t cost;
	uint8_t mlen, moff;
};

struct node {
	size_t off, len;
	struct node *next[256];
};

static void free_nodes(struct node **p) {
	for(size_t i = 0; i < 256; i++) {
		struct node *n = p[i];
		if(!n) continue;
		free_nodes(n->next);
		free(n);
	}
}

inline static void init_nodes(struct node **p) {
	memset(p, 0, 256 * sizeof(*p));
}

static struct backref *compress_data(const uint8_t *data, size_t len) {
	struct node *root[256];
	init_nodes(root);

	if(len >= (size_t)-1 / sizeof(struct backref) - 1) {
		errno = ENOMEM;
		return NULL;
	}
	struct backref *best = malloc((len + 1) * sizeof(struct backref));
	if(!best) {
		return NULL;
	}

	best[0] = (struct backref){
		.cost = 0,
	};

	for(size_t suff_len = 1; suff_len <= len; suff_len++) {
		size_t min_cost = best[suff_len - 1].cost + 9;
		uint8_t min_mlen = 0;
		uint8_t min_moff = 0;

		size_t at = suff_len;
		size_t bound = at < 256 ? 0 : at - 256;
		struct node **p = root;
		while(at > bound) {
			size_t left = at - bound;

			p += data[at - 1];
			struct node *n = *p;
			size_t mlen;
			if(!n) {
				n = calloc(1, sizeof(struct node));
				if(!n) goto fail;
				mlen = left;
				*p = n;
			} else {
				assert(n->len > 0);
				assert(n->off < at);
				size_t moff = at - n->off;
				if(moff > 256) {
					free_nodes(n->next);
					init_nodes(n->next);
					mlen = left;
				} else {
					const uint8_t *cmp1 = data + at;
					const uint8_t *cmp2 = data + n->off;
					if(n->len < left) left = n->len;
					mlen = 0;
					while(mlen < left) {
						if(*--cmp1 != *--cmp2) break;
						mlen++;
					}
					assert(mlen > 0);

					for(size_t i = mlen; i > 0; i--) {
						size_t base = at - i;
						size_t cost = best[base].cost + 17;
						assert(suff_len - base <= 256);
						if(cost < min_cost) {
							assert(suff_len - base > 1);
							min_cost = cost;
							min_mlen = suff_len - base - 1;
							min_moff = moff - 1;
						}
					}

					if(mlen != n->len) {
						n->len -= mlen;
						n->off -= mlen;
						struct node *n2 = calloc(1, sizeof(struct node));
						if(!n2) goto fail;
						n2->next[*cmp2] = n;
						n = n2;
						*p = n;
					}
				}
			}
			n->off = at;
			n->len = mlen;
			p = n->next;
			at -= mlen;
		}

		best[suff_len] = (struct backref){
			.cost = min_cost,
			.mlen = min_mlen,
			.moff = min_moff,
		};
	}

	free_nodes(root);
	return best;

fail:;
	int e = errno;
	free_nodes(root);
	errno = e;
	return NULL;
}

static int reconstruct(FILE *out, const uint8_t *data, size_t len, struct backref *back) {
	size_t cost = back[len].cost;
	size_t bytes = (cost + 7) / 8;
	uint8_t *buf = malloc(bytes);
	if(!buf) return -1;

	uint8_t *at = buf + bytes;
	uint8_t cmd = 0;
	while(len) {
		assert(cost == back[len].cost);
		cmd <<= 1;
		if(back[len].mlen == 0) {
			cost -= 9;
			*--at = data[--len];
		} else {
			cmd |= 1;
			cost -= 17;
			*--at = back[len].mlen;
			*--at = back[len].moff;
			len -= (size_t)back[len].mlen + 1;
		}
		if(cost % 8 == 0) {
			*--at = cmd;
			cmd = 0;
		}
	}
	assert(cost == 0);
	assert(at == buf);

	at = buf;
	while(bytes) {
		size_t n = fwrite_unlocked(at, 1, bytes, out);
		if(n == 0) {
			int e = errno;
			free(buf);
			errno = e;
			return -1;
		}
		at += n;
		bytes -= n;
	}
	free(buf);
	return 0;
}

int main() {
	uint8_t *data;
	ssize_t n = read_data(stdin, &data);
	if(n < 0) {
		fprintf(stderr, "Read Error: %m\n");
		return 1;
	}

	struct backref *best = compress_data(data, n);

	int r = reconstruct(stdout, data, n, best);
	if(r < 0) {
		fprintf(stderr, "Write Error: %m\n");
		return 1;
	}
	free(best);
	free(data);
	return 0;
}
