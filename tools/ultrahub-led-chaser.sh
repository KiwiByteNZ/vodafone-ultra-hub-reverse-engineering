#!/bin/ash

LED_ROOT=/sys/class/leds
DELAY=${1:-0.10}
PIDFILE=/var/run/led-chaser.pid

LEDS="
power:red
power:orange
power:green
internet:red
internet:orange
internet:green
wireless:red
wireless:orange
wireless:green
voip:red
voip:orange
voip:green
mobile:red
mobile:orange
mobile:green
mobile:cyan
mobile:blue
mobile:magenta
mobile:white
"

all_off() {
    for led in $LEDS; do
        [ -e "$LED_ROOT/$led/brightness" ] && echo 0 > "$LED_ROOT/$led/brightness"
    done
}

restore() {
    trap - INT TERM EXIT
    all_off
    rm -f "$PIDFILE"
    /etc/init.d/ledfw restart >/dev/null 2>&1
    /etc/init.d/led restart >/dev/null 2>&1
    exit 0
}

trap restore INT TERM EXIT

if [ -s "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "LED chaser is already running as PID $(cat "$PIDFILE")" >&2
    exit 1
fi

echo $$ > "$PIDFILE"
/etc/init.d/led stop >/dev/null 2>&1
/etc/init.d/ledfw stop >/dev/null 2>&1
killall status-led-eventing.lua led-fw-interface.lua 2>/dev/null
all_off

while :; do
    for led in $LEDS; do
        all_off
        [ -e "$LED_ROOT/$led/brightness" ] && echo 255 > "$LED_ROOT/$led/brightness"
        sleep "$DELAY"
    done
    REVERSE=""
    for led in $LEDS; do REVERSE="$led $REVERSE"; done
    for led in $REVERSE; do
        all_off
        [ -e "$LED_ROOT/$led/brightness" ] && echo 255 > "$LED_ROOT/$led/brightness"
        sleep "$DELAY"
    done
done
