SKIPMOUNT=false
PROPFILE=false
POSTFSDATA=false
LATESTARTSERVICE=false

print_line() {
  ui_print "  $1"
}

wait_volume_key() {
  local getevent_bin
  local event_line
  local empty_reads

  getevent_bin="$(command -v getevent 2>/dev/null)"
  if [ -z "$getevent_bin" ] && [ -x /system/bin/getevent ]; then
    getevent_bin="/system/bin/getevent"
  fi
  if [ -z "$getevent_bin" ]; then
    return 2
  fi

  print_line "Waiting for volume key..."
  empty_reads=0
  while true; do
    event_line="$("$getevent_bin" -lqc 1 2>&1)"
    case "$event_line" in
      *KEY_VOLUMEUP*DOWN*) return 0 ;;
      *KEY_VOLUMEDOWN*DOWN*) return 1 ;;
      *" 0073 "*" 00000001"*) return 0 ;;
      *" 0072 "*" 00000001"*) return 1 ;;
    esac

    if [ -z "$event_line" ] || echo "$event_line" | grep -qi "permission denied\|not found\|invalid option"; then
      empty_reads=$((empty_reads + 1))
      if [ "$empty_reads" -ge 3 ]; then
        return 2
      fi
      sleep 1
    fi
  done
}

choose_yes_no() {
  local prompt="$1"
  local default="$2"
  print_line "$prompt"
  print_line "Vol+ = yes, Vol- = no"
  if type chooseport >/dev/null 2>&1; then
    if chooseport; then
      return 0
    fi
    return 1
  fi
  wait_volume_key
  case "$?" in
    0) return 0 ;;
    1) return 1 ;;
  esac
  print_line "Volume-key selector unavailable, using default: $default"
  [ "$default" = "yes" ]
}

ui_print ""
ui_print "Balatro Portrait Zygisk options"
ui_print ""

if choose_yes_no "Apply Readabletro font/textures?" "yes"; then
  readabletro="on"
else
  readabletro="off"
fi

# Variant names read literally: crt-on = CRT shader stays on (vanilla look).
if choose_yes_no "Disable CRT in portrait mode?" "no"; then
  crt="off"
else
  crt="on"
fi

variant="readabletro-${readabletro}_crt-${crt}"
variant_so="$MODPATH/zygisk/variants/${variant}.so"
target_so="$MODPATH/zygisk/arm64-v8a.so"

if [ ! -f "$variant_so" ]; then
  abort "Missing Zygisk variant: $variant"
fi

cp -f "$variant_so" "$target_so" || abort "Could not select Zygisk variant"
rm -rf "$MODPATH/zygisk/variants"

ui_print ""
ui_print "Selected: Readabletro=$readabletro, CRT shader=$crt"
ui_print "Reboot, then launch the official Play Store Balatro."
