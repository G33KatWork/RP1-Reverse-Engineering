// SPDX-License-Identifier: LGPL-3.0-or-later

#include <stdio.h>
#include <stdint.h>

int main() {
	FILE *in = stdin;
	FILE *out = stdout;

	int c;
	uint8_t out_i = 0;
	char outbuf[256];
	while(1) {
		c = fgetc_unlocked(in);
		if(c < 0) goto end;
		uint8_t cmd = c;
		for(size_t i = 0; i < 8; i++) {
			if(cmd & 1) {
				c = fgetc_unlocked(in);
				if(c < 0) goto fail;
				uint8_t offset = c;
				offset += 1;
				c = fgetc_unlocked(in);
				if(c < 0) goto fail;
				uint8_t len = c;
				do {
					c = outbuf[(uint8_t)(out_i - offset)];
					outbuf[out_i++] = c;
					c = fputc_unlocked(c, out);
					if(c < 0) goto writefail;
				} while(len--);
			} else {
				c = fgetc_unlocked(in);
				if(c < 0) goto end;
				outbuf[out_i++] = c;
				c = fputc_unlocked(c, out);
				if(c < 0) goto writefail;
			}
			cmd >>= 1;
		}
	}

end:
	if(feof_unlocked(in)) return 0;
fail:
	fprintf(stderr, ferror_unlocked(in) ? "Read Error: %m\n" : "Unexpected EOF\n");
	return 1;
writefail:
	fprintf(stderr, "Write Error: %m\n");
	return 1;
}
