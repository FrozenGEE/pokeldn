/* What the screen shows: the radio's own state, or a trade or a gift the host describes with
   DISPLAY (0x0E). Host-compilable like screen.c. docs/hardware_esp32.md, The screen. */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

enum scene_mode { SCENE_IDLE, SCENE_JOINING, SCENE_JOINED, SCENE_HOSTING, SCENE_SNIFFING };

typedef struct {
    uint8_t mode;          /* enum scene_mode */
    uint8_t stations;      /* consoles seated while hosting */
    uint32_t rx, tx;       /* data frames received and sent since boot */
    uint32_t presses;      /* BOOT presses since boot: each wakes the screen */
} scene_radio_t;

/* The panel's brightness, which scene_draw returns: full while anything happens, dimmed after a
   minute of an idle radio, off after ten. */
enum scene_power { SCENE_ON, SCENE_DIM, SCENE_OFF };

/* DISPLAY ops. SHOW: u8 show, u16 hold s (0: until the next show; traded: the wait before theirs
   comes in), title, NUL, line, NUL. ARRIVED cuts a traded show's wait short.
   SPRITE: u8 slot, u8 width <= 64, u8 height <= 64, rows of (width + 7) / 8 bytes, MSB first.
   LOBBY: u8 stars (0: none), u8 joined, u8 seats (1..3), title, NUL, name, NUL, code, NUL; slot 0 is
   its Pokemon. JOINED: u8 joined, at most the lobby's seats. */
enum { DISPLAY_OP_SHOW, DISPLAY_OP_SPRITE, DISPLAY_OP_LOBBY, DISPLAY_OP_JOINED };
/* SHOW selects the shows before SHOWS; LOBBY starts its own. */
enum { SHOW_AUTO, SHOW_TRADE, SHOW_TRADED, SHOW_GIFT, SHOW_GIFTED, SHOW_ARRIVED, SHOWS, SHOW_LOBBY };
enum { SLOT_OURS, SLOT_THEIRS, SLOT_GIFT, SLOTS };
#define SPRITE_W 64
#define SPRITE_H 64

/* What the panel shows of the 128x64 frame: all of it, or the 72x40 window at column 30, row 24 the
   0.42-inch module shows, where the scenes take a compact layout. */
enum scene_panel { PANEL_128X64, PANEL_72X40 };
#define SMALL_X 30
#define SMALL_Y 24
#define SMALL_W 72
#define SMALL_H 40

/* The speaker cue a frame starts: the traded show's ball-in, transfer jingle, link beeps, the
   received ball opening, and the received Pokemon. */
enum scene_audio {
    SCENE_AUDIO_NONE,
    SCENE_AUDIO_TRADE,      /* transfer jingle, 600 ms after the ball-in */
    SCENE_AUDIO_RECEIVED,   /* received Pokemon, REVEAL_MS after the reveal */
    SCENE_AUDIO_BALL_IN,    /* the traded Pokemon goes into its ball */
    SCENE_AUDIO_LINK,       /* data beeps during the exchange */
    SCENE_AUDIO_BALL_OUT,   /* the received ball opens */
};

void scene_panel(uint8_t panel);
/* False for a malformed command. */
bool scene_command(const uint8_t *payload, size_t length, uint32_t now_ms);
/* One cue per event: ball-in at the start, the transfer jingle, link beeps during the exchange,
   the ball opening at reveal + 1000 ms, and the received Pokemon at reveal + REVEAL_MS.
   Called every frame like scene_draw; 0 when this frame starts nothing. */
uint8_t scene_audio_cue(uint32_t now_ms);
/* Back to the radio's own scenes and no sprites: a new host session. */
void scene_reset(void);
uint8_t scene_draw(uint8_t *fb, const scene_radio_t *radio, uint32_t now_ms);
/* The show the scene is drawing: enum scene_show (SHOW_AUTO when none). */
uint8_t scene_show(void);
/* True during the traded show's exchange phase ("trading..."). */
bool scene_traded_exchanging(uint32_t now_ms);
/* True during the traded ball-flash phase; progress is 0..1000. */
bool scene_traded_opening(uint32_t now_ms, uint32_t *progress);
