package main

import (
	"io/fs"
	"net/http/httptest"
	"strings"
	"testing"
	"testing/fstest"
)

func TestLocalServingBoundary(t *testing.T) {
	site := fstest.MapFS{"index.html": {Data: []byte("SimpleOpenCV")}, "vendor/engine.js": {Data: []byte("engine")}}
	h := handler(fs.FS(site), "127.0.0.1:8767", "secret", func() {})
	for _, tc := range []struct {
		path, host, method, origin, token string
		want                              int
	}{
		{"/", "127.0.0.1:8767", "GET", "", "", 200},
		{"/", "attacker.example:8767", "GET", "", "", 403},
		{"/vendor/", "127.0.0.1:8767", "GET", "", "", 404},
		{"/../LICENSE", "127.0.0.1:8767", "GET", "", "", 404},
		{"/__simpleopencv/quit", "127.0.0.1:8767", "GET", "", "", 405},
		{"/__simpleopencv/quit", "127.0.0.1:8767", "POST", "https://example.com", "secret", 403},
		{"/__simpleopencv/quit", "127.0.0.1:8767", "POST", "http://127.0.0.1:8767", "wrong", 403},
		{"/__simpleopencv/quit", "127.0.0.1:8767", "POST", "http://127.0.0.1:8767", "secret", 204},
	} {
		r := httptest.NewRequest(tc.method, "http://"+tc.host+tc.path, strings.NewReader(""))
		r.Host = tc.host
		r.Header.Set("Origin", tc.origin)
		r.Header.Set("X-SimpleOpenCV-Token", tc.token)
		w := httptest.NewRecorder()
		h.ServeHTTP(w, r)
		if w.Code != tc.want {
			t.Errorf("%s %s: got %d want %d", tc.method, tc.path, w.Code, tc.want)
		}
	}
}
