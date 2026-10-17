#!/bin/bash
cd /Users/jessi/karatehp;

lsof -ti:1313 | xargs kill -9

hugo server --bind=192.168.0.40 --baseURL=http://192.168.0.40  --disableFastRender --noHTTPCache

[ $? -eq 0 ] && echo "server hugo emy neu gestartet" || echo "fehler beim starten von emy server"
